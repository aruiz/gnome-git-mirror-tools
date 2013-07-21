#!/usr/bin/python
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
"""
Copyright (c) 2012 Alberto Ruiz <aruiz@gnome.org>
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

import json
import requests
import os
import sys
import os.path
import base64
import getopt, sys
import subprocess
import shlex
import scrapper
import configparser

ORGANIZATION="GNOME"
SKIP=['gtk-vnc',]
#SCRAPER_QUERY="https://api.scraperwiki.com/api/1.0/datastore/sqlite?format=jsondict&name=gnome_git_projects&query=select%20*%20from%20%60swdata%60"

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

    def normalize_name (self, name):
        if name == 'gtk+':
            return 'gtk'
        if name == 'libxml++':
            return 'libxmlmm'
        if name == 'libsigc++2':
            return 'libsigcpp2'
        return name

    def create_github_repo (self, name, description, homepage):
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
        if rq.status_code != 200:
            raise Exception ("Request to create %s failed with code %d:\n%s" % (name,rq.status_code,rq.text))
        
    def check_if_repo_exists (self):
        pass

class Gnome:
    def __init__(self):
        pass

    def list_repositories (self):
        return scrapper.doap_to_python ()

    def mirror_repo (self, repo, download_only=False):
        r = Repo (repo)
        r.checkout_repo ()
        if not download_only:
            r.push_all_branches ()
    def get_index_for_name (self, all_repos, starting_from):
            index = 0
            for repo in all_repos:
                if repo['name'] == starting_from:
                    break
                index += 1

            if index >= len(all_repos):
                return 0

            return index

    def mirror_all_repos (self, starting_from=None, download_only=False):
        all_repos = self.list_repositories()

        if starting_from:
            starts_at = self.get_index_for_name (all_repos, starting_from)
        else:
            starts_at = 0

        for repo in all_repos[starts_at:]:
            if repo['name'] in SKIP:
                continue
            self.mirror_repo (repo, download_only)

def gitcall (call):
    return subprocess.call(shlex.split(call))

class Repo:
    def __init__(self, repo):
        self.url = repo['repository']
        self.name = repo['name']
        self.description = repo['description']
        self.homepage = repo['homepage']
        self.dir = self.name + '.git'

    def pull_all_branches (self):
        print ("Pulling updates from %s" % self.url)
        cwd = os.getcwd()
        os.chdir(self.dir)
        try:    
            gitcall('git remote update')
            gitcall('git fetch origin')
        except OSError:
            raise Exception("There was an error pulling from origin in %s" % (self.url))
        finally:
            os.chdir(cwd)

    def push_all_branches (self):
        #FIXME: Make it pull all actuall branches
        print ("Pushing updates from %s to github" % self.url)
        gh = GitHub()
        gh.create_github_repo (self.name, self.description, self.homepage)

        self.config_origin ()

        cwd = os.getcwd()
        os.chdir(self.dir)
        try:
            gitcall('git push --mirror')
        except OSError:
            raise Exception("There was an error pushing to github from %s" % (self.url))
        finally:
            os.chdir(cwd)

    def config_origin (self):
        cwd = os.getcwd()
        os.chdir(self.dir)

        githubname = GitHub().normalize_name (self.name)

        try:
            gitcall('git config remote.origin.pushurl git@github.com:%s/%s.git' % (ORGANIZATION, githubname))
        except OSError:
            raise Exception("There was an error configuring the git repo %s" % self.name)
        finally:
            os.chdir(cwd)

    def clone_repo (self):
        print("Cloning " + self.url)
        try:
            gitcall('git clone --mirror '+self.url)
        except OSError:
            raise Exception("There was an error cloning %s" % (self.url))

        self.config_origin ()

    def checkout_repo (self):
        if os.path.exists(self.dir):
            self.pull_all_branches ()
            return

        self.clone_repo ()

if __name__ == '__main__':
    starting_at = None
    download_only = False
    optlist, args = getopt.getopt (sys.argv[1:], "", ['start-at=', 'download-only'])
    for opt in optlist:
        if opt[0] == '--start-at':
            starting_at = opt[1]
        if opt[0] == '--download-only':
            download_only = True

    g = Gnome()
    g.mirror_all_repos (starting_at, download_only)
