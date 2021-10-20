import shutil
import os
import json
from enum import Enum
from pathlib import Path

import utils


class Commands(Enum):
    MAKE_DIR = 'makedir'
    MAKE_FILE = 'makefile'
    CD = 'cd'
    WRITE_FILE = 'write'
    SHOW_FILE = 'show'
    DEL = 'del'
    COPY = 'copy'
    MOVE = 'move'
    FREE = 'free'
    EXIT = 'exit'


class Errors(Enum):
    UNDEFINED_COMMAND = 'команда не найдена'
    NO_SPACE = 'в вашей директории не достаточно свободного места'
    NO_SPACE_LIMIT = 'ваша директория не имеет ограничений по объему'
    ALREADY_EXIST = 'директория или файл уже существует'
    FILE_ALREADY_EXIST = 'файл уже существует'
    DIR_ALREADY_EXIST = 'директория уже существует'
    NOT_EXIST = 'директория или файл не существует'
    FILE_NOT_EXIST = 'файл не существует'
    DIR_NOT_EXIST = 'директория не существует'
    WRONG_PASSWORD = 'неверный пароль для пользователя'


class FileManager:

    @staticmethod
    def make_dir(path):
        if path.exists():
            _print_error(Errors.ALREADY_EXIST)
        else:
            path.mkdir(parents=True)

    @staticmethod
    def make_file(path):
        if path.exists():
            _print_error(Errors.NOT_EXIST)
        else:
            path.touch()

    @staticmethod
    def cd(path):
        if path.is_dir():
            os.chdir(path)
        else:
            _print_error(Errors.DIR_NOT_EXIST)

    @staticmethod
    def show_file(path):
        if path.is_file():
            print(path.read_text())
        else:
            _print_error(Errors.FILE_NOT_EXIST)

    @staticmethod
    def delete(path):
        if path.is_dir():
            shutil.rmtree(path)
        elif path.is_file():
            path.unlink()
        else:
            _print_error(Errors.NOT_EXIST)

    @staticmethod
    def move(src_path, dst_path):
        if src_path.exists():
            shutil.move(src_path, dst_path)
        else:
            _print_error(Errors.NOT_EXIST)

    def __init__(self, root, username='', size=None):
        self._root = Path(root).resolve()
        if not self._root.is_dir():
            self.make_dir(self._root)
        os.chdir(self._root)
        self._username = username
        self._size = size

    @property
    def working_dir(self):
        return Path.cwd().relative_to(self._root)

    @property
    def root_size(self):
        return utils.dir_size(self._root)

    @property
    def invite(self):
        working_dir = str(
            self.working_dir).replace('\\', '/').replace('.', '/')
        if working_dir[0] != '/':
            working_dir = '/' + working_dir
        if self._username:
            return f'{self._username}:{working_dir}$ '
        else:
            f'{working_dir}$ '

    def write_file(self, path):
        if path.is_file():
            text = input()
            if self._size and self._is_no_space(utils.str_size(text)):
                _print_error(Errors.NO_SPACE)
                self.free()
            else:
                with open(path, 'a') as file:
                    file.write(text)
        else:
            _print_error(Errors.FILE_NOT_EXIST)

    def copy(self, src_path, dst_path):
        if src_path.is_file():
            if self._size and self._is_no_space(utils.file_size(src_path)):
                _print_error(Errors.NO_SPACE)
                self.free()
            else:
                shutil.copy(src_path, dst_path)
        elif src_path.is_dir():
            if self._size and self._is_no_space(utils.dir_size(src_path)):
                _print_error(Errors.NO_SPACE)
                self.free()
            else:
                shutil.copytree(src_path, dst_path)
        else:
            _print_error(Errors.NOT_EXIST)

    def free(self):
        if self._size:
            free_size = self._size - self.root_size
            print(f'Всего: {self._size}Б; Свободно: {free_size}Б')
        else:
            _print_error(Errors.NO_SPACE_LIMIT)

    def command_line(self):
        while True:
            command, *paths = input(self.invite).split()
            paths = list(map(self._get_path, paths))
            if command == Commands.MAKE_DIR.value:
                self.make_dir(paths[0])
            elif command == Commands.MAKE_FILE.value:
                self.make_file(paths[0])
            elif command == Commands.CD.value:
                self.cd(paths[0])
            elif command == Commands.WRITE_FILE.value:
                self.write_file(paths[0])
            elif command == Commands.SHOW_FILE.value:
                self.show_file(paths[0])
            elif command == Commands.DEL.value:
                self.delete(paths[0])
            elif command == Commands.COPY.value:
                self.copy(paths[0], paths[1])
            elif command == Commands.MOVE.value:
                self.move(paths[0], paths[1])
            elif command == Commands.FREE.value:
                self.free()
            elif command == Commands.EXIT.value:
                break
            else:
                _print_error(Errors.UNDEFINED_COMMAND)

    def _get_path(self, str_path):
        if str_path[0] == '/':
            path = Path(self._root, str_path[1:])
        elif str_path.find('..') != -1:
            path = Path()
            for path_part in Path(str_path).parts:
                resolved_path_part = Path(path_part).resolve()
                if (path_part == '..' and
                        resolved_path_part.is_relative_to(self._root)):
                    path = resolved_path_part
                elif path_part != '..':
                    path = path.joinpath(path_part)
                else:
                    path = self._root
        else:
            resolved_path = Path(str_path).resolve()
            if (resolved_path.is_absolute() and
                    resolved_path.relative_to(self._root)):
                path = Path(str_path).resolve()
            else:
                path = Path.cwd().joinpath(Path(str_path))
        return path

    def _is_no_space(self, extra):
        if self.root_size + extra > self._size:
            return True
        return False


class MultiUserFileManager:

    def __init__(self, users, root=None, size=None):
        self._users = users
        if root is not None:
            self._root = Path(root).resolve()
            self.make_root_dir()
        else:
            self._root = root
        self._size = size
        self._authorized = False
        self._username = None

    def export_settings(self, filename='settings.json'):
        with open(filename) as file:
            self._root = Path(json.load(file)['working_directory']).resolve()
            self.make_root_dir()
        return self

    def make_root_dir(self):
        if not self._root.is_dir():
            self._root.mkdir(parents=True)

    def auth(self):
        username = input('Логин: ')
        password = input('Пароль: ')
        if self._users.exists(username):
            if password == self._users.get_password(username):
                self._authorized = True
        else:
            self._users.add(username, password)
            self._authorized = True
        self._username = username

    def start(self):
        if self._authorized:
            user_working_dir = Path(self._root, self._username)
            FileManager(
                user_working_dir,
                self._username,
                self._size
            ).command_line()
        else:
            _print_error(Errors.WRONG_PASSWORD)


def _print_error(error):
    print('Ошибка:', error.value)
