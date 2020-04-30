import sys

def main(*argv):
    print("GUI >>", *argv)

    # loads all plugin tasks under the "./tasks" folder
    from .task import Task
    Task.importAllTasks()

    from . import cmd
    cmd.run(gui=True)
    

if __name__ == "__main__": 
    sys.exit(main())