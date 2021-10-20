import json
from abc import ABC, abstractmethod
from pathlib import Path


class UsersStorage(ABC):

    @abstractmethod
    def add(self, username, password):
        pass

    @abstractmethod
    def exists(self, username):
        pass

    @abstractmethod
    def get_password(self, username):
        pass


class JSONUsersStorage(UsersStorage):

    def __init__(self, filename):
        self._filename = filename
        if not Path(filename).is_file():
            self.clear()

    def add(self, username, password):
        users = self._load()
        users[username] = password
        self._dump(users)

    def exists(self, username):
        return username in self._load()

    def get_password(self, username):
        return self._load()[username]

    def clear(self):
        self._dump({})

    def _dump(self, obj):
        with open(self._filename, 'w') as file:
            json.dump(obj, file)

    def _load(self):
        with open(self._filename) as file:
            return json.load(file)
