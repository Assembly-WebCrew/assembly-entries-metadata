# Initialization

    python bootstrap.py
    bin/buildout
    # First get client_id.json to client_secrets.json from https://console.cloud.google.com/
    # After that run:
    bin/python lib/youtube-get-credentials.py

# Usage

First copy the example variables file into the usable format and edit
its contents to match proper settings (like year):

    cp variables.inc.sh.example variables.inc.sh

Shell scripts in the root directory are meant to be used for data
updates and fetches. The main logic generally resides in `lib/*.py`
files and these shell scripts only give them appropriate arguments
using `variables.inc.sh` file's contents.

This provides scripts for handling data during and after the
event. There are different approaches for handling published entries
during the event and outside the event depending on if the entry
information is available in machine-friendly format.

# Data handling during the event

During the event the main goal of Assembly Archive and videos on
Youtube is to provide a preview possibility for visitors so that they
can more carefully base their votes on PMS, and for people who miss
the competition from the big screen to be able to view competition
entries. This is divided into three different processes based on the
type of the content we're working with:

1. Image file acquisition, conversion, and thumbnail creation.
2. Music file acquisition, video conversion, and Youtube upload.
3. Video file acquisition and Youtube upload, or Youtube link
   handling.

Entry information (names, authors, vote results, detailed entry
information) usually comes directly from PMS. Image and music files
can be downloaded from PMS, but videos usually go through video
conversion process and get uploaded to Youtube by someone else.

## Contacts and rights needed during the event

1. access to PMS with entry download rights for music and graphics
   competitions, or some other way to acquire such files.
1.1. This also needs access to someone who can make 1920x1080 music
     background file that can be added to videos for music entries
     that are uploaded to Youtube.
2. API access rights to PMS.
3. Youtube account.
4. Address for elaine data dump (vods.xml).
5. All the people who may upload data to Youtube.

PMS access is for the fact that we need to convert images and music to
a format that can be viewed through web. They are usually available
through PMS with compo admin rights. Other places to acquire them
are from people who are responsible for such competitions and through
Assembly file servers that Compocrew and HallAV use to share slides
for graphics competitions. Files can also be shared through the
sneakernet between Compocrew and HallAV, so it's usually beneficial to
contact the people responsible for graphics and music competitions
beforehand so that they know about who to contact if there are any
issues.

We use Youtube for music entry playback instead of providing our own
web based player, as that way we can leverage the large amount of
devices and browsers that work with Youtube. This is the reason why we
need a specific background for music competition entries. 1920x1080
resolution is just for it that we can make Youtube to use the highest
sound quality for the playback.

API access to PMS

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

"Export compos" link.
https://pms.paeae.fi/asm15/compos/admin/export/

## Process for Elaine based data

# Library

A reusable library that is used to handle these data files
programmatically is at `lib/asmmetadata.py`.

# Data format

TODO
