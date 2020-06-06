''' CLI mode '''

import sys
import beebird.utils


def main(*argv):
    ''' entry point of bee in CLI mode '''
    print("CLI >>", *argv)

    beebird.utils.import_builtin_tasks()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
