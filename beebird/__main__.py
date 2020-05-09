import sys
import argparse

import beebird
import beebird.task

def main():
    
    beebird.importBuiltinTasks()

    print(sys.argv)

    parser = argparse.ArgumentParser(prog="beebird", description="Task management and running platform for python 3")
    
    # disable argparser's default sys.exit() behavior since we are running in a thread.
    #parser.exit = lambda *args: 0

    parser.add_argument('--version', action="version", version = f"beebird v{beebird.__version__}")

    subparsers = parser.add_subparsers(help='sub-command help')
    
    parser_run = subparsers.add_parser('run', help='execute task')
    subparsers_run = parser_run.add_subparsers(help='registered tasks')
    # adds all registered tasks
    tasks = beebird.task.TaskMan.instance().getAllTasks()
    for task in tasks:
        parser_task = subparsers_run.add_parser(task.__name__, help=f"task {task.__name__}'s help")

        o = task()
        fields = task.getFields()
        for field in fields:
            v = getattr(o, field)
            parser_task.add_argument(f"--{field}", type=type(v), help="yyy")

        def call_task(args):
            o = task()
            for field in fields:
                setattr(o, field, getattr(args, field))
            o.run()
            print(o.result)

        parser_task.set_defaults(func=call_task)

    parser_create = subparsers.add_parser('create', help='create a task')

    parser_config = subparsers.add_parser('config', help='configuration beebird')

    parser_shell = subparsers.add_parser('shell', help='run task in a shell')


    #r = parser.parse_args("--command create".split())
    args = parser.parse_args(sys.argv[1:])
    print(args)
    if hasattr(args, 'func'):
        args.func(args)


if __name__ == "__main__": 
    sys.exit(main())