from beebird.task import task

@task
def _sys_entry():
    import sys
    import argparse;

    print(sys.argv)

    parser = argparse.ArgumentParser(prog="beebird", description="Task management and running platform for python 3")
    
    # disable argparser's default sys.exit() behavior since we are running in a thread.
    parser.exit = lambda *args: 0

    parser.add_argument('--command', choices=['help', 'config', 'create', 'run', 'shell', 'top' ], help="command")
    parser.add_argument('--args', type=str)

    #r = parser.parse_args("--command create".split())
    r = parser.parse_args(sys.argv[1:])

    if r.command == 'help':
        parser.print_help()


