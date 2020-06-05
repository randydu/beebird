''' CLI mode '''

import sys
import beebird


def main(*argv):
    ''' entry point of bee in CLI mode '''
    print("CLI >>", *argv)

    beebird.import_builtin_tasks()
    beebird.task.run(gui=False)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
