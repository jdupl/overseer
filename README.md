# overseer

Syncs a flac library to an opus clone
* file watcher for instant encoding
* encodes on multiple threads

Tested on Linux only.

## Installation
The file `overseer.py` can be downloaded [here](https://github.com/jdupl/overseer/blob/master/overseer.py).

### Requirements

* Python 3.x
* opusenc
* id3v2
* flac
* TinyTag python library
* pyinotify python library

#### Archlinux

`sudo pacman -S flac opus-tools id3v2 python-pip`

`sudo pip install tinytag pyinotify`

#### Debian/Ubuntu

`sudo apt-get install flac opus-tools id3v2 python3-pip`

`sudo pip3 install tinytag pyinotify`

## Usage

Sync a FLAC library to an opus folder.

Usage is trivial, please take a look at the help with

`./overseer.py -h`

Run as a background process with screen or tmux. I will implement a forking process with init script when the code is finished.
