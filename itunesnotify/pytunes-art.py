#!/usr/bin/env python
import subprocess
import gntp.notifier
import time
import os
import sys

from mutagen.mp3 import MP3
from threading import Thread
from functools import wraps
from PIL import Image


def async(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        thr = Thread(target=f, args=args, kwargs=kwargs)
        thr.start()
    return wrapper


class Song(object):
    pass


class ItunesNotify(object):

    def __init__(self):
        #create growl instance
        self.itunes_growl = self._init_growl()
        #register with relevant information
        self.itunes_growl.register()
        self.previous_song = ''

    def run(self):
        '''
        fpid = os.fork()
        if fpid != 0:
            sys.exit(0)
        '''
        while True:
            if self._itunes_status() == 'playing':
                print 'notifying'
                self._notify_current_song()
            time.sleep(1)

    def _notify_current_song(self):
        song, artist, album = self._song_details()
        path = self._song_path()
        album_art = self._album_art(path)
        print 'resizing image'
        album_icon = self._resize_image(album_art)
        print 'image resized'
        if self.previous_song != song:
            print 'attempting to notify'
            self.itunes_growl.notify(
                noteType="Current Song",
                title=song,
                description='by %s from %s' % (artist, album),
                icon=album_icon)
            self.previous_song = song

    @staticmethod
    def _itunes_status():
        """ returns current status of itunes """
        return subprocess.check_output(["osascript", "-e", 'tell application "iTunes"'
                                        'to player state as string']).strip()

    @staticmethod
    def _song_details():
        """ returns name, artist, and album of
        the current song currenly playing """
        return subprocess.check_output(["osascript", "-e", 'tell application "iTunes"'
                                       'to name of current track'
                                       '&"#"& artist of current track'
                                       '&"#"& album of current track as string']).strip().split('#')

    @staticmethod
    def _song_path():
        """ returns path of current song """
        normalize_path = lambda x: x.lstrip('alias').replace(':', '/')
        path = subprocess.check_output(["osascript", "-e", 'tell application "iTunes"'
                                        'to get location of current track']).strip()

        clean_path = normalize_path(path)
        #trim hard drive name from path
        return clean_path[clean_path.find('/'):]

    @staticmethod
    def _album_art(song_path):
        """ returns raw data of album art of current song """
        song = MP3(song_path)
        art = (song.get('APIC:') or song.get('APIC:Front cover'))
        art_data = art.data if art is not None else None
        if art_data is not None:
            print 'trying to send some art'
        return art_data

    @staticmethod
    def _resize_image(image_data):
        if image_data is not None:
            size = (32, 32)
            image = Image.fromstring('I', size, image_data)
            #raw data from gntp
            return image.tostring()

    @staticmethod
    def _init_growl():
        """ initilizes a growl instance """
        return gntp.notifier.GrowlNotifier(
            applicationName="iTunes",
            notifications=["Current Song"],
            defaultNotifications=["Current Song"])


if __name__ == '__main__':
    itunes_growl = ItunesNotify()
    itunes_growl.run()
