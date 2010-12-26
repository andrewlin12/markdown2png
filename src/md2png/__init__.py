import re
import sys

import markdown
from markdown import etree

import Image, ImageDraw, ImageFont

BULLET_DIAMETER = 4
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

    def __init__(self, width_spec, config={}):
        # List of (Image, height) to be merged for the result
        self.image = None
        self.image_draw = None
        self.image_x = 0
        self.image_y = 0
        self.indent = 0
        # Stack of list types and item numbers
        self.list_types = []
        self.list_item_nums = []
        self.y = 0
        self.image_width = max(width_spec, key=lambda x: x[2])[2]
        self.images = []
        self.line_height = 0
        self.in_pre = False

        self.config = {
            "bold_font_path": "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
            "blockquote_indent": 16,
            "code_indent": 16,
            "code_font_path": "/usr/share/fonts/truetype/freefont/FreeMono.ttf",
            "code_font_size": 14,
            "default_font_path": "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
            "font_size": 12,
            "hr_padding": 0,
            "italics_font_path": "/usr/share/fonts/truetype/freefont/FreeSansOblique.ttf",
            "list_indent": 28,
            "list_item_margin_bottom": 4,
            "bullet_outdent": 8,
            "margin_bottom": 16,
        }
        self.config.update(config)

        # TODO: Make this configurable
        font_size = self.config["font_size"]
        default_font_path = self.config["default_font_path"]
        self.default_font = ImageFont.truetype(default_font_path, font_size)
        self.bold_font = ImageFont.truetype(self.config["bold_font_path"], font_size)
        self.code_font = ImageFont.truetype(self.config["code_font_path"], self.config["code_font_size"])
        self.h1_font = ImageFont.truetype(self.config["default_font_path"], font_size * 3)
        self.h2_font = ImageFont.truetype(self.config["default_font_path"], int(font_size * 2.5))
        self.h3_font = ImageFont.truetype(self.config["default_font_path"], font_size * 2)
        self.h4_font = ImageFont.truetype(self.config["default_font_path"], int(font_size * 1.75))
        self.h5_font = ImageFont.truetype(self.config["default_font_path"], int(font_size * 1.5))
        self.h6_font = ImageFont.truetype(self.config["default_font_path"], int(font_size * 1.25))
        self.italics_font = ImageFont.truetype(self.config["italics_font_path"], font_size)

        self.width_spec = width_spec
        self.width_spec.sort()

    def compact_whitespace(self, text):
        return re.sub('\s+', ' ', text)

    def ensure_image(self, h):
        if self.image_y + h > self.image.size[1]:
            if self.image_y == 0:
                print "Image block size too small!  Results will be cropped..."
                return

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

    def handle_a(self, node):
        text = node.text

        # TODO: Save the bounds for these link somewhere
        self.render_text(node.text, (100, 100, 255, 255), False)
        self.handle_children(node)
        self.render_text(node.tail, (255, 255, 255, 255), False)

    def handle_blockquote(self, node):
        indent = self.config["blockquote_indent"]
        self.indent += indent
        self.newline()
        self.handle_children(node)
        self.indent -= indent
        self.newline()

    def handle_code(self, node):
        text = node.text

        self.render_text(node.text, (255, 255, 255, 255), False, font=self.code_font)
        self.handle_children(node)
        self.render_text(node.tail, (255, 255, 255, 255), False)

    def handle_children(self, node):
        if len(node) > 0:
            for child in node:
                self.handle_node(child)

    def handle_div(self, node):
        if self.image_x != 0:
            self.newline()

        self.handle_children(node)

        if self.image_x != 0:
            self.newline()

    def handle_em(self, node):
        text = node.text

        self.render_text(node.text, (255, 255, 255, 255), False, font=self.italics_font)
        self.handle_children(node)
        self.render_text(node.tail, (255, 255, 255, 255), False)

    def handle_h(self, node):
        text = node.text

        font = getattr(self, node.tag + "_font")
        self.render_text(node.text, (255, 255, 255, 255), True, font=font)
        # TODO: Make this HR padding-bottom configurable
        self.newline()

    def handle_hr(self, node):
        self.newline()
        h = self.config["margin_bottom"]
        horizontal_padding = self.config["hr_padding"]
        self.image_draw.line((horizontal_padding, self.image_y + h / 2,
                              self.image_width - horizontal_padding, self.image_y + h / 2), fill=(255, 255, 255, 255))
        self.newline(h)

    def handle_li(self, node):
        list_type = self.list_types[-1]
        if list_type == "unordered":
            # Draw the bullet
            draw = self.image_draw
            (w, h) = draw.textsize("E", font=self.default_font)
            x = self.image_x - BULLET_DIAMETER - self.config["bullet_outdent"]
            y = self.image_y + (h - BULLET_DIAMETER) / 2
            draw.ellipse((x, y,
                          x + BULLET_DIAMETER,
                          y + BULLET_DIAMETER),
                          outline=(255, 255, 255, 255),
                          fill=(255, 255, 255, 255))

            self.render_text(node.text, (255, 255, 255, 255), True)
            self.handle_children(node)
        elif list_type == "ordered":
            # Draw the number
            draw = self.image_draw
            current_number = "%d" % self.list_item_nums[-1]
            (w, h) = draw.textsize(current_number, font=self.default_font)
            x = self.image_x - w - self.config["bullet_outdent"]
            draw.text((x, self.image_y), current_number + ".",
                      font=self.default_font,
                      fill=(255, 255, 255, 255))

            self.list_item_nums[-1] += 1

            self.render_text(node.text, (255, 255, 255, 255), True)
            self.handle_children(node)

        # REVIEW: Ignore tail text on li items b/c.  Is this okay?
        # self.render_text(node.tail, (255, 255, 255, 255), True)
        self.newline(self.config["list_item_margin_bottom"])

    def handle_node(self, node):
        print "Handling %s" % node.tag
        handlers = {
            "a": self.handle_a,
            "code": self.handle_code,
            "blockquote": self.handle_blockquote,
            "em": self.handle_em,
            "div": self.handle_div,
            "h1": self.handle_h,
            "h2": self.handle_h,
            "h3": self.handle_h,
            "h4": self.handle_h,
            "h5": self.handle_h,
            "h6": self.handle_h,
            "hr": self.handle_hr,
            "li": self.handle_li,
            "ol": self.handle_ol,
            "p": self.handle_p,
            "pre": self.handle_pre,
            "strong": self.handle_strong,
            "ul": self.handle_ul,
        }
        handlers.get(node.tag, self.handle_unknown)(node)
        print "Done with %s" % node.tag

    def handle_ol(self, node):
        indent = self.config["list_indent"]
        self.indent += indent
        self.newline()

        self.list_types.append("ordered")
        self.list_item_nums.append(1)
        self.handle_children(node)
        self.list_item_nums = self.list_item_nums[:-1]
        self.list_types = self.list_types[:-1]

        self.indent -= indent
        self.newline()

    def handle_p(self, node):
        self.render_text(node.text, (255, 255, 255, 255), False)
        self.handle_children(node)

        # TODO: Make padding-bottom of <p> configurable
        self.render_text(node.tail, (255, 255, 255, 255), True)
        self.newline(self.config["margin_bottom"])

    def handle_pre(self, node):
        old_in_pre = self.in_pre
        self.in_pre = True

        indent = self.config["code_indent"]
        self.indent += indent
        self.newline()

        self.handle_children(node)

        self.indent -= indent
        self.newline()

        self.in_pre = old_in_pre

    def handle_strong(self, node):
        text = node.text

        self.render_text(node.text, (255, 255, 255, 255), False, font=self.bold_font)
        self.handle_children(node)
        self.render_text(node.tail, (255, 255, 255, 255), False)

    def handle_ul(self, node):
        indent = self.config["list_indent"]
        self.indent += indent
        self.newline()

        self.list_types.append("unordered")
        self.handle_children(node)
        self.list_types = self.list_types[:-1]

        self.indent -= indent
        self.newline()

    def handle_unknown(self, node):
        print "Unknown tag: %s" % node.tag
        self.handle_children(node)

    def newline(self, h= -1):
        if h == -1:
            h = self.line_height

        self.image_x = self.indent
        self.image_y += h
        self.y += h

        self.line_height = 0

    def new_image_block(self):
        self.save_image_block()

        self.image = Image.new("RGBA", (self.image_width, IMAGE_BLOCK_HEIGHT))
        self.image_draw = ImageDraw.Draw(self.image)
        self.image_y = 0

    def render_text(self, text, color, end_block=False, font=None):
        if text is None:
            return

        if font is None:
            font = self.default_font

        if self.in_pre:
            draw = self.image_draw
            lines = text.split("\n")
            for line in lines:
                draw.text((self.image_x, self.image_y), line, font=font, fill=color)

                (w, h) = draw.textsize(line, font=font)
                self.line_height = max(h, self.line_height)
                self.newline()
        else:
            text = self.compact_whitespace(text)
            start_index = 0
            end_index = 0
            draw = self.image_draw

            parts = text.split(" ")
            while end_index < len(parts):
                w = 0
                while end_index < len(parts):
                    (w, h) = draw.textsize(" ".join(parts[start_index:end_index + 1]),
                                           font=font)
                    if self.image_x + w > self.image_width:
                        break

                    end_index += 1

                text_frag = " ".join(parts[start_index:end_index])
                if end_index > start_index:
                    self.ensure_image(h)

                    self.line_height = max(h, self.line_height)

                    draw.text((self.image_x, self.image_y),
                              text_frag,
                              font=font, fill=color)

                if end_index < len(parts):
                    self.newline()
                else:
                    # If we are at the end of a block, write out a newline 
                    if end_block:
                        self.newline()
                    # Otherwise, leave X at the end of the last word
                    else:
                        # Measure this segment 
                        (w, h) = draw.textsize(text_frag,
                                               font=font)
                        self.image_x += w

                start_index = end_index

    def save_image_block(self):
        if self.image is not None:
            self.images.append((self.image, self.image_y))
            del self.image_draw

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
