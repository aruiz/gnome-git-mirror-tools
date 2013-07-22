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
import configparser
#import smtplib
#import logging

ORGANIZATION="GNOME"
name_maps = {"gtk+":       "gtk",
             "libxml++":   "libxmlmm",
             "libsigc++2": "libsigcpp2"}

class GitHub:
    def __init__ (self):
        config = configparser.ConfigParser()
        #TODO: Inform the user what to do one the file is not there
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
        raise Exception("%s has a '+' character in it which is unsupported bit Github" % name)
    if name in name_maps.keys():
        return name_maps[name]

    return name

def main ():
    gh = GitHub ()
    repo_name = os.getcwd ().split("/")[-2]
    github_name = normalize_name (repo_name)
    if not gh.check_if_repo_exists(repo_name):
        #TODO: Get doap file
        pass
    
    try:
        'git push --mirror git@github.com:%s/%s' % (ORGANIZATION, github_name)
        subprocess.call(shlex.split())
    except OSERror:
        raise

if __name__ == "__main__":
    try:
        main ()
    except:
        #TODO: Send an email to the sysadmins
        pass
