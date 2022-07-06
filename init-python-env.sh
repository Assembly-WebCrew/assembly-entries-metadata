#!/usr/bin/env bash

set -euo pipefail

mkdir -p venv
python3 -mvenv venv
venv/bin/pip install \
             dlib mypy Pillow python-dateutil pytz types_python_dateutil
