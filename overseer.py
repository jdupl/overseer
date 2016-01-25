#!/usr/bin/python3
import os
import re
import sys
import threading
import subprocess
import argparse
import fnmatch
import multiprocessing as mp

from time import sleep
from tinytag import TinyTag
from subprocess import Popen, PIPE
from pyinotify import WatchManager, IN_CLOSE_WRITE, ProcessEvent, Notifier


class Process(ProcessEvent):
    def __init__(self, queue, destination, bitrate):
        self.regex = re.compile('.*\.(?i)flac$')
        self.queue = queue
        self.destination = destination
        self.bitrate = bitrate

    def process_IN_CLOSE_WRITE(self, event):
        target = os.path.join(event.path, event.name)
        if self.regex.match(target):
            new_task = get_encode_task(target, self.destination, self.bitrate)
            if new_task:
                print('Adding new file {} to task queue.'
                      .format(new_task['source']))
                self.queue.put(new_task)


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
        num = int(''.join(i for i in tags.track if i.isdigit()))
        padded_num = "{0:02d}".format(num)
        track_file = padded_num + ' - ' + tags.title.strip()
    else:
        track_file = tags.title.strip()
    return track_file + '.opus'


def get_track_relative_path(tags):
    track_relative_path = None

    track_filename = get_track_filename(tags)
    album_name = tags.album

    if track_filename and album_name:
        safe_path = str.maketrans("", "", "/:?<>\\\"")
        clean_album = tags.album.translate(safe_path)
        clean_track = track_filename.translate(safe_path)
        track_relative_path = os.path.join(clean_album, clean_track)

    return track_relative_path


def get_meta_tags(source):
    output = subprocess.check_output(["metaflac", "--export-tags-to=-", source])
    tags = []
    for line in output.decode("utf8").split("\n"):
        tag = line.split("=", 1)
        if len(tag) == 2:
            tags.append(tag)
    return tags


def encode(task):
    print('Encoding {} at {} kbps.'.format(task['source'], task['bitrate']))
    bitrate = str(task['bitrate'])

    tags_args = []
    for tag, val in get_meta_tags(task['source']):
        tags_args.extend(["--comment", "{}={}".format(tag, val)])

    flac_wav = Popen(['flac', '-scd', task['source']], stdout=PIPE)

    opus_enc_args = ['opusenc']
    opus_enc_args.extend(tags_args)
    opus_enc_args.extend(['--quiet', '--bitrate', bitrate, '-',
                         task['destination']])
    opus_enc = Popen(opus_enc_args, stdin=flac_wav.stdout)
    opus_enc.wait()


def safe_run(queue):
    while True:
        task = queue.get(True)
        try:
            encode(task)
        except Exception as e:
            print("error: {} encoding {}".format(e, task))


def get_files_to_encode(current_source_files, old_files, destination, bitrate):
    new_files = []
    to_encode = []

    for file in current_source_files:
        if is_new_file(file, old_files):
            new_files.append(file)

    for source_file in new_files:
        task = get_encode_task(source_file, destination, bitrate)
        if task:
            to_encode.append(task)

    return to_encode


def get_encode_task(source_file, destination, bitrate):
    tags = TinyTag.get(source_file)
    track_relative_path = get_track_relative_path(tags)

    if track_relative_path:
        track_absolute_path = os.path.join(destination, track_relative_path)
        if not os.path.exists(track_absolute_path):
            return {
                'source': source_file,
                'destination': track_absolute_path,
                'destination_rel': track_relative_path,
                'bitrate': bitrate
            }
    else:
        print('Ignoring ' + source_file)


def prepare_folders(to_encode):
    for encode in to_encode:
        dir_name = os.path.dirname(encode['destination'])
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)


def start_watcher(source, new_files, destination, bitrate):
    wm = WatchManager()
    process = Process(new_files, destination, bitrate)
    notifier = Notifier(wm, process)
    # TODO detect files moving from a dir to another
    wm.add_watch(source, IN_CLOSE_WRITE, rec=True)
    try:
        while True:
            notifier.process_events()
            if notifier.check_events():
                notifier.read_events()
    except KeyboardInterrupt:
        notifier.stop()


def main(argv):
    description = 'Syncs a flac library to an opus copy'
    info_text = 'Depends on opusenc, flac'
    parser = argparse.ArgumentParser(description=description, epilog=info_text)
    parser.add_argument('source', help='the source of the flac files')
    parser.add_argument('destination', help='the destination of the opus files')
    parser.add_argument('--threads', '-t', type=int,
                        help='the number of threads to use')
    parser.add_argument('--bitrate', '-b', type=int, default=64,
                        help='\
    the opus bitrate to use in kbps (default: 64kbps)')

    args = parser.parse_args()
    source = args.source
    destination = args.destination
    bitrate = args.bitrate
    threads = args.threads
    queue = mp.Queue()

    # start watching files
    t = threading.Thread(target=start_watcher, args=(source, queue,
                                                     destination, bitrate))
    t.daemon = True
    t.start()

    print('comparing source and destination')
    old_files = get_old_files()

    # Feel free to implement more
    output_files = get_files(destination, 'opus')
    current_source_files = get_files(source, 'flac')

    print('preparing to encode')
    to_encode = get_files_to_encode(current_source_files, old_files,
                                    destination, bitrate)
    prepare_folders(to_encode)

    print('encoding {} files'.format(len(to_encode)))
    pool = mp.Pool(threads, safe_run, (queue,))

    # start encoding
    for encode in to_encode:
        queue.put(encode)

    # wait forever
    pool.close()
    pool.join()


if __name__ == "__main__":
    main(sys.argv)
