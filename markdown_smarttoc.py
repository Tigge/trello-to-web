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
            self.headers.append({"anchor": element.attrib["id"], "text": element.text})

        for child in element:
            self.collect_headers(child, indent=indent + 1)

    def build_toc(self):
        root = etree.Element("div")
        root.attrib["class"] = "toc"
        ul = etree.SubElement(root, "ul")
        for header in self.headers:
            li = etree.SubElement(ul, "li")
            a = etree.SubElement(li, "a", href="#" + header["anchor"])
            a.text = header["text"]
        return root

    def run(self, root):
        self.collect_headers(root)

        # Generate table of contents
        toc = self.markdown.serializer(self.build_toc())
        for postprocessor in self.markdown.postprocessors.values():
            toc = postprocessor.run(toc)
        self.markdown.toc = toc


class SmartTocExtension(markdown.Extension):
    def __init__(self, *args, **kwargs):
        super(SmartTocExtension, self).__init__(*args, **kwargs)

    def extendMarkdown(self, md, md_globals):
        md.registerExtension(self)
        treeprocessor = SmartTocTreeporcessor(md)
        md.treeprocessors.add("toc", treeprocessor, "_end")


def makeExtension(*args, **kwargs):
    return SmartTocExtension(*args, **kwargs)
