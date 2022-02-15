#!/usr/bin/python3
# -*- coding: utf8 -*-

_api_root = '/service/rest/v1'
_nexus_old = 'https://nexus0.corp'
_nexus_new = 'https://nexus1.corp'
_api_old = _nexus_old + _api_root + '/components'
_api_new = _nexus_new + _api_root + '/components'
_auth = ('user', 'password')

import requests
import re

_assets_exclusion = re.compile(r'\.(md5|sha\d+)$')

def list_components(repo):
    payload = {
        'repository': repo,
    }

    while True:
        r = requests.get(_api_old, params = payload).json()
        for c in r['items']:
            yield c
        if 'continuationToken' in r:
            payload['continuationToken'] = r['continuationToken']
        
        if not payload['continuationToken']:
            return

def migrate_maven_component(src, dst_repo):
    data = {
        "maven2.groupId": src["group"],
        "maven2.artifactId": src["name"],
        "maven2.version": src["version"],
        "maven2.generate-pom": "false",
    }

    n = 1
    files = {}
    for a in src["assets"]:
        extension = a["maven2"]["extension"]
        if _assets_exclusion.search(extension):
            continue
        # download asset
        r = requests.get(a["downloadUrl"])
        fn = "temp/" + a["checksum"]["sha1"]
        with open(fn, "wb") as fd:
            fd.write(r.content)

        data["maven2.asset%d.extension" % n] = extension
        if "classifier" in a["maven2"]:
            data["maven2.asset%d.classifier" % n] = a["maven2"]["classifier"]
        files["maven2.asset%d" % n] = open(fn, 'rb')
        
        n += 1

    requests.post(_api_new, params = {"repository": dst_repo}, data = data, files = files, auth = _auth)

def migrate_nuget_component(src, dst_repo):
    a = src["assets"][0]
    r = requests.get(a["downloadUrl"])
    fn = "temp/" + a["checksum"]["sha1"]
    with open(fn, "wb") as fd:
        fd.write(r.content)
    files = {
        "nuget.asset": open(fn, 'rb'),
    }
    requests.post(_api_new, params = {"repository": dst_repo}, files = files, auth = _auth)
    

if __name__ == '__main__':
    components = list_components('nuget-hosted')
    for c in components:
        print("{group}:{name}:{version}".format(**c))
        try:
            migrate_nuget_component(c, 'nuget-hosted')
        except Exception as e:
            print("Exception: ", e)
