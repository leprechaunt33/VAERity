# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
# Only import if __main__ to prevent multithreading creating duplicate windows
from multiprocessing import freeze_support

if __name__ == "__main__":
    import datetime
    import math, os, re, code

    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
    if 'USERPROFILE' in os.environ:
        os.environ['KIVY_HOME']=os.environ['APPDATA']
    else:
        os.environ['KIVY_HOME']=os.path.expanduser('~')

    from kivy.config import Config
    Config.read(os.path.join(os.environ['KIVY_HOME'], 'vaerity.ini'))
    freeze_support()
    import pandas as pd
    import vaex as vx
    import numpy as np
    import asyncio
    import matplotlib.pyplot as plt
    import seaborn as sns
    from datetime import datetime

    from virtualcolumns import *
    from helperfunc import *
    from rootwindow import RootWindow

def updatestatus(statustxt):
    global rootspace
    if rootspace.windowstatus is not None:
        rootspace.windowstatus.text=statustxt

def setprogress(num):
    global rootspace
    if rootspace.progress is not None:
        rootspace.progress.value=num

async def runtasks():
    rootspace=RootWindow()
    await asyncio.sleep(0)
    taskoutput = await asyncio.gather(rootspace.base())



if __name__ == "__main__":
    asyncio.run(runtasks())