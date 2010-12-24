import re
import sys

import markdown
from markdown import etree

import Image, ImageDraw, ImageFont

IMAGE_BLOCK_HEIGHT = 1000

class ImageExtension(markdown.Extension):
    def __init__(self, width_spec):
        self.width_spec = width_spec

    def get_image(self):
        return self.treeprocessor.get_image()

    def extendMarkdown(self, md, md_globals):
        self.treeprocessor = ImageTreeprocessor(self.width_spec)
        md.treeprocessors.add('m2png', self.treeprocessor, '_end')


class ImageTreeprocessor(markdown.treeprocessors.Treeprocessor):
    """
    Recusively walks the parsed markdown and renders to an image.  Uses chunks
    of IMAGE_BLOCK_HEIGHT to render parts of the markdown incrementally (without
    pre-measuring) and assembles the chunks at the end. 
    """

    def __init__(self, width_spec):
        # List of (Image, height) to be merged for the result
        self.current_image = None
        self.current_image_draw = None
        self.current_image_x = 0
        self.current_image_y = 0
        self.current_y = 0
        self.image_width = max(width_spec, key=lambda x: x[2])[2]
        self.images = []

        # TODO: Make this configurable
        self.image_font = ImageFont.truetype("/home/andrew/.fonts/WhiskeyTown-Sober.ttf", 16)

        self.width_spec = width_spec
        self.width_spec.sort()

    def compact_whitespace(self, text):
        return re.sub('\s+', ' ', text)

    def ensure_image(self, h):
        if self.current_image_y + h > self.current_image.size[1]:
            if self.current_image_y == 0:
                print "Image block size too small!  Results will be cropped..."
                return

            print "need new image block"
            self.new_image_block()

    def get_image(self):
        # Add the last used image if necessary
        self.save_image_block()

        height = reduce(lambda x, y: x + y[1], self.images, 0)
        final = Image.new("RGBA", (self.image_width, height))
        y = 0
        for img in self.images:
            final.paste(img[0], (0, y))
            y += img[1]

        return final

    def handle_node(self, node):
        print "Handling %s" % node.tag
        handlers = {
            "p": self.handle_paragraph,
        }
        handlers.get(node.tag, self.handle_unknown)(node)
        if len(node) > 0:
            for child in node:
                self.handle_node(child)

    def handle_paragraph(self, node):
        text = self.compact_whitespace(node.text)

        self.render_wrapped_text(text, (255, 255, 255, 255), True)

    def handle_unknown(self, node):
        print "Unknown tag: %s" % node.tag

    def new_image_block(self):
        self.save_image_block()

        self.current_image = Image.new("RGBA", (self.image_width, IMAGE_BLOCK_HEIGHT))
        self.current_image_draw = ImageDraw.Draw(self.current_image)
        self.current_image_y = 0

    def render_wrapped_text(self, text, color, end_block=False):
        start_index = 0
        end_index = 0
        draw = self.current_image_draw

        parts = text.split(" ")
        while end_index < len(parts):
            w = 0
            while end_index < len(parts):
                (w, h) = draw.textsize(" ".join(parts[start_index:end_index + 1]),
                                       font=self.image_font)
                if self.current_image_x + w > self.image_width:
                    break

                end_index += 1

            if end_index > start_index:
                self.ensure_image(h)

                text_frag = " ".join(parts[start_index:end_index])
                draw.text((self.current_image_x, self.current_image_y),
                          text_frag,
                          font=self.image_font, fill=color)

            if end_index < len(parts):
                self.current_image_x = 0

                self.current_image_y += h
                self.current_y += h
            else:
                # If we are at the end of a block, set X back to 0 
                if end_block:
                    self.current_image_x = 0

                    self.current_image_y += h
                    self.current_y += h
                # Otherwise, leave X at the end of the last word, plus a space
                else:
                    # Measure this segment with a space on the end 
                    (w, h) = draw.textsize(text_frag + " ", font=self.image_font)
                    self.current_image_x = self.current_image_x + w

            start_index = end_index

    def save_image_block(self):
        if self.current_image is not None:
            self.images.append((self.current_image, self.current_image_y))
            del self.current_image_draw

    def run(self, root):
        self.new_image_block()
        self.handle_node(root)

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
