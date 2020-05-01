import sys

def main(*argv):
    print("CLI >>", *argv)

    import beebird

    beebird.importBuiltinTasks()
    beebird.cmd.run(gui=False)



if __name__ == "__main__": 
    sys.exit(main(sys.argv))