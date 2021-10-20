import filemanager
from users_storage import JSONUsersStorage


def _main():
    fm = filemanager.MultiUserFileManager(
        JSONUsersStorage('users.json'),
        size=20
    ).export_settings()
    fm.auth()
    fm.start()


if __name__ == '__main__':
    _main()
