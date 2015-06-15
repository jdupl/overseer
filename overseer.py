import sys, getopt, os
from tinytag import TinyTag

def is_new_file(file, old_files):
    # TODO handle relative paths
    return file not in old_files

def get_old_files():
    # TODO get actual files from last run
    return []

def get_files(path, extension):
    path_files = []

    for root, sub_folders, files in os.walk(path):
         for file in files:
            if not extension or file.endswith('.' + extension):
                 path_files.append(root + '/' + file)
    return path_files

def help():
    print('overseer.py -s <source> -d <destination>')


def main(argv):
    source = None
    destination = None
    try:
        opts, args = getopt.getopt(argv, "hs:d:",["source=","destination="])
    except getopt.GetoptError:
        help()
        sys.exit(1)
    for opt, arg in opts:
        if opt == '-h':
            help()
            sys.exit(0)
        elif opt in ("-s", "--source"):
            source = arg
        elif opt in ("-d", "--destination"):
            destination = arg

    if not destination or not source:
        help()
        sys.exit(1)

    to_encode = []
    old_files = get_old_files()
    output_files = get_files(destination, 'opus')
    source_files = get_files(source, 'flac')

    for file in source_files:
        if is_new_file(file, old_files):
            to_encode.append(file)

    for file in to_encode:
        tags = TinyTag.get(file)
        album_name = tags.album
        # TODO pad with 0 for 2 length
        track_file = tags.track + ' - ' + tags.title
        track_relative_path = tags.album + '/' + track_name
        track_absolute_path = output + '/' + track_relative_path


if __name__ == "__main__":
   main(sys.argv[1:])
