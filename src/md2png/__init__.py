import markdown
from markdown import etree

import Image, ImageDraw, ImageFont

class ImageExtension(markdown.Extension):
    def __init__(self, width_spec):
        self.width_spec = width_spec

    def get_image(self):
        return self.treeprocessor.get_image()

    def extendMarkdown(self, md, md_globals):
        self.treeprocessor = ImageTreeprocessor(self.width_spec)
        md.treeprocessors.add('m2png', self.treeprocessor, '_end')


class ImageTreeprocessor(markdown.treeprocessors.Treeprocessor):
    def __init__(self, width_spec):
        self.width_spec = width_spec

    def get_image(self):
        return Image.new("RGBA", (100, 100), (255, 255, 255, 255))

    def run(self, root):
        for node in root:
            print node.tag

        return root


def md2png(md_str, width_spec):
    """
    md_str: Valid markdown in a string
    width_spec: A list of tuples (y-offset, x-offset, width) specifying the
                the width constraints for rendering.  Each tuple in the list
                will be used for rendering of all lines between y-offset and
                the next greater y-offset.  The largest y-offset will be used
                until the end of rendering.
    """
    img_ext = ImageExtension(width_spec)

    md = markdown.Markdown(extensions=[img_ext])
    md.convert(md_str)

    return img_ext.get_image()
