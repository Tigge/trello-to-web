#! /usr/bin/env python3

import os
import zipfile
import sys
import settings

__author__ = 'tigge'


def main():
    zipfilename = os.path.join(settings.get("folder"), settings.get("basename") + ".zip")
    zip = zipfile.ZipFile(zipfilename, mode="w", )

    for filename in os.listdir(settings.get("folder")):
        print(filename, os.path.basename(zipfilename),filename == os.path.basename(zipfilename))
        if not filename.startswith(".t2w-temp-") and filename != os.path.basename(zipfilename):
            zip.write(os.path.join(settings.get("folder"), filename), arcname=filename)

    zip.close()


if __name__ == "__main__":
    sys.exit(main())
