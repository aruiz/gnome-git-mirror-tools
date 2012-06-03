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
import urllib
import urllib2
import commands
import os
import os.path
import ConfigParser
import base64
import getopt, sys

ORGANIZATION="GNOME-Project"
SKIP='gtk-vnc'
SCRAPER_QUERY="https://api.scraperwiki.com/api/1.0/datastore/sqlite?format=jsondict&name=gnome_git_projects&query=select%20*%20from%20%60swdata%60"

class GitHub:
    def __init__ (self):
        config = ConfigParser.ConfigParser()
        #TODO: Inform the user what to do one the file is not there
        config.read(os.path.expanduser('~/.gitmirrorrc'))
        self.user = config.get('Github', 'user')
        self.pw   = config.get('Github', 'password')

    def normalize_name (self, name):
        if name == 'gtk+':
            return 'gtk'
        if name == 'libxml++':
            return 'libxmlmm'
        if name == 'libsigc++2':
            return 'libsigcpp2'
        return name

    def create_github_repo (self, name, description):
        data = urllib.urlencode({'name': ORGANIZATION+"/"+self.normalize_name(name), 'description': description})
        request = urllib2.Request('https://github.com/api/v2/json/repos/create', data)
        base64string = base64.encodestring('%s:%s' % (self.user, self.pw)).replace('\n', '')
        request.add_header("Authorization", "Basic %s" % base64string)
        try:
            result = urllib2.urlopen(request)
        except urllib2.HTTPError as e:
            if e.code != 422:
                raise

    def check_if_repo_exists (self):
        pass

class Gnome:
    def __init__(self):
        pass
    def list_repositories (self):
        return json.loads(urllib2.urlopen (SCRAPER_QUERY).read())
    def mirror_repo (self, repo):
        r = Repo (repo)
        r.checkout_repo ()
        r.push_all_branches ()
    def get_index_for_name (self, all_repos, starting_from):
            index = 0
            for repo in all_repos:
                if repo['repository'].split('/')[-1] == starting_from:
                    break
                index += 1

            if index >= len(all_repos):
                return 0

            return index

    def mirror_all_repos (self, starting_from=None):
        all_repos = self.list_repositories()

        if starting_from:
            starts_at = self.get_index_for_name (all_repos, starting_from)
        else:
            starts_at = 0

        for repo in all_repos[starts_at:]:
            if repo['name'] in SKIP:
                continue
            self.mirror_repo (repo)
        
class Repo:
    def __init__(self, repo):
        self.url = repo['repository']
        self.name = self.url.split('/')[-1]
        self.description = repo['name']
        self.dir = self.name + '.git'

    def pull_all_branches (self):
        print ("Pulling updates from %s" % self.url)
        cwd = os.getcwd()
        os.chdir(self.dir)
        status, output = commands.getstatusoutput('git remote update')
        status, output = commands.getstatusoutput('git fetch origin')
        os.chdir(cwd)

        if status != 0:
            raise Exception("There was an error pulling from origin in %s: %s" % (self.url, output))

    def push_all_branches (self):
        #FIXME: Make it pull all actuall branches
        print ("Pushing updates from %s to github" % self.url)
        gh = GitHub()
        gh.create_github_repo (self.name, self.description)

        cwd = os.getcwd()
        os.chdir(self.dir)
        status, output = commands.getstatusoutput('git push --mirror')
        os.chdir(cwd)

        if status != 0:
            raise Exception("There was an error pushing to github from %s: %s" % (self.url, output))

    def clone_repo (self):
        print("Cloning " + self.url)
        status, output = commands.getstatusoutput('git clone --mirror '+self.url)

        if status != 0:
            raise Exception("There was an error cloning %s: %s" % (self.url, output))

        githubname = GitHub().normalize_name (self.name)

        cwd = os.getcwd()
        os.chdir(self.dir)
        commands.getstatusoutput('git config remote.origin.pushurl git@github.com:%s/%s.git' % (ORGANIZATION, githubname))
        os.chdir(cwd)

    def checkout_repo (self):
        if os.path.exists(self.dir):
            self.pull_all_branches ()
            return

        self.clone_repo ()

if __name__ == '__main__':
    starting_at = None
    optlist, args = getopt.getopt (sys.argv[1:], "", ['starting_at='])
    for opt in optlist:
        if opt[0] == "--starting_at":
            starting_at = opt[1]

    g = Gnome()
    g.mirror_all_repos (starting_at)
