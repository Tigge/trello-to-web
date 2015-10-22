import requests

__author__ = 'tigge'


class Trello:

    _APIURL = "https://trello.com/1/"

    def __init__(self, apikey):
        self._apikey = apikey
        self._apitoken = None

    def _fetch(self, url, **params):
        base_params = {"key": self._apikey, "token": self._apitoken}
        base_params.update(params)
        response = requests.get(self._APIURL + url, params=base_params)
        response.raise_for_status()
        return response.json()

    def set_token(self, apitoken):
        self._apitoken = apitoken

    def get_token(self):
        return self._apitoken

    def get_token_url(self, name):
        return "{0}authorize?key={1}&name={2}&expiration=30days&response_type=token".format(self._APIURL, self._apikey, name)

    def user_get(self, user):
        return self._fetch("members/{0}".format(user))

    def boards_get_list(self, board):
        return self._fetch("board/{0}/lists".format(board))

    def boards_get_list_open(self, board):
        return self._fetch("board/{0}/lists/open".format(board))

    def list_get_cards(self, list):
        return self._fetch("list/{0}/cards".format(list), attachments="true")

