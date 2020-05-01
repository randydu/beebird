import sys

def main(*argv):
    print("GUI >>", *argv)

    import beebird

    beebird.importBuiltinTasks()
    beebird.cmd.run(gui=True)
    

if __name__ == "__main__": 
    sys.exit(main())