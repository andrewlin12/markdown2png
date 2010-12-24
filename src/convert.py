import os
import sys

import md2png

if __name__ == "__main__":
    args = sys.argv
    while not args[0].endswith("convert.py"):
        args = args[1:]
    args = args[1:]

    if len(args) < 2:
        print "Usage: python convert.py <markdown-filename> <width> [output-filename]"
        quit()

    input_filename = args[0]

    width = int(args[1])

    output_filename = os.path.splitext(args[0])[0] + ".png"
    if len(args) > 2:
        output_filename = args[2]

    print "Reading %s" % input_filename
    f = open(input_filename)
    img = md2png.md2png(f.read(), (0, 0, width))
    f.close()

    print "Saving to %s" % output_filename
    # img.save(output_filename)
    img.show()
