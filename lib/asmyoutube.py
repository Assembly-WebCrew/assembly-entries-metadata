#!/usr/bin/env python

import os
import httplib2
import re
import time

from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow


def add_auth_args(parser):
    parser.add_argument("--auth_host_name", default="localhost")
    parser.add_argument("--auth_host_port", default=[8080, 8090])
    parser.add_argument("--noauth_local_webserver", default=True)
    parser.add_argument("--auth_local_webserver", default=False)
    parser.add_argument(
        '--logging_level', default='ERROR',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Set the logging level of detail.')


# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret. You can acquire an OAuth 2.0 client ID and client secret from
# the {{ Google Cloud Console }} at
# {{ https://cloud.google.com/console }}.
# Please ensure that you have enabled the YouTube Data API for your project.
# For more information about using OAuth2 to access the YouTube Data API, see:
#   https://developers.google.com/youtube/v3/guides/authentication
# For more information about the client_secrets.json file format, see:
#   https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
CLIENT_SECRETS_FILE = "client_secrets.json"

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account.
YOUTUBE_READ_WRITE_SCOPE = "https://www.googleapis.com/auth/youtube"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# This variable defines a message to display if the CLIENT_SECRETS_FILE is
# missing.
MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0
To make this sample run you will need to populate the client_secrets.json file
found at:
   %s
with information from the {{ Cloud Console }}
{{ https://cloud.google.com/console }}
For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
""" % os.path.abspath(os.path.join(os.path.dirname(__file__),
                                   CLIENT_SECRETS_FILE))


def get_authenticated_service(args):
    flow = flow_from_clientsecrets(
        CLIENT_SECRETS_FILE,
        scope=YOUTUBE_READ_WRITE_SCOPE,
        message=MISSING_CLIENT_SECRETS_MESSAGE)

    storage = Storage("asm-archive-youtube-updater-oauth2.json")
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, storage, args)

    return build(
        YOUTUBE_API_SERVICE_NAME,
        YOUTUBE_API_VERSION,
        http=credentials.authorize(httplib2.Http()))


def try_operation(label, function, retries=3, sleep=4):
    success = False
    retry_count = 0
    while not success and retry_count < retries:
        retry_count += 1
        print "Try %d: %s" % (retry_count, label)
        result = function()
        time.sleep(sleep)
        if result is not None:
            success = True
            break
    if success:
        return result
    print "Failed: %s. Sleeping for 600 seconds." % label
    time.sleep(600)
    return None


URL_REGEX = re.compile(r"^(?:(http(s)?:\/\/)?((w){3}.)?youtu(be|.be)?(\.com)?\/.+v=)([a-zA-Z0-9_-]{11}).*")


def get_video_id_try_url(possible_url):
    if re.match(r"^[a-zA-Z0-9_-]{11}$", possible_url):
        return possible_url
    matches = URL_REGEX.match(possible_url)
    if not matches:
        return None
    return matches.group(7)
