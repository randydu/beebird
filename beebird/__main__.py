''' module entry '''

import sys
import argparse

import beebird
import beebird.task
import beebird.decorators
import beebird.utils


def main():
    ''' entrypoint of beebird console '''
    beebird.utils.import_builtin_tasks()

    # print(sys.argv)

    parser = argparse.ArgumentParser(
        prog="beebird", description="Task management and running platform for python 3")

    # disable argparser's default sys.exit() behavior since we are running in a thread.
    #parser.exit = lambda *args: 0

    parser.add_argument('--version', action="version",
                        version=f"beebird v{beebird.__version__}")

    subparsers = parser.add_subparsers(help='sub-command help')

    parser_run = subparsers.add_parser('run', help='execute task')
    subparsers_run = parser_run.add_subparsers(help='registered tasks')
    # adds all registered tasks
    tasks = beebird.task.TaskMan().all()
    for task in tasks:
        parser_task = subparsers_run.add_parser(
            task.__name__, help=task.__doc__)

        tsk = task()
        fields = tsk.get_fields()
        for field in fields:
            val = getattr(tsk, field)
            if isinstance(val, beebird.decorators.Empty):
                # no default value
                if val.annotation:
                    parser_task.add_argument(
                        field, type=val.annotation, help="yyy")
                else:
                    parser_task.add_argument(field, help="yyy")
            else:
                # has default value
                parser_task.add_argument(
                    f"--{field}", type=type(val), default=val, help="yyy")

        def wrap_func(tsk, fields):
            def call_task(args):
                tsk_ = tsk()
                for field in fields:
                    setattr(tsk_, field, getattr(args, field))
                print("Result >> ", tsk_.run())
            return call_task

        parser_task.set_defaults(func=wrap_func(task, fields))

    subparsers.add_parser('create', help='create a task')

    subparsers.add_parser(
        'config', help='configuration beebird')

    subparsers.add_parser('shell', help='run task in a shell')

    #r = parser.parse_args("--command create".split())
    args = parser.parse_args(sys.argv[1:])
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    sys.exit(main())
