#! /usr/bin/env python3

import argparse
import json
import os
from string import Template
import sys
import urllib.request

import colorama
import requests
import markdown
import rfc6266

import utilities
from trello import Trello


SETTINGS = json.load(open("settings-default.json", "r"))


def get_setting(setting):
    global SETTINGS
    return SETTINGS[setting]


def load_settings():
    global SETTINGS
    try:
        SETTINGS = json.load(open("settings.json", "r"))
    except IOError:
        pass


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
    if not os.path.exists(get_setting("folder")):
        os.makedirs(get_setting("folder"))

    # Generate HTML from Markdown
    html_section_template = Template(open(get_setting("template-section")).read())
    markdown_text = ""
    for index, article in enumerate(articles):
        labels = ""
        if get_setting("features")["labels"]:
            labels = " ".join(article["labels"])

        markdown_text += html_section_template.substitute(content=article["content"], labels=labels)
        if get_setting("features")["lines"] and "noline" not in article["labels"] and index != len(articles) - 1:
            markdown_text += html_section_template.substitute(content="\n\n---\n\n", labels="")

    open(os.path.join(get_setting("folder"), get_setting("basename") + ".md"), "w").write(markdown_text)

    markdown_instance = markdown.Markdown(extensions=get_setting("extensions"), output_format="html5")
    html = markdown_instance.convert(markdown_text)

    # Save images
    for article in articles:
        for image in article["images"]:
            image_filename = os.path.join(get_setting("folder"), image["name"])
            open(image_filename, "wb").write(image["content"])
            utilities.fix_image(image_filename, get_setting("features")["width"])

    # Generate CSS
    css_generated = ""
    for css_file in get_setting("css"):
        css_generated += open(css_file).read() + "\n\n"

    # Add generated Markdown to HTML template
    html_template = Template(open(get_setting("template")).read())
    html_generated = html_template.safe_substitute(title=get_setting("title"), content=html, css=css_generated)
    result_template = Template(html_generated)
    result_generated = result_template.substitute(title=get_setting("title"), width=get_setting("features")["width"])

    open(os.path.join(get_setting("folder"), get_setting("basename") + ".html"), "w").write(result_generated)

    print("\nPreview: file://" + urllib.request.pathname2url(
        os.path.abspath(os.path.join(get_setting("folder"), get_setting("basename") + ".html"))))


def main():
    colorama.init()

    load_settings()

    parser = argparse.ArgumentParser(description='Publish newsletter from Trello list.')
    parser.add_argument('--board', metavar='BOARD', type=str, help='Trello board', required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--list', action='store_true', help='show Trello lists')
    group.add_argument('--publish', metavar='LIST', type=str, help='publish Trello list')
    args = parser.parse_args()

    trello = Trello("443c66695279580563e6aee40eed2811")

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
