from .task import Task

from py_singleton import singleton

# Private 

class Category(object):
    def __init__(self, name):
        self.name = name

class Cmd(object):
    clsTask = None

    name: str = ""  # cmd name
    category: Category = None
    description = ""
    hidden = False
    system = False

@singleton
class CmdMan(object):
    def __init__(self):
        self.cmds = {} #  name => cmd mapping
        self.categories = {} # name => category mapping


# public

def registerCmd(cmd):
    ''' registers cmd from tasks '''
    print(f"registering {cmd}\r\n")


def run(gui = True):
    jstr = '{ "_clsid_":"DummyTask" }'
    task = Task.from_json(jstr)

    if gui:
        from .uis import qt
        qt.run(task)
    else:
        from .uis import console
        console.run(task)
