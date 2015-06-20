# overseer

syncs a flac library to an opus library

Tested on Linux only.

## Installation
The file `overseer.py` can be downloaded [here](https://github.com/jdupl/overseer/blob/master/overseer.py).

### Requirements

* Python 3.x
* opusenc
* id3v2
* flac
* TinyTag python library

#### Archlinux

`sudo pacman -S flac opusenc id3v2 python-pip && sudo pip install tinytag`

#### Debian/Ubuntu

`sudo apt-get install flac opusenc id3v2 python3-pip && sudo pip3 install tinytag`

## Usage

Sync a FLAC library to an opus folder.

Usage is trivial, please take a look at the help with

`./overseer.py -h`
