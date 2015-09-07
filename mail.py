#! /usr/bin/env python3

import argparse
import json
import mimetypes
import smtplib
import os
import premailer

from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
import sys

__author__ = 'tigge'

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


def generate_message(folder, mail_subject, mail_from, mail_to):

    message = MIMEMultipart()
    message['Subject'] = mail_subject
    message['From'] = mail_from
    message['To'] = mail_to

    related = MIMEMultipart('related')
    message.attach(related)

    content = open(os.path.join(folder, "generated.html")).read()
    images = []
    print(os.listdir(folder))
    for file in os.listdir(folder):
        _, extension = os.path.splitext(file)
        print(file, _, extension, mimetypes.types_map.get(extension, "unknown").startswith("image/"))
        if mimetypes.types_map.get(extension, "unknown").startswith("image/"):
            with open(os.path.join(folder, file), 'rb') as fp:
                img = MIMEImage(fp.read(), name=file)
                img.add_header('Content-ID', "<" + file + "@mailer>")
                img.add_header('Content-Disposition', 'inline', filename=file)
                content = content.replace(file, "cid:" + file + "@mailer")
                images.append(img)

    related.attach(MIMEText(content, 'html', "utf-8"))
    for image in images:
        related.attach(image)

    return message


def send_message(message, smtp_server, smtp_port, smtp_username, smtp_password):
    print(smtp_server, smtp_port)
    s = smtplib.SMTP(host=smtp_server, port=smtp_port)
    s.starttls()
    s.login(smtp_username, smtp_password)
    s.send_message(message)
    s.quit()


def main():

    load_settings()

    parser = argparse.ArgumentParser()
    parser.add_argument("--subject", required=True)
    parser.add_argument("--to", required=True)

    args = parser.parse_args()

    message = generate_message(get_setting("folder"), args.subject, get_setting("mail")["from"], args.to)
    send_message(message, get_setting("mail")["smtp"]["server"], get_setting("mail")["smtp"]["port"],
                 get_setting("mail")["smtp"]["username"], get_setting("mail")["smtp"]["password"])


if __name__ == "__main__":
    sys.exit(main())
