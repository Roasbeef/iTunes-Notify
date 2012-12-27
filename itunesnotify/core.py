#!/usr/bin/env python
import subprocess
import os
import sys
import re

from threading import Thread
from functools import wraps
from collections import namedtuple
from Queue import Queue
from time import sleep
from gntp.notifier import GrowlNotifier


__version__ = (0, 0, 1, 1)
PID_PATH = os.path.join(os.path.dirname(__file__), "pid.txt")


def async(f):
    """ Decorator to execute function in new thread """
    @wraps(f)
    def wrapper(*args, **kwargs):
        thr = Thread(target=f, args=args, kwargs=kwargs)
        thr.start()
    return wrapper


def begin_notifications():
    """ Start iTunes-Notify
    """
    notify = iTunesNotifier()
    notify.run()


def end_notifications():
    """ Stop iTunes-Notify if one is running
        otherwise exits with a message
    """
    with open(PID_PATH, 'r+') as f:
        pid = f.read()
        #blank file so program not running
        if not pid:
            print 'iTunes-Notify is not currently running'
            sys.exit(0)
        #kill process
        subprocess.call(["kill", "-9", "%s" % pid])
        print 'iTunes-Notify successfully stopped'

    #blank out file for future use
    open(PID_PATH, 'w').close()


class iTunes(object):

    @staticmethod
    def is_open():
        """ Returns true if there is an iTunes (not the pesky iTunes helper)
            process running, false otherwise
        """
        ps_cmd = ["ps", "axo", "pid,command"]
        p = subprocess.Popen(ps_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        processes = p.communicate()[0]
        if re.search(r'(/Applications/iTunes.app/Contents/MacOS/iTunes\s[^/]*)', processes):
            return True
        return False

    @staticmethod
    def current_status():
        """ Returns current status of itunes """
        return subprocess.check_output(["osascript", "-e", 'tell application "iTunes"'
                                        'to player state as string']).strip()

    @staticmethod
    def current_song_details():
        """ Returns name, artist, and album of
            the current song currenly playing
        """
        return subprocess.check_output(["osascript", "-e", 'tell application "iTunes"'
                                       'to name of current track'
                                       '&"#"& artist of current track'
                                       '&"#"& album of current track as string']).strip().split('#')


class iTunesNotifier(GrowlNotifier):

    def __init__(self):
        #create growl instance
        GrowlNotifier.__init__(self,
                               applicationName="iTunes",
                               notifications=["Current Song"],
                               defaultNotifications=["Current Song"])

        #register growl app with relevant information
        self.register()
        self.song_queue = Queue()
        self.iTunes = iTunes()

    def run(self):
        if self._already_running:
            print 'iTunes-Notify is already running'
            sys.exit(0)

        print 'iTunes-Notify is now running.'
        print 'Run "itunes-notify stop" to stop the notifications'
        #deatch from tty to enable script to run beyond current terminal
        #http://stackoverflow.com/a/1603152/988919
        fpid = os.fork()
        if fpid != 0:
            self._write_pid(fpid)
            sys.exit(0)
        self._feed_songs()
        self._grab_songs()

    @property
    def _already_running(self):
        with open(PID_PATH, 'r') as f:
            pid = f.read()
            return pid != ' ' and pid != ''

    def _write_pid(self, pid):
        """ Writes process pid to file for stopping execution later """
        with open(PID_PATH, 'w') as f:
            f.write(str(pid))

    @async
    def _feed_songs(self):
        """ Creates worker thread to feed songs
            into the song_queue
        """
        Song = namedtuple('Song', 'name artist album')
        previous_song = set(' ')
        while True:
            # TODO: Find a better way handling this
            try:
                if self.iTunes.is_open() and self.iTunes.current_status() == 'playing':
                    song, artist, album = self.iTunes.current_song_details()
                    # don't notify of the same song more than once
                    if song not in previous_song:
                        previous_song.pop()
                        previous_song.add(song)
                        s = Song(song, artist, album)
                        self.song_queue.put(s)
            except:  # iTunes might be open/closed for a split second and cause an error
                pass

            sleep(0.5)

    def _grab_songs(self):
        """ Grab songs from the song_queue
            and send the notification
        """
        while True:
            if not self.song_queue.empty():
                song = self.song_queue.get()
                self.notify(
                    noteType="Current Song",
                    title=song.name,
                    description='by %s from %s' % (song.artist, song.album))

            sleep(0.5)
