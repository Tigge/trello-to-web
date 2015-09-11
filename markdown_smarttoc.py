from markdown.util import etree
import markdown

__author__ = 'tigge'


class SmartTocTreeporcessor(markdown.treeprocessors.Treeprocessor):
    def __init__(self, md):
        super(SmartTocTreeporcessor, self).__init__(md)
        self.running = False
        self.headers = []

    def collect_headers(self, element, indent=0):
        if element.tag == "p" and element.text == "${toc}":
            self.running = True
        if element.tag == "h1" and self.running:
            element.attrib["id"] = "toc-" + str(len(self.headers))
            text = element.text
            for postprocessor in self.markdown.postprocessors.values():
                text = postprocessor.run(text)
            self.headers.append({"anchor": element.attrib["id"], "text": text})

        for child in element:
            self.collect_headers(child, indent=indent + 1)

    def build_toc(self):
        string = '<div class="toc">\n'
        string += ' <ul>\n'
        for header in self.headers:
            string += '  <li><a href="#{0}">{1}</a></li>'.format(header["anchor"], header["text"])
        string += ' </ul>\n'
        string += '</div>'
        return string

    def run(self, root):
        self.collect_headers(root)
        self.markdown.toc = self.build_toc()


class SmartTocExtension(markdown.Extension):
    def __init__(self, *args, **kwargs):
        super(SmartTocExtension, self).__init__(*args, **kwargs)

    def extendMarkdown(self, md, md_globals):
        md.registerExtension(self)
        treeprocessor = SmartTocTreeporcessor(md)
        md.treeprocessors.add("toc", treeprocessor, "_end")


def makeExtension(*args, **kwargs):
    return SmartTocExtension(*args, **kwargs)
