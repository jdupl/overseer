#!/usr/bin/python3
import sys, getopt, os, argparse
import multiprocessing as mp

from subprocess import Popen, PIPE
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

def get_track_filename(tags):
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

def encode(to_encode):
    bitrate = str(to_encode['bitrate'])
    tags = to_encode['tags']

    flac_wav = Popen(['flac', '-scd', to_encode['source']], stdout=PIPE)
    opus_enc = Popen(['opusenc', '--quiet', '--bitrate', bitrate, '-',
        to_encode['destination']], stdin=flac_wav.stdout)
    opus_enc.wait()

    # TODO set genre
    tagging = Popen(['id3v2', '-a', tags['artist'], '-t', tags['title'], '-y',
        tags['year'], '-T', tags['track'], to_encode['destination']])
    tagging.wait()


def safe_run(*args, **kwargs):
    try:
        encode(*args, **kwargs)
    except Exception as e:
        print("error: %s encode(*%r, **%r)" % (e, args, kwargs))

def get_files_to_encode(current_source_files, old_files, destination, bitrate):
    new_files = []
    to_encode = []

    for file in current_source_files:
        if is_new_file(file, old_files):
            new_files.append(file)

    for source_file in new_files:
        tags = TinyTag.get(source_file)
        track_relative_path = get_track_relative_path(tags)
        track_absolute_path = destination + '/' + track_relative_path

        if track_relative_path and not os.path.exists(track_absolute_path):
            tags_dict = dict((k, v)
                    for k, v in tags.__dict__.items() if not k.startswith('_'))
            to_encode.append({
                'source': source_file,
                'destination': track_absolute_path,
                'tags': tags_dict,
                'bitrate': bitrate
            })
        else:
            print('Ignoring ' + source_file)
    return to_encode

def prepare_folders(to_encode):
    for encode in to_encode:
        dir_name = os.path.dirname(encode['destination'])

        if not os.path.isdir(dir_name):
            os.makedirs(dir_name)

def main(argv):
    description = 'Syncs a flac library to an opus copy'
    info_text = 'Depends on opusenc, flac'
    parser = argparse.ArgumentParser(description=description, epilog=info_text)
    parser.add_argument('source', help='the source of the flac files')
    parser.add_argument('destination', help='the destination of the opus files')
    parser.add_argument('--threads', '-t', type=int,
        help='the number of threads to use')
    parser.add_argument('--bitrate', '-b', type=int, default=64,
        help='the opus bitrate to use in kbps (default: 64kbps)')

    args = parser.parse_args()
    source = args.source
    destination = args.destination
    bitrate = args.bitrate
    threads = args.threads

    print('comparing source and destination')
    old_files = get_old_files()
    output_files = get_files(destination, 'opus')
    current_source_files = get_files(source, 'flac')

    print('preparing to encode')
    to_encode = get_files_to_encode(current_source_files, old_files,
        destination, bitrate)
    prepare_folders(to_encode)

    print('encoding {} files'.format(len(to_encode)))
    pool = mp.Pool(threads)
    pool.map(safe_run, to_encode)


if __name__ == "__main__":
   main(sys.argv)
