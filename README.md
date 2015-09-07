Convert Trello list to HTML
===========================

This tool converts a [Trello](https://trello.com/) list to a HTML page. It is intended for creating newsletters or simple web pages.

Features
--------

- Fetch markdown content from description, attachments, Google Drive or Dropbox
- Fetch images from attachments, Google Drive or Dropbox
- Trello labels to CSS classes
- Resizes and autorotates images
- Customizable
    - Use your own HTML template
    - Add your own CSS
    - Add extra markdown modules
- Smart Table of Contents (Markdown extension): looks for the `${toc}` marker, collects H1 tags
  found *after* the marker and replaces it with a table of content.
- Premailer: prepare web page for use in an email 
- Python 3
- Free software, MIT license
- Beautiful default template


Dependencies
------------

- [colorama](https://github.com/tartley/colorama) - Simple cross-platform colored terminal text
- [markdown](https://github.com/waylan/Python-Markdown) - Markdown implementation, with extension support
- [requests](http://www.python-requests.org/en/latest/) - Elegant and simple HTTP library for
- [rfc6266](https://github.com/g2p/rfc6266) -  Content-Disposition header support
- [premailer](http://premailer.io/) - Turns CSS blocks into style attributes
- [wand](http://docs.wand-py.org/) - Ctypes-based simple ImageMagick binding

Usage
-----

See `trello-to-html.py --help`:

```
usage: trello-to-html.py [-h] --board BOARD (--list | --convert LIST)

Convert Trello list to web page.

optional arguments:
  -h, --help      show this help message and exit
  --board BOARD   Trello board
  --list          show Trello lists
  --convert LIST  convert Trello list
```

For emailing and packaging, use `mail.py --subject SUBJECT --to EMAIL` and `zip.py`. The first one will send an email
with inline images to the address you specify, the second one will create a `basename.zip` file in your output folder.

Configure
---------

Copy the `settings-default.json` file to `settings.json` and change the settings according to your preferences.
