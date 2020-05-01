
# imports all tasks in this folder
import pathlib

import beebird

beebird.importTasks(pathlib.Path(__file__).parent, __name__)