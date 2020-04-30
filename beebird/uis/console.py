
""" Console based TaskUI implementation """


from ..ui import TaskUI

from ..task import Task

# Print iterations progress
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = printEnd)
    # Print New Line on Complete
    if iteration == total: 
        print()

class _TaskUIConsole(TaskUI):
    def __init__(self, task):
        super().__init__(task)
    
    def update(self):
        taskName = 'task'
        printProgressBar(self._task.progress*100, 100, prefix=taskName)

    def run(self):
        import threading

        self._task.run(wait = False)

        self.update()

        def task_monitor():
            self.update()
            if self._task.status != Task.Status.DONE:
                self.timer = threading.Timer(1, task_monitor)
                self.timer.start()
            else:
                print('\ndone')

        self.timer = threading.Timer(1, task_monitor)
        self.timer.start()


def run(task):
    _TaskUIConsole(task).run()