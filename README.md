# Initialization

    python bootstrap.py
    bin/buildout

# Usage

First copy the example variables file into the usable format and edit
its contents to match proper settings (like year):

    cp variables.inc.sh.example variables.inc.sh

Shell scripts in the root directory are meant to be used for data
updates and fetches. The main logic generally resides in `lib/*.py`
files and these shell scripts only give them appropriate arguments
using `variables.inc.sh` file's contents.

## Process for PMS based data

Get existing PMS categories:

    ./pms-get-categories.sh

Seed category data with entries when they are known:

    ./pms-merge-category-data.sh <category-name>

Do archive export and update PMS preview links:

    ./pms-update-preview-links.sh <category-name>

Do this during the event and either add ":public true" ":public false"
and ":ongoing true" ":ongoing false" fields to different compo
categories.

## Process for Elaine based data

# Library

A reusable library that is used to handle these data files
programmatically is at `lib/asmmetadata.py`.

# Data format

TODO
