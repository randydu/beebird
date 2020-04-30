from .task import Task


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
