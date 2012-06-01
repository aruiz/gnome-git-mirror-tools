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
import urllib2
import commands
import os
import os.path

ORGANIZATION="GNOME-Project"
SCRAPER_QUERY="https://api.scraperwiki.com/api/1.0/datastore/sqlite?format=jsondict&name=gnome_git_projects&query=select%20*%20from%20%60swdata%60"

def create_github_reop ():


def list_repositories ():
    return json.loads(urllib2.urlopen (SCRAPER_QUERY).read())

def pull_all_branches (url):
    cwd = os.getcwd()
    os.chdir(url.split('/')[-1])
    status, output = commands.getstatusoutput('git pull --all')
    os.chdir(cwd)

    if status != 0:
        raise Exception("There was an error pulling from origin in %s: %s" % (url, output))

def push_all_branches (url):
    cwd = os.getcwd()
    os.chdir(url.split('/')[-1])
    status, output = commands.getstatusoutput('git push --all github')
    os.chdir(cwd)

    if status != 0:
        raise Exception("There was an error pushing to github from %s: %s" % (url, output))

def clone_repo (url):
    print("Cloning " + url)
    status, output = commands.getstatusoutput('git clone '+url)

    if status != 0:
        raise Exception("There was an error cloning %s: %s" % (url, output))

    cwd = os.getcwd()
    os.chdir(url.split('/')[-1])
    commands.getstatusoutput('git config remote.origin.pushurl git@github.com:%s/%s.git' % (ORGANIZATION, url.split('/')[-1]))
    os.chdir(cwd)

def checkout_repo (repo):
    if os.path.exists(repo['repository'].split('/')[-1]):
        pull_all_branches (repo['repository'])
        return

    clone_repo (repo['repository'])

def checkout_all_repos ():
    #NOTE: Getting just one repo for testing purposes
    checkout_repo (list_repositories()[0])

checkout_all_repos ()
