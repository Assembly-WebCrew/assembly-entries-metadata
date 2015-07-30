= Initialization =

    python bootstrap.py
    bin/buildout

= Usage =

First copy the example variables file into the usable format and edit
its contents to match proper settings (like year):

    cp variables.inc.sh.example variables.inc.sh

Shell scripts in the root directory are meant to be used for data
updates and fetches. The main logic generally resides in `lib/*.py`
files and these shell scripts only give them appropriate arguments
using `variables.inc.sh` file's contents.

== Library ==

A reusable library that is used to handle these data files
programmatically is at `lib/asmmetadata.py`.

= Data format =

