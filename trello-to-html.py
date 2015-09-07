#! /usr/bin/env python3

import argparse
import json
import os
from string import Template
import sys
import urllib.request

import colorama
import multiprocessing
import requests
import markdown
import rfc6266
import premailer

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


def get_artice(trello_card):
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
        else:
            article["images"].append(attachment)

    # Fallback on description
    if article["content"] == "":
        article["content"] = trello_card["desc"]

    if article["content"] == "":
        return None

    # Add labels
    for label in trello_card["labels"]:
        article["labels"].append(label["name"] if label["name"] != "" else "color-" + label["color"])

    return article


def generate(trello_list):
    articles = []

    pool = multiprocessing.Pool(processes=10)
    articles = pool.map(get_artice, trello_list)

    # Print status
    for number, (trello_card, article) in enumerate(zip(trello_list, articles), start=1):
        print("\n" + str(number) + ".", trello_card["name"] + ":")

        if article is None:
            print(" - Status:", colorama.Fore.RED + "Warning (no content)", colorama.Fore.RESET)
            continue

        images_str = ", ".join(map(lambda x: x["name"], article["images"]))
        print(" - Images:", colorama.Fore.CYAN + images_str, colorama.Fore.RESET)
        labels_str = ", ".join(article["labels"])
        print(" - Labels:", colorama.Fore.MAGENTA + labels_str, colorama.Fore.RESET)
        print(" - Status:", colorama.Fore.GREEN + "Ok", colorama.Fore.RESET)

    # Remove empty articles
    articles = list(filter(None, articles))

    # Create output folder
    if not os.path.exists(get_setting("folder")):
        os.makedirs(get_setting("folder"))


    # Generate html from articles
    html_section_template = Template(open(get_setting("template-section")).read())
    markdown_instance = markdown.Markdown(extensions=get_setting("extensions"), output_format="html5")
    html = ""
    for index, article in enumerate(articles):
        labels = ""
        if get_setting("features")["labels"]:
            labels = " ".join(article["labels"])

        open(os.path.join(get_setting("folder"), str(index) + ".md"), "w").write(article["content"])
        article_html = markdown_instance.reset().convert(article["content"])
        html += html_section_template.substitute(content=article_html, labels=labels)

        if get_setting("features")["lines"] and "noline" not in article["labels"] and index != len(articles) - 1:
            line_html = markdown_instance.reset().convert("\n\n---\n\n")
            html += html_section_template.substitute(content=line_html, labels="")

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
    extra_args = {}
    if "markdown_smarttoc" in get_setting("extensions"):
        extra_args["toc"] = markdown_instance.toc
    result_generated = result_template.substitute(title=get_setting("title"), width=get_setting("features")["width"],
                                                  **extra_args)

    # Run premailer
    if get_setting("features")["premailer"]:
        open(os.path.join(get_setting("folder"), get_setting("basename") + "-orignal.html"), "w").write(
            result_generated)
        premail_instance = premailer.Premailer(result_generated, keep_style_tags=True)
        result_generated = premail_instance.transform()

    open(os.path.join(get_setting("folder"), get_setting("basename") + ".html"), "w").write(result_generated)

    print("\nPreview: file://" + urllib.request.pathname2url(
        os.path.abspath(os.path.join(get_setting("folder"), get_setting("basename") + ".html"))))


def main():
    colorama.init()

    load_settings()

    parser = argparse.ArgumentParser(description='Convert Trello list to web page.')
    parser.add_argument('--board', metavar='BOARD', type=str, help='Trello board', required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--list', action='store_true', help='show Trello lists')
    group.add_argument('--convert', metavar='LIST', type=str, help='convert Trello list')
    args = parser.parse_args()

    trello = Trello("443c66695279580563e6aee40eed2811")

    # Read or generate token
    try:
        trello.set_token(open(".token", "r").read())
    except:
        print("Go to", trello.get_token_url("trello-to-html"), "and authorize the application. After you have"
              "authorized the application you'll be given a token. Copy and paste that here", "\n")
        trello.set_token(input("Enter your token: "))
        open(".token", "w").write(trello.get_token())

    # List Trello lists
    if args.list:
        trello_lists = trello.boards_get_list_open(args.board)
        for trello_list in trello_lists:
            print(trello_list["name"])
        return 0

    # Convert Trello list
    elif args.convert is not None:
        trello_lists = trello.boards_get_list_open(args.board)
        for trello_list in trello_lists:
            if trello_list["name"] == args.convert:
                print("Converting", trello_list["name"])
                trello_list = trello.list_get_cards(trello_list["id"])
                generate(trello_list)
                return 0
        else:
            print("No such list")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
