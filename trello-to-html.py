#! /usr/bin/env python3

import argparse
import os
from string import Template
import sys

import colorama
import requests
import markdown
import rfc6266

import utilities
from trello import Trello


OUTPUT_FOLDER = "output"
OUTPUT_NAME = "generated"
OUTPUT_WIDTH = 600
OUTPUT_TITLE = "Generated HTML"

def get_attachment(url):
    url = utilities.fix_google_drive_download_url(url)
    url = utilities.fix_dropbox_download_url(url)

    response = requests.get(url)
    mimetype = response.headers.get("content-type").lower().split(";")[0].strip()
    filename = rfc6266.parse_requests_response(response).filename_unsafe

    if not mimetype.startswith("text/") and not mimetype.startswith("image/"):
        raise Exception("Unhandled file type {0}, {1}, {2}".format(url, mimetype, filename))

    if mimetype.startswith("text/"):
        response.encoding = "utf-8"

    attachment = {
        "name": filename,
        "mime": mimetype,
        "url": response.url
    }

    if mimetype.startswith("text/"):
        attachment["content"] = response.text
    else:
        attachment["content"] = response.content

    return attachment


def generate(trello_list):

    articles = []

    for number, trello_card in enumerate(trello_list, start=1):

        print("\n" + str(number) + ".", trello_card["name"] + ":")

        article = {
            "title": trello_card["name"],
            "content": "",
            "images": [],
            "labels": []
        }

        # Add content
        for trello_attachment in trello_card["attachments"]:

            attachment = get_attachment(trello_attachment["url"])

            if attachment["mime"].startswith("text/"):
                article["content"] += attachment["content"]
                print(" - Markdown from", attachment["url"])
            else:
                article["images"].append(attachment)
                print(" - Image from file", attachment["url"])

        # Fallback on description
        if article["content"] == "":
            article["content"] = trello_card["desc"]

        if article["content"] == "":
            print(" - Status:", colorama.Fore.RED + "Warning (no content)", colorama.Fore.RESET)
            continue

        # Add labels
        for label in trello_card["labels"]:
            article["labels"].append(label["name"] if label["name"] != "" else "color-" + label["color"])

        print(" - Labels:", colorama.Fore.MAGENTA + ", ".join(article["labels"]), colorama.Fore.RESET)
        print(" - Status:", colorama.Fore.GREEN + "Ok", colorama.Fore.RESET)

        articles.append(article)

    # Create output folder
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    # Generate HTML from Markdown
    text = ""
    for article in articles:
        classes = ""
        for label in article["labels"]:
            classes += " " + label
        text += '<section class="' + classes + '" markdown="1">\n'
        text += article["content"] + "\n</section>\n\n"
        if "noline" not in article["labels"]:
            text += "------------------------------------\n\n"
    md = markdown.Markdown(
        extensions=['markdown.extensions.extra', 'markdown.extensions.attr_list', 'markdown.extensions.smarty',
                    'markdown_smarttoc'],
        output_format="html5")
    html = md.convert(text)
    open(os.path.join(OUTPUT_FOLDER, OUTPUT_NAME + ".md"), "w").write(text)

    # Save images
    for article in articles:
        for image in article["images"]:
            image_filename = os.path.join(OUTPUT_FOLDER, image["name"])
            open(image_filename, "wb").write(image["content"])
            utilities.fix_image(image_filename, OUTPUT_WIDTH)

    # Generate CSS
    html_template = Template(open("default.css.template").read())
    css_generated = html_template.substitute(width=OUTPUT_WIDTH)

    # Add generated Markdown to HTML template
    html_template = Template(open("default.html.template").read())
    html_generated = html_template.substitute(title=OUTPUT_TITLE, content=html, css=css_generated)

    open(os.path.join(OUTPUT_FOLDER, OUTPUT_NAME + ".html"), "w").write(html_generated)

    print("\nPreview: file://" + os.path.abspath(os.path.join(OUTPUT_FOLDER, OUTPUT_NAME + ".html")))


def main():

    API_KEY = "443c66695279580563e6aee40eed2811"

    colorama.init()

    parser = argparse.ArgumentParser(description='Publish newsletter from Trello list.')
    parser.add_argument('--board', metavar='BOARD', type=str, help='Trello board', required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--list', action='store_true', help='show Trello lists')
    group.add_argument('--publish', metavar='LIST', type=str, help='publish Trello list')
    args = parser.parse_args()

    trello = Trello(API_KEY)

    # Read or generate token
    try:
        trello.set_token(open(".token", "r").read())
    except:
        print("Go to", trello.get_token_url("Newsletter"), "and authorize the application. After you have authorized",
              "the application you'll be given a token. Copy and paste that here", "\n")
        trello.set_token(input("Enter your token: "))
        open(".token", "w").write(trello.get_token())

    # List Trello lists
    if args.list:
        trello_lists = trello.boards_get_list_open(args.board)
        for trello_list in trello_lists:
            print(trello_list["name"])
        return 0

    # Publish Trello list
    elif args.publish is not None:
        trello_lists = trello.boards_get_list_open(args.board)
        for trello_list in trello_lists:
            if trello_list["name"] == args.publish:
                print("Publishing", trello_list["name"])
                trello_list = trello.list_get_cards(trello_list["id"])
                generate(trello_list)
                return 0
        else:
            print("No such list")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
