#!/usr/bin/env python
import subprocess
import os
import sys
import re
import pykka

from collections import namedtuple
from gntp.notifier import GrowlNotifier


__version__ = (0, 0, 1, 0)
PID_PATH = os.path.join(os.path.dirname(__file__), "pid.txt")


def write_pid(pid):
    """ Writes process pid to file for stopping execution later """
    with open(PID_PATH, 'w+') as f:
        f.write(str(pid))


def already_running():
    """ Return true if an instance of iTunes-Notify is currently running """
    with open(PID_PATH, 'r') as f:
        pid = f.read()
        return pid != ' ' and pid != ''


def begin_notifications():
    """ Start iTunes-Notify, unless an instance is currently running """
    if already_running():
        print 'iTunes-Notify is already running'
        sys.exit(0)

    fpid = os.fork()
    # daemonize
    if fpid != 0:
        write_pid(fpid)
        sys.exit(0)

    notifier = iTunesNotifierActor.start().proxy()
    listener = iTunesListenerActor.start(notifier).proxy()


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
    pykka_traversable = True

    @staticmethod
    def is_open():
        """ Returns true if there is an iTunes (not the pesky iTunes helper)
            process running, false otherwise
        """
        ps_cmd = ["ps", "axo", "pid,command"]
        p = subprocess.Popen(ps_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        processes = p.communicate()[0]
        return re.search(r'(/Applications/iTunes.app/Contents/MacOS/iTunes\s[^/]*)', processes)

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


class iTunesListenerActor(pykka.gevent.GeventActor):
    def __init__(self, notifier):
        super(iTunesListenerActor, self).__init__()
        self.notifier = notifier
        self.itunes = iTunes()
        self.last_track_title = ''
        self.new_track = namedtuple('Track', 'title artist album')

    def listen(self, message):
        # TODO: Find a better way handling this
        while True:
            try:
                if self.itunes.is_open() and self.itunes.current_status() == 'playing':
                    title, artist, album = self.iTunes.current_song_details()
                    # don't reply with the song sent last
                    if title.get() != self.last_track_title:
                        s = self.new_track(title.get(), artist.get(), album.get())
                        # send the new song over to the notifier actor
                        self.notifier.tell({'new_track': s})
            except:  # iTunes might be open/closed for a split second and cause an error
                pass


class iTunesNotifierActor(pykka.gevent.GeventActor, GrowlNotifier):
    def __init__(self):
        # register growl app with relevant information
        super(iTunesNotifierActor, self).__init__(applicationName="iTunes",
                                                  notifications=["Current Song"],
                                                  defaultNotifications=["Current Song"])
        self.register()
        # initialize actor
        super(iTunesNotifierActor, self).__init__()

    def on_receive(self, message):
        track = message['new_track']
        self.notify(noteType="Current Track", title=track.name,
                    description='by {} from {}'.format(track.artist, track.album))

    def on_start(self):
        print 'iTunes-Notify is now running.'
        print 'Run "itunes-notify stop" to stop the notifications'
