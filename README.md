Overview
--------
This project *attempts* to render John Gruber's markdown format to `PNG` (or
other image formats).  The markdown syntax lives 
[here](http://daringfireball.net/projects/markdown/syntax).

Currently, it uses Python's PIL image library to render the results and 
python-markdown to parse markdown.

**NOTE**: This has only been tested on Python 2.6 so far...

***

Supported Elements
------------------
- Block Elements
    - paragraph
    - headers
    - blockquote
    - lists
    - code block
    - hr
- Inline Elements
    - anchor
    - emphasis
    - code

***

Getting Started
---------------
    easy_install PIL
    easy_install Markdown
    
    cd src
    python convert.py <markdown_filename> [output_filename] [width]
    
Tests
-----
1. Item 1
1. Item 2 - This is a test of a longer string in a list.  Hopefuly this wraps around properly.
1. Item 3
1. Item 4
    1. Subitem 1
    1. Subitem 2
1. Item 5

