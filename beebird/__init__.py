""" Task management and running platform for python 3



"""

import pkgutil
import importlib

from .__main__ import main
__license__ = "MIT"
__author__ = "Randy Du <randydu@gmail.com>"
__version__ = "0.1.0"


def import_tasks(folder, package):
    '''
        imports all tasks under a directory
    '''

    for _, name, _ in pkgutil.iter_modules([folder]):
        importlib.import_module('.'+name, package=package)


def import_builtin_tasks():
    ''' load all beebird's built-in tasks (under {beebird_pkg_dir}/tasks/)

        the tasks/__init__.py will dynamically import all sub-packages
    '''
    from . import tasks # pylint: disable=(unused-import, import-outside-toplevel)
