#!/usr/bin/env python

import asmyoutube
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    asmyoutube.add_auth_args(parser)
    args = parser.parse_args()
    yt_service = asmyoutube.get_authenticated_service(args)
