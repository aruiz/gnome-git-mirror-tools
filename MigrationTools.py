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

ORGANIZATION="GNOME-Project"
SCRAPER_QUERY="https://api.scraperwiki.com/api/1.0/datastore/sqlite?format=jsondict&name=gnome_git_projects&query=select%20*%20from%20%60swdata%60"

class GitHub:
    def __init__ (self):
        config = ConfigParser.ConfigParser()
        #TODO: Inform the user what to do one the file is not there
        config.read(os.path.expanduser('~/.gitmirrorrc'))
        self.user = config.get('Github', 'user')
        self.pw   = config.get('Github', 'password')

    def create_github_repo (self, name, description):
        #TODO: Check whether it exists already
        data = urllib.urlencode({'name': ORGANIZATION+"/"+name, 'description': description})
        request = urllib2.Request('https://github.com/api/v2/json/repos/create', data)
        base64string = base64.encodestring('%s:%s' % (self.user, self.pw)).replace('\n', '')
        request.add_header("Authorization", "Basic %s" % base64string)
        result = urllib2.urlopen(request)

    def check_if_repo_exists (self):
        pass

class Gnome:
    def __init__(self):
        pass
    def list_repositories (self):
        return json.loads(urllib2.urlopen (SCRAPER_QUERY).read())
    def checkout_all_repos (self):
        #NOTE: Getting just one repo for testing purposes
        r = Repo(self.list_repositories()[0])
        r.checkout_repo ()
        r.push_all_branches ()

class Repo:
    def __init__(self, repo):
        self.url = repo['repository']
        self.name = self.url.split('/')[-1]
        self.description = repo['name']

    def pull_all_branches (self):
        cwd = os.getcwd()
        os.chdir(self.name)
        status, output = commands.getstatusoutput('git pull --all')
        os.chdir(cwd)

        if status != 0:
            raise Exception("There was an error pulling from origin in %s: %s" % (self.url, output))

    def push_all_branches (self):
        gh = GitHub()
        gh.create_github_repo (self.name, self.description)

        cwd = os.getcwd()
        os.chdir(self.name)
        status, output = commands.getstatusoutput('git push --all')
        os.chdir(cwd)

        if status != 0:
            raise Exception("There was an error pushing to github from %s: %s" % (self.url, output))

        os.chdir(self.name)
        status, output = commands.getstatusoutput('git push --tags')
        os.chdir(cwd)

        if status != 0:
            raise Exception("There was an error pushing to github from %s: %s" % (self.url, output))

    def clone_repo (self):
        print("Cloning " + self.url)
        status, output = commands.getstatusoutput('git clone '+self.url)

        if status != 0:
            raise Exception("There was an error cloning %s: %s" % (self.url, output))

        cwd = os.getcwd()
        os.chdir(self.name)
        commands.getstatusoutput('git config remote.origin.pushurl git@github.com:%s/%s.git' % (ORGANIZATION, self.name))
        os.chdir(cwd)

    def checkout_repo (self):
        if os.path.exists(self.name):
            self.pull_all_branches ()
            return

        self.clone_repo ()

