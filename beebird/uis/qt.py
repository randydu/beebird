""" Qt based TaskUI implementation """

import sys
import threading


from PyQt5.QtWidgets import QMainWindow, QWidget, QProgressBar, QLabel, \
    QTextEdit, QDialog, QDialogButtonBox, QGridLayout, QVBoxLayout
from PyQt5.QtWidgets import QApplication

from beebird.task import Task, TaskMan
from ..ui import TaskUI

#from PyQt5 import QtGui



class _TaskUIQt(TaskUI):
    def __init__(self, task=None):
        super().__init__(task)
        self.timer = None

    def run(self):

        app = QApplication(sys.argv)

        ui_main = QMainWindow()
        task_name = 'dummy'
        ui_main.setWindowTitle(f"QBackup: [{task_name}]")

        task_gauge = QProgressBar(ui_main)

        if self._task.isProgressAvailable():
            task_gauge.setRange(0, 100)
            task_gauge.setValue(0)
        else:
            task_gauge.setRange(0, 0)

        ui_main.setCentralWidget(task_gauge)

        status_bar = ui_main.status_bar()

        ui_main.setGeometry(300, 300, 350, 50)
        ui_main.show()

        self._task.run(wait=False)
        status_bar.showMessage('running...')

        def task_monitor():
            if self._task.isProgressAvailable():
                task_gauge.setValue(self._task.progress*100)

            if self._task.status != Task.Status.DONE:
                self.timer = threading.Timer(1, task_monitor)
                self.timer.start()
            else:
                status_bar.showMessage('done')

        self.timer = threading.Timer(1, task_monitor)
        self.timer.start()

        app.exec_()

    @staticmethod
    def create(obj, fields):
        ''' create a task object with fields '''

        app = QApplication(sys.argv)  # pylint: disable= unused-variable

        dlg = QDialog()
        task_name = type(obj).__name__
        dlg.setWindowTitle(f"QBackup: [{task_name}]")

        # field editor
        layout = QGridLayout()

        j = 0
        for i in fields:
            layout.addWidget(QLabel(i), j, 0)
            # inspect field type and uses appropriate widget
            layout.addWidget(QTextEdit(str(getattr(obj, i))), j, 1)
            j += 1

        ui_fields = QWidget()
        ui_fields.setLayout(layout)

        # dialog layout
        layout = QVBoxLayout()
        layout.addWidget(ui_fields)

        qbtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        btn_box = QDialogButtonBox(qbtn)
        btn_box.accepted.connect(dlg.accept)
        btn_box.rejected.connect(dlg.reject)

        layout.addWidget(btn_box)
        dlg.setLayout(layout)

        dlg.setGeometry(300, 300, 350, 200)
        dlg.exec_()


def run(task):
    ''' run a task '''
    _TaskUIQt(task).run()


def create_task(clsname):
    ''' create a task by name '''

    cls = TaskMan().getTaskByName(clsname)
    obj = cls()

    # both class and object fields are needed to create a task
    fields = obj.getFields()
    #
    _TaskUIQt().create(obj, fields)


def edit_task(task): # pylint: disable=unused-argument
    ''' create a task '''
