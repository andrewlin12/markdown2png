Overview
--------
This project attempts to render John Gruber's markdown format to `PNG` (or
other image formats).  The markdown syntax lives 
[here](http://daringfireball.net/projects/markdown/syntax).blahblah

Currently, it uses Python's PIL image library to render the results and 
python-markdown to parse markdown.

*NOTE*: This has only been tested on Python 2.6 so far...

***

Supported Elements
------------------
- headers
- unordered list
- paragraph
- code block
- hr
- blockquote
- emphasis
- code
- anchor

***

Getting Started
---------------
    easy_install PIL
    easy_install Markdown
    
    cd src
    python convert.py <markdown_filename> [output_filename] [width]