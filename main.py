# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
# Only import if __main__ to prevent multithreading creating duplicate windows
if __name__ == "__main__":
    import datetime
    import math, os, re, code
    import readline
    import rlcompleter

    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
    import pandas as pd
    import vaex as vx
    import numpy as np
    import asyncio
    import matplotlib.pyplot as plt
    import seaborn as sns
    from datetime import datetime
    import pyreadline as prl

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

async def main():
    updatestatus("Starting import of data...")
    dfdata = vaershandle('DATA')

    setprogress(10)
    updatestatus("Dataframe length: {len(dfdata)}\nColumns: {dfdata.column_names}")
    await asyncio.sleep(0)

    dfsymptoms=vaershandle('symptoms')
    setprogress(20)
    updatestatus("SYMPTOMS frame loaded")
    await asyncio.sleep(0)
    dfvax=vaershandle('vax')

    setprogress(30)
    updatestatus("VAX frame loaded")
    await asyncio.sleep(0)

    seenv = dict()

    def seenid(x):
        if x in seenv:
            return False
        else:
            seenv[x] = 1
            return True

    updatestatus("Getting unique ids from VAERSVAX table")
    setprogress(40)
    await asyncio.sleep(0)

    vaxdf2 = dfvax[dfvax.apply(seenid, arguments=[dfvax.VAERS_ID])]

    updatestatus("Joining with VAERSDATA table")
    setprogress(50)
    await asyncio.sleep(0)

    dfdata = dfdata.join(vaxdf2, on='VAERS_ID', how='left', allow_duplication=True)

    updatestatus(f"Dataframe length after join with vax table: {len(dfdata)}")
    setprogress(60)

    hosp=len(dfdata[dfdata.HOSPITAL == 'Y'])
    hospcovid=len(dfdata[(dfdata.HOSPITAL == 'Y') & ((dfdata.VAX_TYPE == 'COVID19') | (dfdata.VAX_TYPE.str.len() < 1)) ])
    deaths=len(dfdata[dfdata.DIED == 'Y'])
    deathscovid=len(dfdata[(dfdata.DIED == 'Y') & ((dfdata.VAX_TYPE == 'COVID19') | (dfdata.VAX_TYPE.str.len() < 1)) ])
    print(f"{deaths} deaths, {deathscovid} COVID related")
    print(f'{hosp} hospitalizations, {hospcovid} COVID related')

    print(f'Concatenated symptoms frame is {len(dfsymptoms)} records')
    print(f'Concatenated vax frame is {len(dfvax)} records')
    print("Adding virtual columns to group dates and ages")
    dfdata['pdate'] = dfdata.RECVDATE.apply(parse_datetime)
    dfdata['ydate'] = dfdata.RECVDATE.apply(year_datetime)
    dfdata['age_bin'] = dfdata.AGE_YRS.apply(age_bin)

    while True:
        print("Pick a report, or Q to quit.")
        print("1. Vaccinations by month and sex, stack plot.")
        print("2. Hospitalisations and deaths by age group, filtered by year.")
        print("3. List most words in symptom text")
        print("4. Filter symptom text by common word")
        print("5. 2D histogram over age and days since vaccination")
        print("6. Interactive Python shell")
        action=input("--> ")
        if action == 'Q':
            dfdata.close()
            dfsymptoms.close()
            dfvax.close()
            exit()
        elif action == '1':
            bymonthandsex(dfdata)
        elif action == '2':
            piecharts1(dfdata)
        elif action == '3':
            symptoms(dfsymptoms)
        elif action == '4':
            filtersymptoms(dfsymptoms)
        elif action == '5':
            dfdata.viz.heatmap(dfdata.AGE_YRS, dfdata.NUMDAYS, f="log")
            plt.show()
        elif action == '6':
            vars = globals().copy()
            vars.update(locals())

            readline.set_completer(rlcompleter.Completer(vars).complete)
            readline.parse_and_bind("tab: complete")
            shell = code.InteractiveConsole(vars)
            try:
                shell.interact()
            except SystemExit:
                pass

async def runtasks():
    rootspace=RootWindow()
    await asyncio.sleep(0)
    taskoutput = await asyncio.gather(rootspace.base())



if __name__ == "__main__":
    asyncio.run(runtasks())