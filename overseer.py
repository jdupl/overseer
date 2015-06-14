import os
from tinytag import TinyTag

def is_new_file(file, old_files):
    # TODO handle relative paths
    return file in old_files

def get_old_files():
    # TODO get actual files from last run
    return []

def get_files(path):
    path_files = []

    for root, sub_folders, files in os.walk(path):
         for file in files:
             path_files.append(file)
    return path_files

def get_lossless_files(files):
    lossless_files = []

    for file in files:
        if file.endswith('.mp3'):
            lossless_files.append(file)
    return lossless_files

def main():
    source = "Téléchargements"
    output = "output"

    old_files = get_old_files()
    source_files = get_lossless_files(get_files(source))

    for file in source_files:
        if is_new_file(file, old_files):
            tags = TinyTag.get(file)
            print(tags.artist)
            print(tags.album)


main()
