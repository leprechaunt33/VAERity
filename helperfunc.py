import kivy.app
import vaex as vx
from vaex.hdf5.dataset import Hdf5MemoryMapped
from datetime import datetime
import os, re, code
from collections import Counter
import pandas as pd
import matplotlib.pyplot as plt
plt.switch_backend('agg')
import seaborn as sns
import numpy as np
from nltk import word_tokenize

global dbfilepath
global AGE_BINS
global MAX_AGE
global TOTALBINS

dbfilepath= 'D:/AllVAERSDataCSVS'
AGE_BINS=20
MAX_AGE=120
TOTALBINS=int(MAX_AGE/AGE_BINS)+1

def vaershandle(what: str = 'DATA', years: object = 'all') -> vx.DataFrame:
    what = str(what).upper()
    if type(years) == str:
        if years == 'all':
            years = list(range(1990, datetime.today().year + 1))
            years.append('NonDomestic')
        else:
            years = [years]

    multipath = []
    for year in years:
        fpath = dbfilepath + '/' + str(year) + "VAERS" + what
        if os.path.exists(fpath + ".hdf5"):
            multipath.append(fpath + ".hdf5")
        else:
            if os.path.exists(fpath+".csv"):
                print(f"Converting {fpath}.csv to hdf5...")
                df = vx.from_csv(fpath + ".csv", convert=f"{fpath}.hdf5", encoding='latin1')
                df.close()
                multipath.append(fpath + ".hdf5")
            else:
                print(f"Skipping nonexistent {year}...")

    df = vx.open_many(multipath)
    return df

def bymonthandsex(dfdata,appobj: kivy.app.App):
    appobj.update_status("Creating groupby clause")
    gby=dfdata.groupby(by=[dfdata.pdate, dfdata.SEX])
    appobj.update_status("Aggregating")
    cnt=gby.agg('count')
    gendertab={'M': 0, 'F': 1,'U': 2}
    gcount=dict()
    appobj.update_status("Iterating rows")
    for row in cnt.iterrows():
        cr1=row[1]
        if cr1['pdate'] in gcount:
            gcount[cr1['pdate']][gendertab[cr1['SEX']]]=cr1['count']
        else:
            gcount[cr1['pdate']]=[0,0,0]
            gcount[cr1['pdate']][gendertab[cr1['SEX']]] = cr1['count']

    maledata=[gcount[k][0] for k in sorted(gcount.keys())]
    femaledata=[gcount[k][1] for k in sorted(gcount.keys())]
    ungendered=[gcount[k][2] for k in sorted(gcount.keys())]
    xdata=list(sorted(gcount.keys()))
    appobj.ids['graphdata']=pd.DataFrame.from_dict({
        'month': xdata, 'male': maledata, 'female': femaledata, 'ungendered': ungendered
    })
    plt.stackplot(xdata, maledata, femaledata, ungendered)

def piecharts1(dfdata, appobj: kivy.app.App):
    global TOTALBINS, AGE_BINS
    appobj.update_status("Now querying hospitalised by age by month...")
    appobj.update_status("Creating groupby clause")
    gby = dfdata[dfdata.HOSPITAL == 'Y'].groupby(by=[dfdata.ydate, dfdata.age_bin])
    gbydied = dfdata[dfdata.DIED == 'Y'].groupby(by=[dfdata.ydate, dfdata.age_bin])

    appobj.update_status("Aggregating")
    cnt = gby.agg('count')
    cntdied = gbydied.agg('count')
    gcount = {}
    gcount2 = {}

    appobj.update_status("Iterating aggregated data")
    # Hospitalised
    for row in cnt.iterrows():
        cr1 = row[1]
        if cr1['ydate'] in gcount:
            if cr1['age_bin'] == -1:
                gcount[cr1['ydate']][0] = cr1['count']
            else:
                agebin = int(cr1['age_bin'] / AGE_BINS)
                # print(agebin,len(gcount[cr1['pdate']]))
                gcount[cr1['ydate']][agebin] = cr1['count']
        else:
            agebin = int(cr1['age_bin'] / AGE_BINS)
            gcount[cr1['ydate']] = [0] * TOTALBINS
            if cr1['age_bin'] == -1:
                gcount[cr1['ydate']][0] = cr1['count']
            else:
                gcount[cr1['ydate']][agebin] = cr1['count']

    # Deaths
    for row in cntdied.iterrows():
        cr1 = row[1]
        if cr1['ydate'] in gcount2:
            if cr1['age_bin'] == -1:
                gcount2[cr1['ydate']][0] = cr1['count']
            else:
                agebin = int(cr1['age_bin'] / AGE_BINS)
                gcount2[cr1['ydate']][agebin] = cr1['count']
        else:
            agebin = int(cr1['age_bin'] / AGE_BINS)
            gcount2[cr1['ydate']] = [0] * TOTALBINS
            if cr1['age_bin'] == -1:
                gcount2[cr1['ydate']][0] = cr1['count']
            else:
                gcount2[cr1['ydate']][agebin] = cr1['count']

    # Now we have gcount full of hospitalised by age range
    # We now iterate the bins to generate the series data
    yseries = []
    yseries2 = []
    for agebin in range(0, TOTALBINS):
        binseries = [gcount[k][agebin] for k in sorted(gcount.keys())]
        yseries.append(binseries)
        binseries = [gcount2[k][agebin] for k in sorted(gcount2.keys())]
        yseries2.append(binseries)

    xdata = list(sorted(gcount.keys()))
    ydata2021 = [s[-2] for s in yseries]
    ydata2022 = [s[-1] for s in yseries]
    died2021 = [s[-2] for s in yseries2]
    died2022 = [s[-1] for s in yseries2]

    snum = 0
    graphbottom = [0] * len(xdata)
    graphbottom = np.array(graphbottom)

    # fig, ax = plt.subplots(2,2)
    plt.set_cmap('tab20')

    appobj.update_status(f"xdata is {len(xdata)}, ydata is {len(yseries[0])}")

    yleg = []
    yleg.append("Not Provided")
    for snum in range(1, len(yseries)):
        yleg.append(f"{(snum - 1) * AGE_BINS}-{snum * AGE_BINS}")

    fig, (axs) = plt.subplots(2, 2, figsize=(16, 16))
    mypal = sns.color_palette('deep')[0:len(yseries)]
    mypalbright = sns.color_palette('bright')[0:len(yseries)]
    appobj.ids['graphdata']=pd.DataFrame.from_dict({'age': yleg,
                                                    'died2021': died2021,
                                                    'died2022': died2022,
                                                    'hospital2021': ydata2021,
                                                    'hospital2022': ydata2022
                                                    })

    axs[0, 0].set_title("Hospitalisations by age group for 2021")
    patches, texts, autotexts = axs[0, 0].pie(ydata2021, autopct='%1.1f%%', colors=mypal, labels=yleg)
    axs[0, 1].set_title("Hospitalisations by age group for 2022")
    patches, texts, autotexts = axs[0, 1].pie(ydata2022, autopct='%1.1f%%', colors=mypal, labels=yleg)
    axs[1, 0].set_title("Deaths by age group for 2021")
    patches, texts, autotexts = axs[1, 0].pie(died2021, autopct='%1.1f%%', colors=mypalbright, labels=yleg)
    axs[1, 1].set_title("Deaths by age group for 2022")
    patches, texts, autotexts = axs[1, 1].pie(died2022, autopct='%1.1f%%', colors=mypalbright, labels=yleg)
    plt.tight_layout()

