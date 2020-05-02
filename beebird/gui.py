import sys

def main(*argv):
    print("GUI >>", *argv)

    import beebird

    beebird.importBuiltinTasks()
    beebird.task.run(gui=True)
    

if __name__ == "__main__": 
    sys.exit(main())