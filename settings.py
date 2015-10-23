import json

__author__ = 'tigge'

# Load default settings, then try local
__settings = json.load(open("settings-default.json", "r"))
try:
    __settings = json.load(open("settings.json", "r"))
except IOError:
    pass


def get(setting):
    global __settings
    return __settings[setting]
