
# imports all tasks in this folder
import pathlib

import beebird

beebird.import_tasks(pathlib.Path(__file__).parent, __name__)