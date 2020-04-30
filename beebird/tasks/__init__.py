
# imports all tasks in this folder
def _importTasks():
    import pkgutil
    import importlib
    import pathlib

    for _, name, _ in pkgutil.iter_modules([pathlib.Path(__file__).parent]):
        importlib.import_module('.'+name, package=__name__)

_importTasks()