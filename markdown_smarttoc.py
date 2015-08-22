from markdown.util import etree
import markdown

__author__ = 'tigge'


class SmartTocTreeporcessor(markdown.treeprocessors.Treeprocessor):

    def __init__(self):
        self.running = False
        self.headers = []


    def collect_headers(self, element, indent=0):
        if element.tag == "p" and element.text == "[[toc]]":
            self.running = True
        if element.tag == "h1" and self.running:
            element.attrib["id"] = "toc-" + str(len(self.headers))
            self.headers.append({"anchor": element.attrib["id"], "text": element.text})

        for child in element:
            self.collect_headers(child, indent=indent+1)

    def build_toc(self):
        root = etree.Element("div")
        root.attrib["class"] = "toc"
        ul = etree.SubElement(root, "ul")
        for header in self.headers:
            li = etree.SubElement(ul, "li")
            a = etree.SubElement(li, "a", href="#" + header["anchor"])
            a.text = header["text"]
        return root

    def insert_toc(self, element, parent, index):

        if element.tag == "p" and element.text == "[[toc]]":
            parent[index] = self.build_toc()

        for index, child in enumerate(element):
            self.insert_toc(child, element, index)

    def run(self, root):
        self.collect_headers(root)
        self.insert_toc(root, None, 0)


class SmartTocExtension(markdown.Extension):

    def __init__(self, *args, **kwargs):
        super(SmartTocExtension, self).__init__(*args, **kwargs)

    def extendMarkdown(self, md, md_globals):
        md.registerExtension(self)
        md.treeprocessors.add("toc", SmartTocTreeporcessor(), "_end")


def makeExtension(*args, **kwargs):
    return SmartTocExtension(*args, **kwargs)
