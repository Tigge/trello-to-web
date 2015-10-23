#! /usr/bin/env python3

import mimetypes
import os
import zipfile
import sys
import settings

__author__ = 'tigge'


def main():
    filename = os.path.join(settings.get("folder"), settings.get("basename") + ".zip")
    zip = zipfile.ZipFile(filename, mode="w", )

    zip.write(os.path.join(settings.get("folder"), settings.get("basename") + ".html"),
              arcname=settings.get("basename") + ".html")
    for file in os.listdir(settings.get("folder")):
        _, extension = os.path.splitext(file)
        if mimetypes.types_map.get(extension, "unknown").startswith("image/"):
            zip.write(os.path.join(settings.get("folder"), file), arcname=file)

    zip.close()


if __name__ == "__main__":
    sys.exit(main())
