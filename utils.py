import os


def dir_size(path):
    size = 0
    for path, dirs, files in os.walk(path):
        for file in files:
            file_path = os.path.join(path, file)
            size += file_size(file_path)
    return size


def str_size(string):
    return len(string.encode())


def file_size(path):
    return os.path.getsize(path)