import re

__author__ = 'tigge'

from wand.image import Image


def fix_image(filename, max_width):
    with Image(filename=filename) as img:
        img.auto_orient()
        if img.width > max_width:
            ratio = img.height / img.width
            img.resize(width=max_width, height=round(max_width * ratio))
        img.type = 'optimize'
        img.compression_quality = 80
        img.save(filename=filename)


def fix_google_drive_download_url(url):
    url = re.sub(r"https://drive\.google\.com/(?:a/.*){0,1}file/d/(.*?)/view\?usp=.*",
                 r"https://drive.google.com/uc?authuser=0&id=\1&export=download", url)
    return url


def fix_dropbox_download_url(url):
    url = url[:-5] + "?dl=1" if url.startswith("https://www.dropbox.com") and url.endswith("?dl=0") else url
    return url


