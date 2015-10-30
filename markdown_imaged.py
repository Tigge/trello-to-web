import os.path
import urllib.parse

import requests

import settings
import utilities
from markdown import Extension
from markdown.inlinepatterns import ImagePattern, IMAGE_LINK_RE


class ImageDownloadPattern(ImagePattern):
    def handleMatch(self, match):
        el = super(ImageDownloadPattern, self).handleMatch(match)
        urlparts = urllib.parse.urlparse(el.attrib["src"])
        if urlparts.netloc:
            response = requests.get(urlparts.geturl())
            filename = os.path.basename(urlparts.path)
            with open(os.path.join(settings.get("folder"), filename), "wb") as f:
                f.write(response.content)
                el.attrib["src"] = filename
            utilities.fix_image(os.path.join(settings.get("folder"), filename), settings.get("features")["width"])
        return el


class ImageDownload(Extension):
    def extendMarkdown(self, md, md_globals):
        md.inlinePatterns['image_link'] = ImageDownloadPattern(IMAGE_LINK_RE, md)


def makeExtension(configs={}):
    return ImageDownload(configs=configs)
