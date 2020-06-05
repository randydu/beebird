''' GUI mode '''

import sys

import beebird

def main(*argv):
    ''' entry of GUI mode '''
    print("GUI >>", *argv)

    beebird.import_builtin_tasks()
    beebird.task.run(gui=True)


if __name__ == "__main__":
    sys.exit(main())
