from beebird.task import task,Task

@task
def file(filename:str):
    ''' run a task file '''
    try:
        tsk = Task.loadFromFile(filename)
        return tsk.run()
    except Exception as ex:
        print(ex)




