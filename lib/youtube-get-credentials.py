#!/usr/bin/env python

import youtube
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    youtube.add_auth_args(parser)
    args = parser.parse_args()
    yt_service = youtube.get_authenticated_service(args)
