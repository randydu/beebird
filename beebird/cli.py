import sys

def main(*argv):
    from .task import Task
    Task.importAllTasks()

    print("CLI >>", *argv)

    from . import cmd
    cmd.run(gui=False)



if __name__ == "__main__": 
    sys.exit(main(sys.argv))