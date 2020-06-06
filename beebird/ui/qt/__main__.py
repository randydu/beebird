''' GUI mode '''

import sys

import beebird.utils

#from . import qt


def main(*argv):
    ''' entry of GUI mode '''
    print("GUI >>", *argv)

    beebird.utils.import_builtin_tasks()

    #qt.run(task)


if __name__ == "__main__":
    sys.exit(main())
