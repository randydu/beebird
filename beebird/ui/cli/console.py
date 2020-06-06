
""" Console based TaskUI implementation """


import threading

from beebird.ui import TaskUI

from beebird.task import Task

# Print iterations progress


# pylint: disable=too-many-arguments
def print_progress_bar(iteration, total, prefix='', suffix='', decimals=1,
                       length=100, fill='█', print_end="\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent
                                  complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        print_end    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 *
                                                     (iteration / float(total)))
    filled_length = int(length * iteration // total)
    pbar = fill * filled_length + '-' * (length - filled_length)
    print('\r%s |%s| %s%% %s' % (prefix, pbar, percent, suffix), end=print_end)
    # Print New Line on Complete
    if iteration == total:
        print()


class _TaskUIConsole(TaskUI):
    def __init__(self, task):
        super().__init__(task)
        self.timer = None

    def update(self):
        ''' update process ui '''
        task_name = 'task'
        print_progress_bar(self._task.progress*100, 100, prefix=task_name)

    def run(self):
        ''' start running task in console mode '''

        lck = threading.Lock()
        lck.acquire()

        self._task.run(wait=False)

        self.update()

        def task_monitor():
            self.update()
            if self._task.status != Task.Status.DONE:
                self.timer = threading.Timer(1, task_monitor)
                self.timer.start()
            else:
                print('\ndone')
                lck.release()

        self.timer = threading.Timer(1, task_monitor)
        self.timer.start()

        # wait until the task_monitor() has updated the done status.
        lck.acquire()

        print('\ngame over!')


def run(task):
    ''' run a task in console '''
    _TaskUIConsole(task).run()
