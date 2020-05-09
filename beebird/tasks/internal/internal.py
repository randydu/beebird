from beebird.task import task,Task

@task
def file(filename:str):
    ''' run a task file '''
    try:
        tsk = Task.loadFromFile(filename)
        tsk.run()
        print("Result >> ", tsk.result)
    except Exception as ex:
        print(ex)




