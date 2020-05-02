
__license__ = "MIT"
__author__ = "Randy Du <randydu@gmail.com>"
__version__ = "0.0.1"

def importTasks(dir, package):
    '''
        imports all tasks under a directory
    '''
    import pkgutil
    import importlib

    for _, name, _ in pkgutil.iter_modules([dir]):
        importlib.import_module('.'+name, package=package)


def importBuiltinTasks():
    ''' load all beebird's built-in tasks (under {beebird_pkg_dir}/tasks/) 

        the tasks/__init__.py will dynamically import all sub-packages
    '''
    from . import tasks