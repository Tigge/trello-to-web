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
import settings
from trello import Trello


def get_attachment(url):
    url = utilities.fix_google_drive_download_url(url)
    url = utilities.fix_dropbox_download_url(url)

    response = requests.get(url)
    response.raise_for_status()
    mimetype = response.headers.get("content-type").lower().split(";")[0].strip()
    filename = rfc6266.parse_requests_response(response).filename_unsafe

    if "X-Auto-Login" in response.headers:
        raise Exception("Login needed for {0}".format(url))

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
    if not os.path.exists(settings.get("folder")):
        os.makedirs(settings.get("folder"))

    # Generate html from articles
    html_section_template = Template(open(settings.get("template-section")).read())
    markdown_instance = markdown.Markdown(extensions=list(settings.get("extensions")),
                                          extension_configs=settings.get("extensions"), output_format="html5")
    html = ""
    for index, article in enumerate(articles):
        labels = ""
        if settings.get("features")["labels"]:
            labels = " ".join(article["labels"])

        open(os.path.join(settings.get("folder"), ".t2w-temp-" + str(index) + ".md"), "w").write(article["content"])
        article_html = markdown_instance.reset().convert(article["content"])
        html += html_section_template.substitute(content=article_html, labels=labels)

        if settings.get("features")["lines"] and "noline" not in article["labels"] and index != len(articles) - 1:
            line_html = markdown_instance.reset().convert("\n\n---\n\n")
            html += html_section_template.substitute(content=line_html, labels="")

    # Save images
    for article in articles:
        for image in article["images"]:
            image_filename = os.path.join(settings.get("folder"), image["name"])
            open(image_filename, "wb").write(image["content"])
            utilities.fix_image(image_filename, settings.get("features")["width"])

    # Generate CSS
    css_generated = ""
    for css_file in settings.get("css"):
        css_generated += open(css_file).read() + "\n\n"

    # Add generated Markdown to HTML template
    html_template = Template(open(settings.get("template")).read())
    html_generated = html_template.safe_substitute(title=settings.get("title"), content=html, css=css_generated)

    result_template = Template(html_generated)
    extra_args = {}
    if "markdown_smarttoc" in settings.get("extensions"):
        extra_args["toc"] = markdown_instance.toc
    result_generated = result_template.substitute(title=settings.get("title"), width=settings.get("features")["width"],
                                                  **extra_args)

    # Run premailer
    if settings.get("features")["premailer"]:
        open(os.path.join(settings.get("folder"), ".t2w-temp-" + settings.get("basename") + "-orignal.html"),
             "w").write(result_generated)
        premail_instance = premailer.Premailer(result_generated, keep_style_tags=True)
        result_generated = premail_instance.transform()

    open(os.path.join(settings.get("folder"), settings.get("basename") + ".html"), "w").write(result_generated)

    print("\nPreview: file://" + urllib.request.pathname2url(
        os.path.abspath(os.path.join(settings.get("folder"), settings.get("basename") + ".html"))))


def main():
    colorama.init()

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
        trello.user_get("me")
    except Exception as e:
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
