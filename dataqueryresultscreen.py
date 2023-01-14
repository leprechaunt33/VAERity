import datetime
import json
import math
import re
import threading
import time
from collections import Counter, OrderedDict
import datetime as dt
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
from modulardataset import ModularDataset
from regextextfield import RegexTextField
from rtfdocument import RtfDocument


class DataQueryResultScreen(Screen):
    start_index = NumericProperty(0)
    screen_size = NumericProperty(1)
    _ds: pd.DataFrame = None
    recordFormat = [{'type': 'hbox', 'content': [
        {'label': 'PATIENT', 'stylekeys': ['patiendata.background', 'patientdata.textcolor'],
         'ref_func': 'narrow_state', 'ref_resolver': 'self', 'formula': 'patient_header',
         'labelonly': True, 'resolver': 'self', 'id': 'patient', 'kwargs': {'bold': True, 'text_size': [600, 150]}}]},
                    {'tablename': 'patientdata', 'cols': 2, 'rows': 3,
                     'stylekeys': ['patientdata.background', 'patientdata.textcolor',
                                   'eventheader.background', 'eventheader.textcolor',
                                   None, None], 'type': 'table', 'splitter': 'bottom',
                     'content': [
                         {'label': 'Onset Date', 'formula': 'fm:ONSET_DATE', 'id': 'onset',
                          'kwargs': {'size_hint_y': None, 'height': 40}},
                         {'label': 'Vaccinated On', 'formula': 'fm:VAX_DATE', 'id': 'vaxdate',
                          'kwargs': {'size_hint_y': None, 'height': 40}},
                         {'label': 'Days since vaccination', 'formula': 'fm:NUMDAYS', 'id': 'numdays',
                          'kwargs': {'size_hint_y': None, 'height': 40}},
                         {'label': 'Life threatening?', 'formula': 'bf:L_THREAT', 'id': 'lthreat',
                          'kwargs': {'size_hint_y': None, 'height': 40}},
                         {'label': 'Classification', 'formula': 'recAttr',
                          'resolver': 'self', 'id': 'classification',
                          'kwargs': {'size_hint_y': None, 'height': 40}},
                         {'label': 'Hospital stay', 'formula': 'hospital_stay',
                          'resolver': 'self', 'id': 'x_stay',
                          'kwargs': {'size_hint_y': None, 'height': 40}}
                     ]
                     },
                    {'tablename': 'vaccinedata', 'cols': 2, 'rows': 3,
                     'stylekeys': ['vaccinedata.background', 'vaccinedata.textcolor',
                                   'vaccineheader.background', 'vaccineheader.textcolor',
                                   None, None], 'type': 'table', 'splitter': 'bottom',
                     'content': [
                         {'label': 'Vaccine Type', 'formula': 'print_vaxtype', 'ref': 'vaxtype',
                          'ref_func': 'narrow_vaxtype', 'ref_resolver': 'self', 'id': 'vaxtype',
                          'resolver': 'self',
                          'kwargs': {'size_hint_y': None, 'height': 40}},
                         {'label': 'Vaccine Manufacturer', 'formula': 'fm:VAX_MANU', 'id': 'vaxmanu',
                          'kwargs': {'size_hint_y': None, 'height': 40}},
                         {'label': 'Dose Number', 'formula': 'fm:VAX_DOSE_SERIES', 'id': 'vaxdose',
                          'kwargs': {'size_hint_y': None, 'height': 40}},
                         {'label': 'Lot Number', 'formula': 'print_vaxlot', 'ref': 'vaxlot',
                          'ref_func': 'query_batch', 'ref_resolver': 'self', 'id': 'vaxlot',
                          'resolver': 'self',
                          'kwargs': {'size_hint_y': None, 'height': 40}
                          },
                         {'label': 'Vaccine Site', 'formula': 'fm:VAX_SITE', 'id': 'vaxsite',
                          'kwargs': {'size_hint_y': None, 'height': 40}},
                         {'label': 'Vaccine Route', 'formula': 'fm:VAX_ROUTE', 'id': 'vaxroute',
                          'kwargs': {'size_hint_y': None, 'height': 40}}
                     ]
                     },
                    {'type': 'tabgroup', 'splitter': None, 'content': [
                        {'header': 'Symptom Text', 'content': [
                            {'textinput': True, 'formula': 'fm:SYMPTOM_TEXT', 'id': 'symptomtext'}
                        ]
                         },
                        {'header': 'Lab Data', 'content': [
                            {'textinput': True, 'formula': 'fm:LAB_DATA', 'id': 'labdata'}
                        ]
                         },
                        {'header': 'Medications', 'content': [
                            {'textinput': True, 'formula': 'fm:OTHER_MEDS', 'id': 'medications'}
                        ]
                         },
                        {'header': 'Allergies', 'content': [
                            {'textinput': True, 'formula': 'fm:ALLERGIES', 'id': 'allergies'}
                        ]
                         },
                        {'header': 'History', 'content': [
                            {'textinput': True, 'formula': 'fm:HISTORY', 'id': 'history'}
                        ]
                         },
                        {'header': 'Current', 'content': [
                            {'textinput': True, 'formula': 'fm:CUR_ILL', 'id': 'current'}
                        ]
                         }
                    ]}
                    ]

    def stylemissing(self,value,prefix, prefix2):
        return f"""
<td style="color: {self.currapp._vc[f"{prefix}.textcolor"]}; background-color: {self.currapp._vc[f"{prefix}.background"]};">
<data value="{self.formatmissing(value)}" style="color: {self.currapp._vc[f"{prefix2}.textcolor"]}; background-color: {self.currapp._vc[f"{prefix2}.background"]};">{self.formatmissing(value)}</data></td>
"""

    def copy_to_clipboard(self,*args):
        r=self._ds.iloc[self.start_index]
        cc=self.currapp._vc['eventheader.background']
        fc=self.currapp._vc['eventheader.textcolor']
        lbc = self.currapp._vc['label.textcolor']
        lbb = self.currapp._vc['label.background']
        wcc = self.currapp._vc['window.clearcolor']
        sdf=self.currapp.df['symptoms']
        syms=[]
        symrows=sdf[sdf.VAERS_ID == r.VAERS_ID].to_dict()
        for i in range(1, 6):
            syms.extend([x for x in map(lambda s: s.as_py(),symrows[f"SYMPTOM{i}"]) if ((x is not None) and (len(x)>0))])

        evthtml=f"""
<html>
<head>
    <style>
.patientdata {{
    font-weight: bold;
    background-color: {self.currapp._vc['patientdata.background']};
    color: {self.currapp._vc['patientdata.textcolor']};S
}}

#patientdata th {{
 background-color: {cc};
 color: {fc};
}}

#patientdata td > data {{
  background-color: {lbc};
  color: {lbb};
}}

body {{
  background-color: {wcc};
  color: {lbc};
}}
    </style>
</head>
<body>
<table id="patienttable">
<thead>
<th colspan=4>
<div id="patientdata"><header><h3>[VAERS: {r.VAERS_ID}]<br />
PATIENT (<data class="patientdata sex" value="{self.formatmissing(r.SEX)}">{self.formatmissing(r.SEX)}</data>,
  <data class="patientdata age" value="{self.formatmissing(r.CAGE_YR)}">{self.formatmissing(r.CAGE_YR)}</data>,
  <data class="patientdata state" value="{self.formatmissing(r.STATE)}">{self.formatmissing(r.STATE)}</data>)</h3></header>
  <details><summary>{len(syms)} symptom(s)</summary><br>
  {", ".join(f'<data value="{s}">{s}</data>' for s in syms)}</details>
</header></div>
</th>
</thead>
<tr>
    <th>Onset Date</th>
{self.stylemissing(r.ONSET_DATE,'patientdata','label')}
    <th>Vaccinated On</th>
{self.stylemissing(r.VAX_DATE,'patientdata','label')}
</tr><tr>
    <th>Days since vaccination</th>
{self.stylemissing(r.NUMDAYS,'patientdata','label')}
    <th>Life threatening?</th>
    <td><data value="{self.boolformat(r.L_THREAT)}">{self.boolformat(r.L_THREAT)}</data></td>
</tr><tr>
    <th>Classification</th>
{self.stylemissing(" ".join(self.getRecordAttributes(r)),'patientdata','label')}
    <th>Hospital Stay</th>
    <td><data value="{self.formatmissing(r.HOSPDAYS)}">{self.formatmissing(r.HOSPDAYS)} days, {self.boolformat(r.X_STAY, 'E','NE', 'NE')}</data></td>
</tr>
</table>
<table id="vaccinedata">
<tr>
<thead>
<th colspan=4><div class="vaccinedata">VACCINE DATA</div></th>
</thead>
</tr><tr>
    <th>Vaccine Type</th>
{self.stylemissing(r.VAX_TYPE,'vaccinedata','label')}
    <th>Vaccine Manufacturer</th>
{self.stylemissing(r.VAX_MANU,'vaccinedata','label')}
</tr><tr>
    <th>Dose Number</th>
{self.stylemissing(r.VAX_DOSE_SERIES,'vaccinedata','label')}
    <th>Lot Number</th>
{self.stylemissing(r.VAX_LOT,'vaccinedata','label')}
</tr><tr>
    <th>Vax Site</th>
{self.stylemissing(r.VAX_SITE,'vaccinedata','label')}
    <th>Vaccine Route</th>
{self.stylemissing(r.VAX_ROUTE,'vaccinedata','label')}
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
<body>
</html>
        """

        d=RtfDocument(font_table = [{'family': 'swiss', 'name': 'Calibri'}], color_table=[
            wcc, lbc, lbb, cc, fc
        ], page_size=[11*1440,8.5*1440])

        d.add_style(0,fontnum=0,fontsize=20, fg=lbc, bg=wcc, raw=['\\box','\\cbpat3'], stylename='ProgramColors')
        d.add_raw('\\s0').italic(False).bold(True).add_text(f"[VAERS {r.VAERS_ID}]").br()
        d.add_text(f"PATIENT ({self.formatmissing(r.SEX)}, {self.formatmissing(r.CAGE_YR)}, {self.formatmissing(r.STATE)}, {len(syms)} symptom(s)").br()
        d.add_text(", ".join(syms)).add_raw(['\\par'])
        solidborder=['single', 'single', 'single', 'single']
        dotborder=['dotted','dotted','dotted','dotted']

        # Row 1
        ptwidths=[3950, 3950*2, 3950*3, 3950*4]
        d.add_row_definition({'borders': [solidborder, dotborder, solidborder, dotborder],
                              'widths': ptwidths
                              })
        d.single_paragraph_column('Onset Date',3,4)
        d.single_paragraph_column(self.formatmissing(r.ONSET_DATE),0,1)
        d.single_paragraph_column('Vaccinated On',3,4)
        d.single_paragraph_column(self.formatmissing(r.VAX_DATE),0,1)
        d.end_row()

        # Row 2
        d.add_row_definition({'borders': [solidborder, dotborder, solidborder, dotborder],
                              'widths': ptwidths
                              })
        d.single_paragraph_column('Days since vaccination',3,4)
        d.single_paragraph_column(self.formatmissing(r.NUMDAYS),0,1)
        d.single_paragraph_column('Life threatening?',3,4)
        d.single_paragraph_column(self.formatmissing(r.L_THREAT),0,1)
        d.end_row()

        # Row 3
        d.add_row_definition({'borders': [solidborder, dotborder, solidborder, dotborder],
                              'widths': ptwidths
                              })
        d.single_paragraph_column('Classification',3,4)
        d.single_paragraph_column(" ".join(self.getRecordAttributes(r)),0,4)
        d.single_paragraph_column('Hospital stay',3,4)
        d.single_paragraph_column(f"{self.formatmissing(r.HOSPDAYS)} days, {self.boolformat(r.X_STAY, 'E','NE', 'NE')}",0,4)
        d.end_row()

        doctext=d.document()
        f=open("syntax-check.rtf","w")
        print(doctext,file=f)
        f.close()
        clippy=OrderedDict()
        clippy['HTML Format']=evthtml
        clippy['CF_TEXT']=inscriptis.get_text(evthtml)
        clippy['Rich Text Format']=doctext.encode('utf-8')
        klembord.set(clippy)

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

    def hospital_stay(self,r, f, caller):
        return f"{self.formatmissing(r.HOSPDAYS)} days, {self.boolformat(r.X_STAY, 'E', 'NE', 'NE')}"

    def recAttr(self, row, f, caller):
        return " ".join(self.getRecordAttributes(row))

    def patient_header(self, row, f, caller):
        sdf=self.currapp.df['symptoms']
        syms=[]
        symrows=sdf[sdf.VAERS_ID == row.VAERS_ID].to_dict()
        for i in range(1, 6):
            syms.extend([x for x in map(lambda s: s.as_py(),symrows[f"SYMPTOM{i}"]) if ((x is not None) and (len(x)>0))])

        pt: Label=caller.ids['patient']

        pt.text=f"PATIENT ({self.formatmissing(row.SEX)}, {self.age(row)}, [color=#2222FF][ref=state]{self.formatmissing(row.STATE)}[/ref][/color]), {len(syms)} symptom(s)\n{', '.join(syms)}\n"
        pt.texture_update()
        lblheight=max(pt.texture_size[1]*1.1, 100)
        pt.text_size=(self.currapp.root.width * 0.9, lblheight)
        pt.valign='center'
        return pt.text


    def print_vaxtype(self, r, f, caller):
        return f"[ref=vaxtype][color=#6666FF][u]{caller.formatmissing(r.VAX_TYPE)}[/u][/color][/ref]"

    def print_vaxlot(self, r, f, caller):
        return f"[ref=batch][color=#6666FF][u]{caller.formatmissing(r.VAX_LOT)}[/u][/color][/ref]"

    def update_screen(self):
        if self._ds is None:
            return None

        row=self._ds.iloc[self.start_index]

        for id in self.md.ids.keys():
            self.md.ids[id].text=self.md.formula(id, row, self)

        self._navIndex.text=str(self.start_index)
        self._rh.text=self.record_header()

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
    def showplot(self, fig, xdata):
        ss=self.currapp.manager.get_screen('statscreen')
        ss.set_figure(fig, xdata)
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
        if dq.flux['deaths'].selection() == 'Yes':
            narrow_criteria.append('deaths')

        if dq.flux['hospital'].selection() == 'Yes':
            narrow_criteria.append('hospitalisations')

        if dq.flux['disable'].selection() == 'Yes':
            narrow_criteria.append('disabled')

        if (dq.flux['er0'].selection() == 'Yes') or (dq.flux['er1'].selection() == 'Yes'):
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
        figs=[fig]
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
        if not 'osdate' in self._ds.columns.to_list():
            self._ds['osdate']=pd.to_datetime(self._ds.RECVDATE, errors='coerce')
            try:
                self._ds['weekdate']=self._ds['osdate']-self._ds['osdate'].dt.dayofweek.map(dt.timedelta)
                self._ds['monthdate'] = self._ds['osdate'].dt.to_period("M")
            except Exception as ex:
                print(ex)

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
        xdata=[[]]
        
        plt.rcParams['axes.grid']=True
        # NA values - graph at top left
        statusupdate("MPL STARTING",7)
        xdata[0].append(navals[0].to_list())
        sns.barplot(y=navals['index'].to_list(), x=navals[0].to_list(), ax=ax0)
        ax0.set_title("Data Insights by % filled")
        # Top symptoms - left, middle
        sns.barplot(y=c['s'][0,0:maxsym],x=c['c'][0,0:maxsym], palette=mypal, ax=ax1)
        ax1.set_title("Most common symptoms")
        xdata[0].append(c['c'][0,0:maxsym])
        # Incidents by manufacturer - bottom left.
        sns.barplot(data=bymanu, y='index', x='VAX_MANU', palette=mypal, ax=ax2)
        ax2.set_title("Reports by Manufacturer")
        xdata[0].append(bymanu['VAX_MANU'])
        statusupdate("MPL 3 of 10",8)
        # Numdays cumulative - upper middle
        out=self._ds
        sns.histplot(data=out[out.DIED == 'Y'], x="NUMDAYS", binrange=[0, 60], binwidth=1,
                     cumulative=True, color="red", ax=ax5)
        xdata[0].append(out['NUMDAYS'].tolist())
        sns.histplot(data=out[out.HOSPITAL == 'Y'], x="NUMDAYS",
                         binrange=[0, 60], binwidth=1, alpha=0.7, cumulative=True, color="blue", ax=ax5)
        sns.histplot(data=out[(out.DISABLE == 'Y') | (out.L_THREAT == 'Y')], x="NUMDAYS",
                     binrange=[0, 60], binwidth=1, alpha=0.5, cumulative=True, color="orange", ax=ax5)
        sns.histplot(data=out[(out.ER_ED_VISIT == 'Y') | (out.ER_VISIT == 'Y')], x="NUMDAYS",
                     binrange=[0, 60], binwidth=1, alpha=0.2, cumulative=True, color="green", ax=ax5)
        ax5.set_title("Cumulative by days onset")
            # Histograms and final summary
        statusupdate("MPL MULTIPLOT",9)
        sns.histplot(x=self._ds.HOSPDAYS, bins=50, binrange=[0,49], ax=ax4)
        ax4.set_title("Hospital Stays")

        sns.histplot(x=self._ds.AGE_YRS, bins=24, ax=ax3)
        sns.histplot(x=self._ds.CAGE_YR, bins=24, ax=ax3, alpha=0.2)
        ax3.set_title("Age distribution")

        sns.barplot(x=xsummary, y=ysummary, palette=mypal, ax=ax6)
        ax6.set_title("At a glance")

        xdata[0].append(self._ds.HOSPDAYS.tolist())
        xdata[0].append(self._ds.AGE_YRS.tolist())
        xdata[0].append(xsummary)

        statusupdate("MPL HISTS DONE",10)

        if len(BATCHES) > 40:
            maxbatch=40
        else:
            maxbatch=len(BATCHES)

        sns.barplot(x=STATES.index, y=STATES.values, ax=ax7, palette=mypal)
        ax7.set_title("Top States in Dataset")
        xdata[0].append(STATES.index)
        sns.barplot(x=BATCHES.iloc[0:maxbatch].index, y=BATCHES.iloc[0:maxbatch].values, ax=ax8, palette=mypal)
        ax8.set_title(f"Top batches ({maxbatch} shown)")
        xdata[0].append(BATCHES.iloc[0:maxbatch].index)
        statusupdate("MPL PLOT PAGE 1/2 COMPLETE",10)

        ax6.tick_params(axis="x", rotation=45)
        ax8.tick_params(axis="x", rotation=45)

        ax0.set_xlabel("Column")
        ax0.set_ylabel("Missing values")
        ax5.set_xlabel("Days since vaccination")
        ax2.set_ylabel("Manufacturer")
        ax2.set_xlabel("Number of incidents")

        ax3.set_xlabel("Age at vaccination")

        fig2 = plt.figure(figsize=(25, 25), dpi=100)
        gs2 = fig2.add_gridspec(4, 1)
        ts=[]
        ts.append(fig2.add_subplot(gs2[0]))
        ts.append(fig2.add_subplot(gs2[1]))
        ts.append(fig2.add_subplot(gs2[2]))
        ts.append(fig2.add_subplot(gs2[3]))

        tsindex=0
        xdata.append([])

        dq=self.currapp.manager.get_screen('dataqueryscreen')
        if (len(BATCHES) == 1) or (dq.ids['VAX_LOT'].tbox.text != ''):
            gby = self._ds.value_counts(['weekdate', 'VAX_LOT'], dropna=False).reset_index(name='count')
            pivot = gby.pivot_table(index='weekdate', columns=['VAX_LOT'], values='count', dropna=False)
            pivot.fillna(value=0, inplace=True)

            unique_axes=gby['VAX_LOT'].unique()
            seriez=[pivot[y].to_list() for y in pivot.columns]

            ts[tsindex].stackplot(pivot.index, *seriez, labels=unique_axes)

            ts[tsindex].set_title("Reports for batch by time")
            xmin=gby['weekdate'].min()
            xmax=gby['weekdate'].max()
            ts[tsindex].set_xlim(left=xmin, right=xmax)
            xdata[1].append(pivot.index)

            tsindex += 1

        if (len(STATES) == 1) or (dq.ids['STATE'].text != ''):
            gby = self._ds.value_counts(['weekdate', 'STATE'], dropna=False).reset_index(name='count')
            pivot = gby.pivot_table(index='weekdate', columns=['STATE'], values='count', dropna=False)
            pivot.fillna(value=0, inplace=True)

            unique_axes=gby['STATE'].unique()
            seriez=[pivot[y].to_list() for y in pivot.columns]

            lines=ts[tsindex].stackplot(pivot.index, *seriez, labels=unique_axes)
            plt.legend()
            xmin=gby['weekdate'].min()
            xmax=gby['weekdate'].max()
            ts[tsindex].set_xlim(left=xmin, right=xmax)
            ts[tsindex].set_title("Reports per state by time")
            xdata[1].append(pivot.index)

            tsindex += 1

        gby=self._ds.value_counts(['weekdate','STATE'], dropna=False).reset_index(name='count')
        pivot=gby.pivot_table(index='weekdate',columns=['STATE'], values='count', dropna=False)
        sns.heatmap(pivot, ax=ts[tsindex])
        statusupdate("MPL PLOT PAGE 2/2 COMPLETE",10)
        figs.append(fig2)
        self.showplot(figs, xdata)

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

        self.md=ModularDataset(self,self.recordFormat)
        for content in self.md.content:
            vbox1.add_widget(content)

        return vbox1

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