#! /usr/bin/env python3

import json
import mimetypes
import os
import zipfile

import sys

__author__ = 'tigge'

SETTINGS = json.load(open("settings-default.json", "r"))


def get_setting(setting):
    global SETTINGS
    return SETTINGS[setting]


def load_settings():
    global SETTINGS
    try:
        SETTINGS = json.load(open("settings.json", "r"))
    except IOError:
        pass


def main():

    load_settings()

    filename = os.path.join(get_setting("folder"), get_setting("basename") + ".zip")
    zip = zipfile.ZipFile(filename, mode="w",)

    zip.write(os.path.join(get_setting("folder"), get_setting("basename") + ".html"),
              arcname=get_setting("basename") + ".html")
    for file in os.listdir(get_setting("folder")):
        _, extension = os.path.splitext(file)
        if mimetypes.types_map.get(extension, "unknown").startswith("image/"):
            zip.write(os.path.join(get_setting("folder"), file), arcname=file)

    zip.close()

if __name__ == "__main__":
    sys.exit(main())
