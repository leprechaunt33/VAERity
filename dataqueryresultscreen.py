import math
import re
import threading
import time
from collections import Counter

import inscriptis
import klembord
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from kivy.app import App
from kivy.clock import mainthread, Clock
from kivy.properties import NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.screenmanager import Screen
from kivy.uix.splitter import Splitter
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelHeader
from kivy.uix.textinput import TextInput
from kivy.utils import get_color_from_hex

from dataframegridview import ColoredButton, ColoredLabel
from regextextfield import RegexTextField


class DataQueryResultScreen(Screen):
    start_index = NumericProperty(0)
    screen_size = NumericProperty(1)
    _ds: pd.DataFrame = None

    def copy_to_clipboard(self,*args):
        r=self._ds.iloc[self.start_index]
        sdf=self.currapp.df['symptoms']
        syms=[]
        symrows=sdf[sdf.VAERS_ID == r.VAERS_ID].to_dict()
        for i in range(1, 6):
            syms.extend([x for x in map(lambda s: s.as_py(),symrows[f"SYMPTOM{i}"]) if ((x is not None) and (len(x)>0))])

        evthtml=f"""
<head>
    <style="text/css">
.patientdata {{
    font-weight: bold
    background-color: {self.currapp._vc['patientdata.background']}
    color: {self.currapp._vc['patientdata.textcolor']}
}}

    </style>
</head>
<table id="patienttable">
<thead>
<th colspan=4>
<div id="patientdata"><header><h3>[VAERS: {r.VAERS_ID}]<br />
PATIENT (<data class="patientdata, sex" value="{self.formatmissing(r.SEX)}">{self.formatmissing(r.SEX)}</data>,
  <data class="patientdata, age" value="{self.formatmissing(r.CAGE_YR)}">{self.formatmissing(r.CAGE_YR)}</data>,
  <data class="patientdata, state" value="{self.formatmissing(r.STATE)}">{self.formatmissing(r.STATE)}</data>)</h3></header>
  <details><summary>{len(syms)} symptom(s)</summary><br>
  {", ".join(f'<data value="{s}">{s}</data>' for s in syms)}</details>
</header></div>
</th>
</thead>
<tr>
    <th>Onset Date</th>
    <td><data value="{self.formatmissing(r.ONSET_DATE)}"><time>{self.formatmissing(r.ONSET_DATE)}</time></data></td>
    <th>Vaccinated On</th>
    <td><data value="{self.formatmissing(r.VAX_DATE)}"><time>{self.formatmissing(r.VAX_DATE)}</time></data></td>
</tr><tr>
    <th>Days since vaccination</th>
    <td><data value="{self.formatmissing(r.NUMDAYS)}">{self.formatmissing(r.NUMDAYS)}</data></td>
    <th>Life threatening?</th>
    <td><data value="{self.boolformat(r.L_THREAT)}">{self.boolformat(r.L_THREAT)}</data></td>
</tr><tr>
    <th>Classification</th>
    <td><data value="{" ".join(self.getRecordAttributes(r))}">{" ".join(self.getRecordAttributes(r))}</data></td>
    <th>Hospital Stay</th>
    <td><data value="{self.formatmissing(r.HOSPDAYS)}">{self.formatmissing(r.HOSPDAYS)} days, {self.boolformat(r.X_STAY, 'E','NE')}</data></td>
</tr>
</table>
<table id="vaccinedata">
<tr>
<thead>
<th colspan=4><div class="vaccinedata">VACCINE DATA</div></th>
</thead>
</tr><tr>
    <th>Vaccine Type</th>
    <td><data value="{self.formatmissing(r.VAX_TYPE)}">{self.formatmissing(r.VAX_TYPE)}</data></td>
    <th>Vaccine Manufacturer</th>
    <td><data value="{self.formatmissing(r.VAX_MANU)}">{self.formatmissing(r.VAX_MANU)}</data></td>
</tr><tr>
    <th>Dose Number</th>
    <td><data value="{self.formatmissing(r.VAX_DOSE_SERIES)}">{self.formatmissing(r.VAX_DOSE_SERIES)}</data></td>
    <th>Lot Number</th>
    <td><data value="{self.formatmissing(r.VAX_LOT)}">{self.formatmissing(r.VAX_LOT)}</data></td>
</tr><tr>
    <th>Vax Site</th>
    <td><data value="{self.formatmissing(r.VAX_SITE)}">{self.formatmissing(r.VAX_SITE)}</data></td>
    <th>Vaccine Route</th>
    <td><data value="{self.formatmissing(r.VAX_ROUTE)}">{self.formatmissing(r.VAX_ROUTE)}</data></td>
</tr><tr>
</table>
<table id='detailstable'>
<tr>
<td><h4>SYMPTOM TEXT</h4></td>
<td><textarea id='symptomtext'>{self.formatmissing(r.SYMPTOM_TEXT)}</textarea></td>
</tr><tr>
<td><h4>LAB DATA</h4></td>
<td><textarea id='labdata'>{self.formatmissing(r.LAB_DATA)}</textarea></td>
</tr><tr>
<td><h4>MEDICATIONS</h4></td>
<td><textarea id='medicationst'>{self.formatmissing(r.OTHER_MEDS)}</textarea></td>
</tr><tr>
<td><h4>ALLERGIES</h4></td>
<td><textarea id='symptomtext'>{self.formatmissing(r.ALLERGIES)}</textarea></td>
</tr><tr>
<td><h4>PRIOR HISTORY</h4></td>
<td><textarea id='symptomtext'>{self.formatmissing(r.HISTORY)}</textarea></td>
</tr><tr>
<td><h4>CURRENT ILLNESSES</h4></td>
<td><textarea id='symptomtext'>{self.formatmissing(r.CUR_ILL)}</textarea></td>
</tr>
</table>
        """
        klembord.set_with_rich_text(inscriptis.get_text(evthtml), evthtml)
    def goback(self, *args):
        dq = self.manager.get_screen('dataqueryscreen')
        # Clear the form so hidden filters don't stay set
        dq.reset_form()
        self.currapp.manager.current = 'dataqueryscreen'

    def boolformat(self, boolval, truthval = 'Yes', falseval='No', npval = 'Not Provided'):
        if boolval is None:
            return npval

        if isinstance(boolval,float):
            if math.isnan(boolval):
                return npval
        if str(boolval) == '':
            return falseval

        if str(boolval) == 'Y':
            return truthval

    def age(self, row):
        if row is None:
            return "Unknown"

        if math.isnan(row['AGE_YRS']):
            if math.isnan(row['CAGE_YR']):
                return "Unknown"
            return str(row['CAGE_YR'])
        else:
            return str(row['AGE_YRS'])

    def formatmissing(self,val):
        if val is None:
            return "Not Provided"

        if isinstance(val,float):
            if math.isnan(val):
                return "Not Provided"

            return str(int(val))

        if str(val) == '':
            return "Not Provided"

        return str(val)

    @mainthread
    def narrow_state(self, *args):
        dq=self.manager.get_screen('dataqueryscreen')
        dq.set_textinput('STATE',self._ds.iloc[self.start_index].STATE)

        self.start_index=0
        Clock.schedule_once(dq.execute_query,1)
        self.manager.current = 'dataqueryscreen'

    @mainthread
    def narrow_vaxtype(self, *args):
        dq=self.manager.get_screen('dataqueryscreen')
        dq.set_spinner_on('VAX_TYPE',self._ds.iloc[self.start_index].VAX_TYPE)
        dq.set_checkbox('VAX_TYPE','down')

        self.start_index=0
        Clock.schedule_once(dq.execute_query,1)
        self.manager.current = 'dataqueryscreen'

    @mainthread
    def query_batch(self,  instance, *args):
        dq=self.manager.get_screen('dataqueryscreen')
        if self._polling == False:
            dq.reset_form()
            self._polling=True
            Clock.schedule_once(self.query_batch)
        else:
            vl: RegexTextField=dq.ids['VAX_LOT']
            #dq.set_checkbox('VAX_LOT','down')
            #dq.set_textinput('VAX_LOT',self._ds.iloc[self.start_index].VAX_LOT)
            vl.set_text(self._ds.iloc[self.start_index].VAX_LOT)
            vl.set_isregex(True)
            self.start_index=0
            self.manager.current = 'dataqueryscreen'
            self._polling=False
            print("Scheduling...")
            Clock.schedule_once(dq.execute_query)

    def update_screen(self):
        if self._ds is None:
            return None

        row=self._ds.iloc[self.start_index]
        self.ids['vaxdate'].text=self.formatmissing(row.VAX_DATE)
        self.ids['onset'].text=self.formatmissing(row.ONSET_DATE)
        self.ids['numdays'].text=self.formatmissing(row.NUMDAYS)
        self.ids['classification'].text=" ".join(self.getRecordAttributes(row))
        self.ids['lthreat'].text=self.boolformat(row.L_THREAT)
        self.ids['x_stay'].text=f"{self.formatmissing(row.HOSPDAYS)} days, {self.boolformat(row.X_STAY, 'E','NE','NE')}"
        self.ids['vaxtype'].text= f"[ref=vaxtype][color=#6666FF][u]{self.formatmissing(row.VAX_TYPE)}[/u][/color][/ref]"
        self.ids['vaxmanu'].text = self.formatmissing(row.VAX_MANU)
        self.ids['vaxroute'].text = self.formatmissing(row.VAX_ROUTE)
        self.ids['vaxdose'].text = self.formatmissing(row.VAX_DOSE_SERIES)
        self.ids['vaxlot'].text = f"[ref=batch][color=#6666FF][u]{self.formatmissing(row.VAX_LOT)}[/u][/color][/ref]"
        self.ids['vaxsite'].text = self.formatmissing(row.VAX_SITE)
        self.ids['labdata'].text = self.formatmissing(row.LAB_DATA)
        self.ids['symptomtext'].text = self.formatmissing(row.SYMPTOM_TEXT)
        self.ids['allergies'].text = self.formatmissing(row.ALLERGIES)
        self.ids['medications'].text = self.formatmissing(row.OTHER_MEDS)
        self.ids['history'].text = self.formatmissing(row.HISTORY)
        self.ids['current'].text = self.formatmissing(row.CUR_ILL)
        self._navIndex.text=str(self.start_index)
        self._rh.text=self.record_header()
        sdf=self.currapp.df['symptoms']
        syms=[]
        symrows=sdf[sdf.VAERS_ID == row.VAERS_ID].to_dict()
        for i in range(1, 6):
            syms.extend([x for x in map(lambda s: s.as_py(),symrows[f"SYMPTOM{i}"]) if ((x is not None) and (len(x)>0))])

        self.ids['patient'].text=f"PATIENT ({self.formatmissing(row.SEX)}, {self.age(row)}, [color=#2222FF][ref=state]{self.formatmissing(row.STATE)}[/ref][/color]), {len(syms)} symptom(s)\n{', '.join(syms)}\n"
        self.ids['patient'].text_size=(self.currapp.root.width, 150)
        self.ids['patient'].valign='center'

    def set_ds(self,ds):
        self._ds=ds
        self.update_screen()

    def attempt_navigate(self, *args):
        print(f"In attempt_navigate, text is {self._navIndex.text}")
        if re.fullmatch("^[0-9]+$",self._navIndex.text) is not None:
            newindex=int(self._navIndex.text)
            if newindex >= len(self._ds):
                newindex=max(0,len(self._ds)-self.screen_size)
            self._navIndex.text=str(newindex)
            self.start_index = newindex
            self.update_screen()
        else:
            print("Regular expression did not match")

    def navRight(self,*args):
        if (self.start_index+self.screen_size) >= len(self._ds):
            self.start_index=max(0,len(self._ds)-self.screen_size)
        else:
            self.start_index += self.screen_size

        self._navIndex.text=str(self.start_index)
        self.update_screen()

    def navLeft(self,*args):
        self.start_index=max(self.start_index-self.screen_size,0)
        self.update_screen()
        self._navIndex.text=str(self.start_index)

    def getRecordAttributes(self,datarow):
        recAttr=[]
        if datarow['DISABLE'] == 'Y':
            recAttr.append('DISABLED')

        if datarow['BIRTH_DEFECT'] == 'Y':
            recAttr.append('BIRTH DEFECT')

        if datarow['HOSPITAL'] == 'Y':
            recAttr.append('HOSPITALISED')

        if datarow['ER_VISIT'] == 'Y':
            recAttr.append('ER[LEGACY]')

        if datarow['ER_ED_VISIT'] == 'Y':
            recAttr.append('ER')

        if datarow['DIED'] == 'Y':
            recAttr.append('DECEASED')

        if datarow['RECOVD'] == 'Y':
            recAttr.append('RECOVERED')

        return recAttr

    def record_header(self):
        if self._ds is None:
            return "No Records Displayed"
        else:
            return f"Record {self.start_index+1} of {len(self._ds)} records"

    @mainthread
    def showplot(self, fig):
        ss=self.currapp.manager.get_screen('statscreen')
        ss.set_figure(fig)
        self.currapp.manager.current = 'statscreen'

    def summarize_plot(self,*args):
        # TODO: Expand contextual heading to account for full query details
        dq=self.currapp.manager.get_screen('dataqueryscreen')

        subhead=''

        if dq.checks['VAX_TYPE'].state == 'down':
            subhead=f"{subhead}{dq.spinners['VAX_TYPE'].text} vaccinations"
        else:
            subhead=f"{subhead}Vaccinations"

        if dq.ids['STATE'].text != '':
            if dq.ids['VAX_LOT'].text != '':
                subhead = f"{subhead} in batch {dq.ids['VAX_LOT'].text}, {dq.ids['STATE']} only"
            else:
                subhead = f"{subhead} for {dq.ids['STATE'].text}"

        narrow_criteria=[]
        if dq.checks['deaths0'].state == 'down':
            narrow_criteria.append('deaths')

        if dq.checks['hosp0'].state == 'down':
            narrow_criteria.append('hospitalisations')

        if dq.checks['disabled0'].state == 'down':
            narrow_criteria.append('disabled')

        if dq.checks['emergency0'].state == 'down':
            narrow_criteria.append('ER visits')

        if len(narrow_criteria) >0:
            if len(narrow_criteria) == 1:
                subhead = f"{subhead} narrowed to include {narrow_criteria[0]} only"
            else:
                subhead = f"{subhead} narrowed to include {', '.join(narrow_criteria[0:-1])} or {narrow_criteria[-1]}"

            if subhead != '':
                subhead= f"{subhead}\n"

            narrow_criteria=[]
            if dq.checks['VAX_DOSE_SERIES'].state == 'down':
                narrow_criteria.append(f"Dose {dq.spinners['VAX_DOSE_SERIES'].text}")

            if dq.checks['SEX'].state == 'down':
                tr={'M': 'male', 'F': 'female', 'U': 'ungendered'}
                narrow_criteria.append(f"{tr[dq.spinners['SEX'].text]} only")

            if len(narrow_criteria) > 0:
                subhead=f"{subhead}{', '.join(narrow_criteria)}"
        return subhead

    def stats_thread(self):
        dfs=self.currapp.df['symptoms']
        dfd=self.currapp.df['data']
        pcounter=time.perf_counter()
        vid=dfs.VAERS_ID.tolist()
        def statusupdate(txt,stp):
            self._popup_status.text = f"{pcounter-time.perf_counter():.3} {txt}"
            self._popup_progress.value = int(stp)

        statusupdate("BEGIN",1)

        s=self.idlist[0]
        e=self.idlist[-1]
        r=e-s+1
        b=1+r//100         # ie 1 bin of 100 for 99 records
        print(f"s={s},e={e},r={r},b={b}")
        sets=[set() for i in range(b+1)]
        for id in self.idlist:
            sets[(id-s)//b].add(id)

        start_time=time.perf_counter()
        print('List of list enumeration...')
        idx=[]
        for i, y in enumerate(vid):
            try:
                if (y>=s) and (y<=e) and (y in sets[(y-s)//b]):
                    idx.append(i)
            except:
                print(f"Exception caught at {i}, {y}, {y-s}//{b}")
                return None
        print("taking results...")
        resultset=dfs.take(idx)
        end_time =time.perf_counter()
        statusupdate("SYMPTOM SET EXTRACTED",2)

        symptomset=[]
        for i in range(1,6):
            symptomset.extend([x for x in resultset[f"SYMPTOM{i}"].evaluate().to_pylist() if x is not None])
            print(len(symptomset),end=' ')

        c=Counter(symptomset)
        statusupdate("SYMPTOM SET COUNTED",3)
        plt.cla()
        plt.clf()

        fig, (ax)=plt.subplots(3,3, figsize=(25,25), dpi=100)
        fig=plt.figure(figsize=(25,25), dpi=100)
        gs0 = fig.add_gridspec(3, 3)

        ax0 = fig.add_subplot(gs0[0, 0])
        ax1 = fig.add_subplot(gs0[1, 0])
        ax2 = fig.add_subplot(gs0[2, 0])
        ax3 = fig.add_subplot(gs0[0, 1])
        ax4 = fig.add_subplot(gs0[0, 2])
        ax5 = fig.add_subplot(gs0[1, 1])
        ax6 = fig.add_subplot(gs0[1, 2])
        gs1 = gs0[2, 1:].subgridspec(2,1, wspace=0)

        ax7 = fig.add_subplot(gs1[0])
        ax8 = fig.add_subplot(gs1[1])

        ax0.grid(visible=True, which='both', axis='both')
        ax1.grid(visible=True, which='both', axis='both')
        ax2.grid(visible=True, which='both', axis='both')
        ax3.grid(visible=True, which='both', axis='both')
        ax4.grid(visible=True, which='both', axis='both')
        ax5.grid(visible=True, which='both', axis='both')
        ax6.grid(visible=True, which='both', axis='both')
        ax7.grid(visible=True, which='both', axis='both')
        ax8.grid(visible=True, which='both', axis='both')

        plt.subplots_adjust(left=0.15, top=0.9)
        fig.suptitle(self.summarize_plot(), y=0.98, fontsize=14)

        statusupdate("MPL SETUP DONE",3)

        DIED=len(self._ds[self._ds.DIED == 'Y'])
        HOSPITAL=len(self._ds[self._ds.HOSPITAL == 'Y'])
        ERVISITS=len(self._ds[(self._ds.ER_VISIT == 'Y') | (self._ds.ER_ED_VISIT=='Y')])
        DISABLED=len(self._ds[self._ds.DISABLE == 'Y'])
        OFCVISITS=len(self._ds[self._ds.OFC_VISIT == 'Y'])
        BIRTHDEFECTS=len(self._ds[self._ds.BIRTH_DEFECT == 'Y'])
        LTHREAT=len(self._ds[self._ds.L_THREAT == 'Y'])
        statusupdate("SIMPLE FILTERS DONE",4)
        BATCHES=self._ds['VAX_LOT'].str.upper().value_counts().sort_values(ascending=False)
        statusupdate("BATCHES DONE",5)
        STATES=self._ds['STATE'].str.upper().value_counts().sort_values()
        statusupdate("STATES DONE",6)
        xsummary=['Deaths','Hospitalisations','Life-threatening?','ER visits','Disabled','Birth Defects','Office/Clinic visits']
        ysummary=[DIED, HOSPITAL, LTHREAT, ERVISITS, DISABLED, BIRTHDEFECTS, OFCVISITS]

        c=np.array([sorted(c.items(), key=lambda k: k[1], reverse=True)],
                   dtype=[('s',np.dtype('U200')),('c',np.dtype('i4'))])
        if len(c['c'][0]) > 30:
            maxsym=30
        else:
            maxsym=len(c['c'][0])
        mypal = sns.color_palette('deep')[0:maxsym]
        navals = self._ds.isnull().sum().sort_values().reset_index()
        bymanu=self._ds.VAX_MANU.value_counts().reset_index()
        
        plt.rcParams['axes.grid']=True
        # NA values - graph at top left
        statusupdate("MPL STARTING",7)
        sns.barplot(y=navals['index'].to_list(), x=navals[0].to_list(), ax=ax0)
        # Top symptoms - left, middle
        sns.barplot(y=c['s'][0,0:maxsym],x=c['c'][0,0:maxsym], palette=mypal, ax=ax1)
        # Incidents by manufacturer - bottom left.
        sns.barplot(data=bymanu, y='index', x='VAX_MANU', palette=mypal, ax=ax2)
        statusupdate("MPL 3 of 10",8)
        # Numdays cumulative - upper middle
        out=self._ds
        sns.histplot(data=out[out.DIED == 'Y'], x="NUMDAYS", binrange=[0, 60], binwidth=1,
                     cumulative=True, color="red", ax=ax5)
        sns.histplot(data=out[out.HOSPITAL == 'Y'], x="NUMDAYS",
                         binrange=[0, 60], binwidth=1, alpha=0.7, cumulative=True, color="blue", ax=ax5)
        sns.histplot(data=out[(out.DISABLE == 'Y') | (out.L_THREAT == 'Y')], x="NUMDAYS",
                     binrange=[0, 60], binwidth=1, alpha=0.5, cumulative=True, color="orange", ax=ax5)
        sns.histplot(data=out[(out.ER_ED_VISIT == 'Y') | (out.ER_VISIT == 'Y')], x="NUMDAYS",
                     binrange=[0, 60], binwidth=1, alpha=0.2, cumulative=True, color="green", ax=ax5)
            # Histograms and final summary
        statusupdate("MPL MULTIPLOT",9)
        sns.histplot(x=self._ds.HOSPDAYS, bins=50, binrange=[0,49], ax=ax4)
        sns.histplot(x=self._ds.AGE_YRS, bins=24, ax=ax3)
        sns.histplot(x=self._ds.CAGE_YR, bins=24, ax=ax3, alpha=0.2)
        sns.barplot(x=xsummary, y=ysummary, palette=mypal, ax=ax6)

        statusupdate("MPL HISTS DONE",10)

        if len(BATCHES) > 40:
            maxbatch=40
        else:
            maxbatch=len(BATCHES)

        sns.barplot(x=STATES.index, y=STATES.values, ax=ax7, palette=mypal)
        sns.barplot(x=BATCHES.iloc[0:maxbatch].index, y=BATCHES.iloc[0:maxbatch].values, ax=ax8, palette=mypal)
        statusupdate("MPL PLOT COMPLETE",10)

        ax6.tick_params(axis="x", rotation=45)
        ax8.tick_params(axis="x", rotation=45)

        ax0.set_xlabel("Column")
        ax0.set_ylabel("Missing values")
        ax5.set_xlabel("Days since vaccination")
        ax2.set_ylabel("Manufacturer")
        ax2.set_xlabel("Number of incidents")

        ax3.set_xlabel("Age at vaccination")
        self.showplot(plt.gcf())

    def statsscreen(self, *args):
        self.idlist=sorted(self._ds['VAERS_ID'].to_list())
        threading.Thread(target=self.stats_thread).start()
        self._popup_progress=ProgressBar(max=10)
        self._popup_status=Label()
        hbox1=BoxLayout(orientation='vertical')
        hbox1.add_widget(self._popup_progress)
        hbox1.add_widget(self._popup_status)
        self._popup=Popup(size_hint=(0.9,0.3), content=hbox1, title="Preparing statistics...")
        self._popup.open()

    def build_navigation_strip(self):
        # LEFT TODO: Style stats button
        navbg=get_color_from_hex(self.currapp._vc['navbutton.background'])
        navfg = get_color_from_hex(self.currapp._vc['navbutton.textcolor'])
        rhbg = get_color_from_hex(self.currapp._vc['recordheader.background'])
        rhfg = get_color_from_hex(self.currapp._vc['recordheader.textcolor'])
        bbbg = get_color_from_hex(self.currapp._vc['backbutton.background'])
        bbfg = get_color_from_hex(self.currapp._vc['backbutton.textcolor'])

        navstrip = BoxLayout(orientation='horizontal', size_hint = [1, None], height=40)

        rgba=get_color_from_hex("#111133")
        btn1=ColoredButton(bbbg,text='Go Back', color=bbfg,bold=True,size_hint=[None,None],
                                   width=75, height=30)

        btn1.bind(on_press=self.goback)
        navstrip.add_widget(btn1)

        btn2=ColoredButton(rgba,text='Stats', color=[1,1,1,1],bold=True,size_hint=[None,None],
                                   width=75, height=30)

        btn2.bind(on_press=self.statsscreen)

        navstrip.add_widget(btn2)

        btn3=ColoredButton(bbbg,text='To Clipboard', color=bbfg,bold=True,size_hint=[None,None],
                                   width=90, height=30)

        btn3.bind(on_press=self.copy_to_clipboard)

        navstrip.add_widget(btn3)

        lbl1=ColoredLabel(rhbg, color=rhfg)
        lbl1.text= self.record_header()

        navstrip.add_widget(lbl1)
        self._rh=lbl1

        butNavLeft = ColoredButton(navbg,text=' < ', color=navfg,bold=True,size_hint=[None,None],
                                   width=30, height=30)
        butNavLeft.bind(on_press=self.navLeft)

        navstrip.add_widget(butNavLeft)
        navIndex=TextInput(multiline=False, size_hint=[None,None], width=60, height=30, halign='center',
                            text=str(self.start_index))
        navstrip.add_widget(navIndex)
        self._navIndex=navIndex
        self._navIndex.bind(on_text_validate=self.attempt_navigate)
        butNavRight=ColoredButton(navbg,text=' > ', color=navfg, bold = True, size_hint=[None,None],
                                  width=30, height=30)

        butNavRight.bind(on_press=self.navRight)
        navstrip.add_widget(butNavRight)
        return navstrip

    def build_record_panel(self):
        vbox1=BoxLayout(orientation='vertical')
        hbox1=BoxLayout(orientation='horizontal', padding=5)
        bglabel=get_color_from_hex(self.currapp._vc['patientdata.background'])
        pdfg=get_color_from_hex(self.currapp._vc['patientdata.textcolor'])
        ehbg=get_color_from_hex(self.currapp._vc['eventheader.background'])
        ehfg=get_color_from_hex(self.currapp._vc['eventheader.textcolor'])
        vdbg=get_color_from_hex(self.currapp._vc['vaccinedata.background'])
        vdfg=get_color_from_hex(self.currapp._vc['vaccinedata.textcolor'])
        vhbg=get_color_from_hex(self.currapp._vc['vaccineheader.background'])
        vhfg=get_color_from_hex(self.currapp._vc['vaccineheader.textcolor'])
        tboxbg = get_color_from_hex(self.currapp._vc['textbox.background'])
        tboxfg = get_color_from_hex(self.currapp._vc['textbox.textcolor'])

        lbl1=ColoredLabel(bglabel, text='PATIENT DATA', bold=True, markup=True, color=pdfg, padding=[5, 5])

        self.ids['patient']=lbl1
        lbl1.bind(on_ref_press=self.narrow_state)
        hbox1.add_widget(lbl1)
        vbox1.add_widget(hbox1)
        glayout=GridLayout(cols=4)

        # Onset
        lbl1=ColoredLabel(ehbg, text='Onset Date:', size_hint_y=None, color=ehfg,
                              height=40)

        glayout.add_widget(lbl1)

        fld1=Label(size_hint_y=None, height=40)
        self.ids['onset']=fld1
        glayout.add_widget(fld1)

        # Vax Date
        lbl2 = ColoredLabel(ehbg, text='Vaccinated On:', size_hint_y=None, color=ehfg,
                     height=40)

        glayout.add_widget(lbl2)

        fld2 = Label(size_hint_y=None, height=40)
        self.ids['vaxdate'] = fld2
        glayout.add_widget(fld2)

        # NUMDAYS
        lbl3 = ColoredLabel(ehbg, text='Days since vaccination:', size_hint_y=None, color=ehfg,
                     height=40)
        glayout.add_widget(lbl3)

        fld3 = Label(size_hint_y=None, height=40)
        self.ids['numdays'] = fld3
        glayout.add_widget(fld3)

        # L_THREAT
        lbl4 = ColoredLabel(ehbg, text='Life threatening?', size_hint_y=None, color=ehfg,
                     height=40)
        glayout.add_widget(lbl4)

        fld4 = Label(size_hint_y=None, height=40)
        self.ids['lthreat'] = fld4
        glayout.add_widget(fld4)

        # Covers DISABLE HOSPITAL DIED ER_VISIT ER_ED_VISIT
        lbl5 = ColoredLabel(ehbg, text='Classification:', size_hint_y=None, color=ehfg,
                     height=40)
        glayout.add_widget(lbl5)

        fld5 = Label(size_hint_y=None, height=40)
        self.ids['classification'] = fld5
        glayout.add_widget(fld5)

        lbl6 = ColoredLabel(ehbg, text='Hospital stay', size_hint_y=None, color=ehfg,
                     height=40)
        glayout.add_widget(lbl6)

        fld6 = Label(size_hint_y=None, height=40)
        self.ids['x_stay'] = fld6
        glayout.add_widget(fld6)

        splitr=Splitter(sizable_from = 'bottom')
        splitr.add_widget(glayout)

        vbox1.add_widget(splitr)

        hbox1=BoxLayout(orientation='horizontal', size_hint=[1, None], height=50)
        lbl1=ColoredLabel(vdbg, text='VACCINE DATA', size_hint_y=None, color=vdfg,
                              height=40, bold=True)

        self.ids['vaccine']=lbl1
        hbox1.add_widget(lbl1)
        vbox1.add_widget(hbox1)

        glayout=GridLayout(cols=4)

        # VAX_TYPE
        lbl1=ColoredLabel(vhbg, text='Vaccine Type:', size_hint_y=None, color=vhfg,
                              height=40)

        glayout.add_widget(lbl1)

        fld1=Label(size_hint_y=None, height=40, markup=True)
        self.ids['vaxtype']=fld1
        fld1.bind(on_ref_press=self.narrow_vaxtype)
        glayout.add_widget(fld1)

        # VAX_MANU
        lbl2=ColoredLabel(vhbg, text='Vaccine Manufacturer:', size_hint_y=None, color=vhfg,
                              height=40)

        glayout.add_widget(lbl2)

        fld2=Label(size_hint_y=None, height=40)
        self.ids['vaxmanu']=fld2
        glayout.add_widget(fld2)

        # VAX_DOSE_SERIES
        lbl3=ColoredLabel(vhbg, text='Dose Number:', size_hint_y=None, color=vhfg,
                              height=40)

        glayout.add_widget(lbl3)

        fld3=Label(size_hint_y=None, height=40)
        self.ids['vaxdose']=fld3
        glayout.add_widget(fld3)

        # VAX_LOT
        lbl4=ColoredLabel(vhbg, text='Lot Number:', size_hint_y=None, color=vhfg,
                              height=40)

        glayout.add_widget(lbl4)

        fld4=Label(size_hint_y=None, height=40, markup=True)
        fld4.bind(on_ref_press=self.query_batch)
        self.ids['vaxlot']=fld4
        glayout.add_widget(fld4)

        # VAX_SITE
        lbl5=ColoredLabel(vhbg, text='Vax Site:', size_hint_y=None, color=vhfg,
                              height=40)

        glayout.add_widget(lbl5)

        fld5=Label(size_hint_y=None, height=40)
        self.ids['vaxsite']=fld5
        glayout.add_widget(fld5)

        # VAX_MANU
        lbl6=ColoredLabel(vhbg, text='Vaccine Route:', size_hint_y=None, color=vhfg,
                              height=40)

        glayout.add_widget(lbl6)

        fld6=Label(size_hint_y=None, height=40)
        self.ids['vaxroute']=fld6
        glayout.add_widget(fld6)

        splitr=Splitter(sizable_from = 'bottom')
        splitr.add_widget(glayout)

        vbox1.add_widget(splitr)

        tpanel=TabbedPanel(do_default_tab=False)

        tph1=TabbedPanelHeader(text="Symptom Text")
        tpanel.add_widget(tph1)
        content1=TextInput(readonly=True, multiline=True, foreground_color=tboxfg, background_color=tboxbg)
        self.ids['symptomtext']=content1
        tph1.content=content1

        tph0=TabbedPanelHeader(text="Lab Data")
        tpanel.add_widget(tph0)
        content0=TextInput(readonly=True, multiline=True, foreground_color=tboxfg, background_color=tboxbg)
        self.ids['labdata']=content0
        tph0.content=content0

        tph2=TabbedPanelHeader(text="Medications")
        tpanel.add_widget(tph2)
        content2=TextInput(readonly=True, multiline=True, foreground_color=tboxfg, background_color=tboxbg)
        self.ids['medications']=content2
        tph2.content=content2

        tph3=TabbedPanelHeader(text="Allergies")
        tpanel.add_widget(tph3)
        content3=TextInput(readonly=True, multiline=True, foreground_color=tboxfg, background_color=tboxbg)
        self.ids['allergies']=content3
        tph3.content=content3

        tph4=TabbedPanelHeader(text="History")
        tpanel.add_widget(tph4)
        content4=TextInput(readonly=True, multiline=True, foreground_color=tboxfg, background_color=tboxbg)
        self.ids['history']=content4
        tph4.content=content4

        tph5=TabbedPanelHeader(text="Current")
        tpanel.add_widget(tph5)
        content5=TextInput(readonly=True, multiline=True, foreground_color=tboxfg, background_color=tboxbg)
        self.ids['current']=content5
        tph5.content=content5

        vbox1.add_widget(tpanel)

        return vbox1

    def size_symptoms(self, instance, *args):
        self.ids['patient'].text_size=(self.currapp.root.width, 150)

    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self._polling = False
        self.currapp=App.get_running_app()
        if 'graphdata' in self.currapp.ids:
            self._ds=self.currapp.ids['graphdata']
        ns=self.build_navigation_strip()
        self.bind(on_size=self.size_symptoms)
        vbox=BoxLayout(orientation='vertical')
        vbox.add_widget(ns)
        record_display=self.build_record_panel()
        vbox.add_widget(record_display)
        self.add_widget(vbox)