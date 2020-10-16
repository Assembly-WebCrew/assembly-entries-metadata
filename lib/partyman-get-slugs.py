#!/usr/bin/env python3

import argparse
import asmmetadata
import http.cookiejar
import json
import os
import re
import requests
import requests.utils
import sys
import urllib.request

def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('cookie_jar')
    args = parser.parse_args(argv[1:])

    cookie_jar = http.cookiejar.MozillaCookieJar(args.cookie_jar)
    cookie_jar.load()
    result = requests.get(
        url="https://scene.assembly.org/api/v1/playlist/?format=json",
        cookies = cookie_jar)
    partyman_playlists = result.json()
    for playlist in partyman_playlists:
        slug = playlist["competition"]["slug"]
        print(slug)
    return os.EX_OK

if __name__ == "__main__":
    sys.exit(main(sys.argv))