def symptoms(dfsymptoms, appobj: kivy.app.App):
    if 'symptomtxt' not in appobj.ids:
        appobj.update_status("Collating SYMPTOM1 data")
        symptomtxt = dfsymptoms.SYMPTOM1.tolist()
        appobj.update_status("Collating SYMPTOM2 data")
        symptomtxt.extend(dfsymptoms.SYMPTOM2.tolist())
        appobj.update_status("Collating SYMPTOM3 data")
        symptomtxt.extend(dfsymptoms.SYMPTOM3.tolist())
        appobj.update_status("Collating SYMPTOM4 data")
        symptomtxt.extend(dfsymptoms.SYMPTOM4.tolist())
        appobj.update_status("Collating SYMPTOM5 data")
        symptomtxt.extend(dfsymptoms.SYMPTOM5.tolist())
        symptomtxt=list(filter(lambda s: s is not None,symptomtxt))
        appobj.ids['symptomtxt']=symptomtxt

    if 'wfreq' not in appobj.ids:
        appobj.update_status("Tokenizing, this may take a while...")
        wtokens = word_tokenize(" ".join(appobj.ids['symptomtxt']))
        appobj.ids['wfreq'] = Counter(wtokens)

    allwords=pd.DataFrame(appobj.ids['wfreq'].items(), columns=['word','frequency']).sort_values(by='frequency', ascending=False).reset_index()
    appobj.ids['graphdata']=allwords
    fig, axs = plt.subplots(2, 1)
    sns.barplot(data=allwords.iloc[0:100], x='word', y='frequency', ax=axs[0])
    sns.barplot(data=allwords.iloc[100:200], x='word', y='frequency', ax=axs[1])
    axs[0].tick_params(axis="x",rotation=90)
    axs[1].tick_params(axis="x",rotation=90)
    plt.tight_layout()

def filtersymptoms(dfsymptoms, filterword, appobj):
    global symptomtxt
    if 'symptomtxt' not in globals():
        appobj.update_status("SYMPTOM1")
        symptomtxt = dfsymptoms.SYMPTOM1.tolist()
        appobj.update_status("SYMPTOM2")
        symptomtxt.extend(dfsymptoms.SYMPTOM2.tolist())
        appobj.update_status("SYMPTOM3")
        symptomtxt.extend(dfsymptoms.SYMPTOM3.tolist())
        appobj.update_status("SYMPTOM4")
        symptomtxt.extend(dfsymptoms.SYMPTOM4.tolist())
        appobj.update_status("SYMPTOM5")
        symptomtxt.extend(dfsymptoms.SYMPTOM5.tolist())
        symptomtxt = list(filter(lambda s: s is not None, symptomtxt))

    symptomfreq=Counter(symptomtxt)
    freqdf=pd.DataFrame(symptomfreq.items(), columns=['symptom','frequency']).sort_values(by='frequency', ascending=False).reset_index()

    def searchfilterword(x):
        if re.search(filterword, x, re.IGNORECASE):
            return True
        else:
            return False

    if filterword != '':
        freqdf=freqdf[freqdf.symptom.apply(searchfilterword)].reset_index()



    appobj.update_status(f'{len(freqdf)} discrete symptoms found')
    if (len(freqdf) > 100):
        appobj.update_status("Only the first 100 records will be displayed")
        freqdf=freqdf.iloc[0:100]

    appobj.ids['graphdata']=freqdf
    plt.cla()
    plt.clf()
    sns.barplot(data=freqdf, x='symptom', y='frequency')
    plt.xticks(rotation=90)
    plt.grid(visible=True,which='both', axis='both')
    plt.tight_layout()

