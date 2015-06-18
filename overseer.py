import sys, getopt, os

import subprocess
from tinytag import TinyTag
import multiprocessing as mp

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

def get_track_filename(tags):
    track_number = ' '
    if not tags.title:
        return None
    if tags.track:
        track_file = "{0:02d}".format(int(tags.track)) + ' - ' + tags.title
    else:
        track_file = tags.title
    return track_file + '.opus'

def get_track_relative_path(tags):
    track_relative_path = None

    track_filename = get_track_filename(tags)
    album_name = tags.album

    if track_filename and album_name:
        track_relative_path = tags.album + '/' + track_filename

    return track_relative_path

def encode(encode):
    subprocess.check_call(['flac', '-scd', encode['source'], '|', 'opusenc',
        '--bitrate', '64', '-', encode['destination']])

def safe_run(*args, **kwargs):
    try:
        encode(*args, **kwargs)
    except Exception as e:
        print("error: %s encode(*%r, **%r)" % (e, args, kwargs))

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
    new_files = []
    old_files = get_old_files()

    output_files = get_files(destination, 'opus')
    current_source_files = get_files(source, 'flac')

    for file in current_source_files:
        if is_new_file(file, old_files):
            new_files.append(file)

    for source_file in new_files:
        tags = TinyTag.get(source_file)
        track_relative_path = get_track_relative_path(tags)
        track_absolute_path = destination + '/' + track_relative_path

        if track_relative_path and not os.path.exists(track_absolute_path):
            to_encode.append({
                'source': source_file,
                'destination': track_absolute_path,
                'tags': tags
            })
        else:
            print('Ignoring ' + source_file)

    print('preparing encodings')
    for encode in to_encode:
        dir_name = os.path.dirname(encode['destination'])

        if not os.path.isdir(dir_name):
            os.makedirs(dir_name)

    print('encoding files')
    pool = mp.Pool()
    pool.map(safe_run, to_encode)


if __name__ == "__main__":
   main(sys.argv[1:])
