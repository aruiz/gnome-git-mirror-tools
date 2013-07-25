#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
"""
Copyright (c) 2013 Alberto Ruiz <aruiz@gnome.org>
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

  * Redistributions of source code must retain the above copyright notice,
    this list of conditions and the following disclaimer.
  * Redistributions in binary form must reproduce the above copyright notice,
    this list of conditions and the following disclaimer in the documentation
    and/or other materials provided with the distribution.
  * Neither the name of Pioneers of the Inevitable, Songbird, nor the names
    of its contributors may be used to endorse or promote products derived
    from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
import os
import sys
import requests
import subprocess
import shlex
import configparser
import xml.etree.ElementTree as et
import smtplib
from email.mime.text import MIMEText
import tempfile

ORGANIZATION="GNOME"
name_maps = {"gtk+":       "gtk",
             "libxml++":   "libxmlmm",
             "libsigc++2": "libsigcpp2"}

class GitHub:
    def __init__ (self):
        config = configparser.ConfigParser()
        try:
            config.read(os.path.expanduser('~/.gitmirrorrc'))
            self.user = config.get('Github', 'user')
            self.pw   = config.get('Github', 'password')
        except configparser.NoSectionError:
            raise Exception ("~/.gitmirrorrc non existant or missing [Github] section with user and password keys")
        except configparser.NoOptionError:
            raise Exception ("~/.gitmirrorrc misses user or/and password keys in the [Github] section")

    def check_if_repo_exists (self, name):
        rq = requests.get('https://api.github.com/repos/'+ORGANIZATION+'/'+name,
                          auth=(self.user, self.pw))
        if rq.status_code != 200:
            return False

        return True

    def create_github_repo (self, name, description, homepage):
        if self.check_if_repo_exists (name):
            return
        payload = json.dumps({
                             'name': self.normalize_name(name),
                             'description': description,
                             'homepage': homepage,
                             'has_wiki': False,
                             'has_issues': False
                             })
        rq = requests.post('https://api.github.com/orgs/'+ORGANIZATION,
                           auth=(self.user, self.pw),
                           data=payload)
        if rq.status_code == 200:
            return

def normalize_name (name):
    if "+" in name:
        raise Exception("%s has a '+' character in it which is unsupported bit Github.\nYou have to add it to the exception maps in the post-update hook." % name)
    if name in name_maps.keys():
        return name_maps[name]

    return name

def get_repo_name ():
    repo_name = os.getcwd ().split("/")[-1]
    if repo_name == ".git":
        repo_name = os.getcwd ().split("/")[-2]
    elif repo_name.endswith(".git"):
        repo_name = repo_name[0:-4]
    return repo_name

def get_repo_settings (name):
    nss = {'doap': 'http://usefulinc.com/ns/doap#',
           'rdf':  'http://www.w3.org/1999/02/22-rdf-syntax-ns#'}
    doap_url = "https://git.gnome.org/browse/%s/plain/%s.doap" % (name, name)

    rq = requests.get(doap_url)
    if rq != 200:
        raise Exception ("Could not get doap: %s", doap_url)

    prj = et.fromstring (rq.text)

    resource = '{%s}resource' % nss['rdf']

    repo = prj.find('doap:repository/doap:GitRepository/doap:location', nss)
    name = prj.find ('doap:name', nss)
    desc = prj.find('doap:shortdesc', nss)
    homepage = prj.find('doap:homepage/[@rdf:resource]', nss)
    category = prj.find('doap:category/[@rdf:resource]', nss)

    repo = repo.get(resource)
    name = name.text if name else repo.split('/')[-1]
    descdesc = desc.text if desc else name
    homepage = homepage.get(resource) if homepage else 'http://www.gnome.org/'
    category = category.get(resource) if category else 'gnome'

    return { "category":    category.encode('utf-8').decode('utf-8'),
             "homepage":    homepage.encode('utf-8').decode('utf-8'),
             "name":        name.encode('utf-8').decode('utf-8'),
             "repository":  repo.encode('utf-8').decode('utf-8'),
             "description": desc.encode('utf-8').decode('utf-8')}

def main ():
    gh = GitHub ()
    repo_name = get_repo_name ()
    github_name = normalize_name (repo_name)
    if not gh.check_if_repo_exists(repo_name):
        settings = get_repo_settings (repo_name)
    try:
        command = 'git push --mirror git@github.com:%s/%s' % (ORGANIZATION, github_name)
        out = tempfile.NamedTemporaryFile (prefix="github",suffix="std")
        err = tempfile.NamedTemporaryFile (prefix="github",suffix="err")
        subprocess.check_call(shlex.split(command), stderr=err, stdout=out)
        out.close()
        err.close()
    except subprocess.CalledProcessError:
        out = open(out.name, "r")
        err = open(err.name, "r")
        raise Exception("Error trying to push branch %s\nSTDOUT:\n%s\nSTDERR\n%s" % (repo_name, out.read(), err.read()))

if __name__ == "__main__":
    try:
        main ()
    except Exception as e:
        msg = MIMEText(str(e))
        msg['Subject'] = "[GITHUB HOOK] ERROR trying to push %s" %  os.getcwd ()
        msg['From']    = "gnome-sysadmin@gnome.org"
        msg['To']      = "gnome-sysadmin@gnome.org"
        msg['X-GNOME-SERVICE'] = "github-mirror"
        server = smtplib.SMTP("localhost")
        server.send_message (msg)
        server.quit ()
        raise e
