import sys

def main():
    
    import beebird.task

    beebird.importBuiltinTasks()
    entry = beebird.task.TaskMan.instance().getTaskByName('_sys_entry')()
    return entry.run()

    '''
    import sys
    import argparse;

    print(sys.argv)

    parser = argparse.ArgumentParser(prog="beebird", description="Task management and running platform for python 3")
    parser.add_argument('--command', choices=['help', 'config', 'create', 'run', 'shell', 'top' ], help="command")
    parser.add_argument('--args', type=str)

    r = parser.parse_args(sys.argv[1:])
    return 0
    '''
if __name__ == "__main__": 
    sys.exit(main())