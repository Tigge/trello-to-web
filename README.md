Convert Trello list to HTML
===========================

Features
--------

- Fetch markdown from description, attachment, Google Drive or Dropbox
- Fetch images from attachment, Google Drive or Dropbox
- Labels to CSS classes
- Smart table of contents, looks for the `[[toc]]` marker, collects H1 tags
  found *after* the marker and replaces it with a table of content.
- Resizes and autorotates images
- Python 3

Dependencies
------------

- colorama
- requests
- markdown
- rfc6266

Usage
-----

See `trello-to-html.py --help`.
