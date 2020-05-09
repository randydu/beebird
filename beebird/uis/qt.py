""" Qt based TaskUI implementation """


from beebird.task import Task, TaskMan

from ..ui import TaskUI

from PyQt5 import QtGui

from PyQt5.QtWidgets import QMainWindow, QWidget, QProgressBar, QLabel, QTextEdit,QDialog, QDialogButtonBox, QGridLayout, QVBoxLayout
from PyQt5.QtWidgets import QApplication

class _TaskUIQt(TaskUI):
    def __init__(self, task = None):
        super().__init__(task)

    def run(self):
        import sys
        import threading

        app = QApplication(sys.argv)

        uiMain = QMainWindow()
        taskName = 'dummy'
        uiMain.setWindowTitle(f"QBackup: [{taskName}]")

        taskGauge = QProgressBar(uiMain)

        if self._task.isProgressAvailable():
            taskGauge.setRange(0,100)
            taskGauge.setValue(0)
        else:
            taskGauge.setRange(0,0)

        uiMain.setCentralWidget(taskGauge)        

        statusBar = uiMain.statusBar()

        uiMain.setGeometry(300, 300, 350, 50)
        uiMain.show()

        self._task.run(wait = False)
        statusBar.showMessage('running...')

        def task_monitor():
            if self._task.isProgressAvailable():
                taskGauge.setValue(self._task.progress*100)

            if self._task.status != Task.Status.DONE:
                self.timer = threading.Timer(1, task_monitor)
                self.timer.start()
            else:
                statusBar.showMessage('done')

        self.timer = threading.Timer(1, task_monitor)
        self.timer.start()

        app.exec_()

    def create(self, obj, fields):
        ''' create a task object with fields '''
        import sys

        app = QApplication(sys.argv) # pylint: disable= unused-variable

        dlg = QDialog()
        taskName = type(obj).__name__
        dlg.setWindowTitle(f"QBackup: [{taskName}]")

        # field editor
        layout = QGridLayout()

        j = 0
        for i in fields:
            layout.addWidget(QLabel(i), j,0)
            # TODO: inspect field type and uses appropriate widget
            layout.addWidget(QTextEdit(str(getattr(obj, i))), j,1)
            j += 1


        uiFields = QWidget()
        uiFields.setLayout(layout)

        # dialog layout
        layout = QVBoxLayout()
        layout.addWidget(uiFields)

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        buttonBox = QDialogButtonBox(QBtn)
        buttonBox.accepted.connect(dlg.accept)
        buttonBox.rejected.connect(dlg.reject)

        layout.addWidget(buttonBox)
        dlg.setLayout(layout)

        dlg.setGeometry(300, 300, 350, 200)
        dlg.exec_()



def run(task):
    ''' run a task '''
    _TaskUIQt(task).run()

def createTask(clsname):
    ''' create a task by name '''
    import py_json_serialize

    clsTask = TaskMan.instance().getTaskByName(clsname)
    obj = clsTask()

    # both class and object fields are needed to create a task
    fields = obj.getFields()
    # 
    _TaskUIQt().create(obj, fields)


def editTask(task):
    ''' create a task '''
    pass