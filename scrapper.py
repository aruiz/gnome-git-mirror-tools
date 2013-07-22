import requests
import xml.etree.ElementTree as et
import json

def doap_to_python ():
  rq = requests.get('https://git.gnome.org/repositories.doap')
  repos = et.fromstring(rq.text)
  nss = {'doap': 'http://usefulinc.com/ns/doap#',
         'rdf':  'http://www.w3.org/1999/02/22-rdf-syntax-ns#'}

  projects = repos.findall('doap:Project', nss)

  repos_list = []

  for prj in projects:
    resource = '{%s}resource' % nss['rdf']

    repo = prj.find('doap:repository/doap:GitRepository/doap:location', nss)
    name = prj.find ('doap:name', nss)
    desc = prj.find('doap:shortdesc', nss)
    homepage = prj.find('doap:homepage/[@rdf:resource]', nss)
    category = prj.find('doap:category/[@rdf:resource]', nss)

    repo = repo.get(resource)
    name = name.text if name else repo.split('/')[-1]
    desc = desc.text if desc else name
    homepage = homepage.get(resource) if homepage else 'http://www.gnome.org/'
    category = category.get(resource) if category else 'gnome'

    obj = {"category":    category.encode('utf-8').decode('utf-8'),
           "homepage":    homepage.encode('utf-8').decode('utf-8'),
           "name":        name.encode('utf-8').decode('utf-8'),
           "repository":  repo.encode('utf-8').decode('utf-8'),
           "description": desc.encode('utf-8').decode('utf-8')}
    repos_list.append(obj)

  return repos_list

def list_repos ():
  rq = requests.get('https://git.gnome.org/repositories.doap')
  repos = et.fromstring(rq.text)
  nss = {'doap': 'http://usefulinc.com/ns/doap#',
         'rdf':  'http://www.w3.org/1999/02/22-rdf-syntax-ns#'}

  projects = repos.findall('doap:Project', nss)

  repos_list = []

  for prj in projects:
    resource = '{%s}resource' % nss['rdf']

    repo = prj.find('doap:repository/doap:GitRepository/doap:location', nss)
    repo = repo.get(resource)
    print (repo)

if __name__ == '__main__':
  list_repos ()

