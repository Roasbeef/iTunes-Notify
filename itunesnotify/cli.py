"""iTunes-Notify.

Usage:
  itunes-notify run
  itunes-notify stop

Options:
  -h --help  Show this screen
  --version  Show current version


"""
from docopt import docopt
from .core import (begin_notifications, end_notifications, __version__)


def begin():
    release_version = ".".join(str(x) for x in __version__)
    arguments = docopt(__doc__, help=True, version='iTunes-Notify %s' % release_version)
    if arguments.get('run'):
        begin_notifications()
    elif arguments.get('stop'):
        end_notifications()
    else:
        print __doc__

if __name__ == '__main__':
    begin()
