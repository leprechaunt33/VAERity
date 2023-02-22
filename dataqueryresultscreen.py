import datetime
import json
import math
import pprint
import re, os
import threading
import time
import traceback
from collections import Counter, OrderedDict
import datetime as dt
import inscriptis
import klembord
import matplotlib.pyplot as plt
from kivy.uix.spinner import Spinner
from kivy.uix.togglebutton import ToggleButton
import pickle
plt.switch_backend('agg')
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
                            {'textinput': True, 'id': 'symptomtext', 'formula': 'textinput_manage', 'resolver': 'self'}
                        ]
                         },
                        {'header': 'Lab Data', 'content': [
                            {'textinput': True, 'id': 'labdata', 'formula': 'textinput_manage', 'resolver': 'self'}
                        ]
                         },
                        {'header': 'Medications', 'content': [
                            {'textinput': True, 'id': 'medications', 'formula': 'textinput_manage', 'resolver': 'self'}
                        ]
                         },
                        {'header': 'Allergies', 'content': [
                            {'textinput': True, 'id': 'allergies', 'formula': 'textinput_manage', 'resolver': 'self'}
                        ]
                         },
                        {'header': 'History', 'content': [
                            {'textinput': True, 'id': 'history', 'formula': 'textinput_manage', 'resolver': 'self'}
                        ]
                         },
                        {'header': 'Current', 'content': [
                            {'textinput': True, 'formula': 'fm:CUR_ILL', 'id': 'current'}
                        ]
                         }
                    ]}
                    ]

    def textinput_manage(self,r, f, caller):

        if f == 'symptomtext':
            return f"=== {len(r.SYMPTOM_TEXT or '')} characters ===\n{self.formatmissing(r.SYMPTOM_TEXT)}"
        elif f == 'labdata':
            return f"=== {len(r.LAB_DATA or '')} characters ===\n{self.formatmissing(r.LAB_DATA)}"
        elif f == 'medications':
            return f"=== {len(r.OTHER_MEDS or '')} characters ===\n{self.formatmissing(r.OTHER_MEDS)}"
        elif f == 'history':
            return f"=== {len(r.HISTORY or '')} characters ===\n{self.formatmissing(r.HISTORY)}"
        elif f == 'allergies':
            return f"=== {len(r.ALLERGIES or '')} characters ===\n{self.formatmissing(r.ALLERGIES)}"

    def stylemissing(self,value,prefix, prefix2):
        return f"""
<td style="color: {self.currapp._vc[f"{prefix}.textcolor"]}; background-color: {self.currapp._vc[f"{prefix}.background"]};">
<data value="{self.formatmissing(value)}" style="color: {self.currapp._vc[f"{prefix2}.textcolor"]}; background-color: {self.currapp._vc[f"{prefix2}.background"]};">{self.formatmissing(value)}</data></td>
"""

    def handle_keyboard(self, window, key, scancode, codepoint, modifier, keyname):
        focus = self.currapp.current_focus()
        if (len(modifier) == 0) and (keyname in self.currapp.navkeys):
            if (focus is None) or (not isinstance(focus, TextInput)):
                if keyname == 'left':
                    self.navLeft()
                elif keyname == 'right':
                    self.navRight()
        elif (keyname == 'x') and all(m in modifier for m in ['ctrl', 'alt']):
            for key in self.md.stylekeys:
                for element in self.md.stylekeys[key]:
                    if isinstance(element, ColoredLabel):
                        print(f"{key}: {element.text}")
        elif (keyname == 'y') and all(m in modifier for m in ['ctrl', 'alt']):
            for element in self.walk():
                print(f"{type(element)} {element.size} {element.pos} parent {element.parent}")
                if hasattr(element,'text'):
                    print(element.text)
                if hasattr(element,'color'):
                    print(element.color)
        elif (keyname == 'd') and all(m in modifier for m in ['ctrl', 'alt']):
            self.save_db_state()
        elif (keyname == 'h') and all(m in modifier for m in ['ctrl', 'alt']):
            self.start_analysis_thread()

    def save_db_state(self, *args):
        dfdata: pd.DataFrame=self._ds

        def outcome_binary(r):
            return int(r['DIED'] == 'Y')+int(r['HOSPITAL']=='Y')*2+int(r['DISABLE']=='Y')*4+\
                int(r['L_THREAT']=='Y')*8+int(r['X_STAY']=='Y')*16+int(r['RECOVD']=='Y')*32+ \
                int(r['ER_VISIT'] == 'Y') * 64+ int(r['ER_ED_VISIT']=='Y')*128+ \
                int(r['OFC_VISIT'] == 'Y') * 256 + int(r['BIRTH_DEFECT']=='Y')*512

        dfdata['outcome']=dfdata.apply(outcome_binary, axis=1)
        pdata=dfdata.sort_values(by='VAERS_ID')[['VAERS_ID', 'outcome']].to_dict()
        if 'APPDATA' in os.environ:
            folder=os.environ['APPDATA']
        else:
            folder = os.path.expanduser('~')

        pfile=str(os.path.join(folder, 'dbstate.pickle'))

        if os.path.exists(pfile):
            with open(pfile, "rb") as pickle_file:
                pdata2=pickle.load(pickle_file)
            set1=set(pdata2['VAERS_ID'])
            set2=set(pdata['VAERS_ID'])
            set3=set1 ^ set2
            set4=set1 & set3
            set5=set2 & set3
            diff_file = str(os.path.join(folder, 'dbstate-difference.txt'))
            with open(diff_file,"w") as diffy:
                print(f"Removed: {set4}", file=diffy)
                print(f"Added: {set5}", file=diffy)
        else:
            with open(pfile, "wb") as pickle_file:
                pickle.dump(pdata, pickle_file)


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

        if (row.SPLTTYPE is not None) and (row.SPLTTYPE != ''):
            hdrtext=f"{row.SPLTTYPE}\n"
        else:
            hdrtext=''

        hdrtext += f"PATIENT ({self.formatmissing(row.SEX)}, {self.age(row)}, [color=#2222FF][ref=state]{self.formatmissing(row.STATE)}[/ref][/color]), {len(syms)} symptom(s)\n{', '.join(syms)}\n"
        pt.text=hdrtext
        pt.texture_update()
        lblheight=min(max(pt.texture_size[1]*1.1, 100),600)
        pt.text_size=(self.currapp.root.width * 0.9, lblheight)
        pt.valign='center'
        if len(syms) > 30:
            print(f"{pt.text} {pt.width} {pt.height} {pt.text_size} {pt.texture_size}")
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
    def showplot(self, fig, xdata, graph_options):
        ss=self.currapp.manager.get_screen('statscreen')
        ss.set_figure(fig, xdata, graph_options, self.md)
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
            if dq.ids['VAX_LOT'].selection() != '':
                subhead = f"{subhead} in batch {dq.ids['VAX_LOT'].selection()}, {dq.ids['STATE'].text} only"
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

    def patient_outcomes_by_time(self, current_figure, current_axis, options, popup, axis: plt.Axes):
        if options is None:
            options = {'stacked': False, 'cumulative': False, 'percentage': False, 'absence': False}
        limited_ds: pd.DataFrame=self._ds[['DIED','HOSPITAL','DISABLE', 'ER_ED_VISIT', 'L_THREAT', 'weekdate']].groupby('weekdate').count()
        if options['absence']:
            outcomegroup = self.md.datatables['data'].get_group('outcomes')
            filterlets = []
            for field in outcomegroup:
                filterlets.append(f"({field.name} != 'Y')")
            nooutcomefilter = ' & '.join(filterlets)
            nooutcome_ds=self._ds.query(nooutcomefilter)

        axis.cla()
        stackdict = limited_ds.fillna(value=0).reset_index().to_dict()
        stacklist = []
        stacklegends=[]
        ourx = stackdict['weekdate']
        for col in stackdict.keys():
            if col != 'weekdate':
                oury = stackdict[col]
                if options['percentage']:
                    dslen=len(self._ds)
                    stackcol = [oury[k]*100/dslen for k, v in sorted(ourx.items(), key=lambda x: x[1])]
                else:
                    stackcol = [oury[k] for k, v in sorted(ourx.items(), key=lambda x: x[1])]
                stacklist.append(stackcol)
                stacklegends.append(col)
        if options['absence']:
            if options['percentage']:
                stackcol = [len(nooutcome_ds[nooutcome_ds.weekdate == v]) * 100 / dslen for k, v in sorted(ourx.items(), key=lambda x: x[1])]
            else:
                stackcol = [len(nooutcome_ds[nooutcome_ds.weekdate == v]) for k, v in
                            sorted(ourx.items(), key=lambda x: x[1])]
            stacklist.append(stackcol)
            stacklegends.append('No outcome')
        ourx = [x.date() for x in sorted(ourx.values())]
        if options['stacked']:
            if options['cumulative']:
                for yseries in stacklist:
                    for i, y in enumerate(yseries):
                        if i > 0:
                            yseries[i]=y+yseries[i-1]
                axis.stackplot(ourx, *stacklist)
            else:
                axis.stackplot(ourx, *stacklist)
            axis.legend(stacklegends)
        else:
            if options['cumulative']:
                for yseries in stacklist:
                    for i, y in enumerate(yseries):
                        if i > 0:
                            yseries[i]=y+yseries[i-1]
                for i, series in enumerate(stacklist):
                    axis.plot(ourx, series, label=stacklegends[i])

                axis.legend()
            else:
                if options['percentage']:
                    for i, series in enumerate(stacklist):
                        axis.plot(ourx, series, label=stacklegends[i])

                    axis.legend()
                else:
                    for i, series in enumerate(stacklist):
                        axis.plot(ourx, series, label=stacklegends[i])

                    axis.legend()
                    #sns.lineplot(data=limited_ds, ax=axis)
        if options['cumulative']:
            axis.set_title("Key patient outcomes by time (cumulative)")
        else:
            axis.set_title("Key patient outcomes by time")
        if options['percentage']:
            axis.set_ylabel("Percentage of total reports")
        else:
            axis.set_ylabel("Number of reports")
        axis.set_xlabel("Week")
        xdata=limited_ds.reset_index()['weekdate'].to_list()
        return xdata

    def bytime_buildopt(self,current_figure, current_axis, options, popup, axis):
        lbg=get_color_from_hex(self.currapp._vc['label.background'])
        lfg=get_color_from_hex(self.currapp._vc['label.textcolor'])
        cboxcol=get_color_from_hex(self.currapp._vc['togglebutton.background'])

        hbox1=BoxLayout(orientation='horizontal')
        lbl1 = ColoredLabel(lbg, color=lfg, text="Cumulative?", size_hint=(0.2,0.1))
        lbl1.pos_hint={'top': 1, 'x': 0}
        self.ids['bytime_cumulative']=ToggleButton(size_hint_y=None, height=25, size_hint_x=None, width=40,
                                                   allow_no_selection=True, background_color=cboxcol,
                                                   pos_hint={'x': 0.2, 'top': 1})
        hbox1.add_widget(lbl1)
        hbox1.add_widget(self.ids['bytime_cumulative'])

        hbox2 = BoxLayout(orientation='horizontal')
        lbl1 = ColoredLabel(lbg, color=lfg, text="Stacked?", size_hint=(0.2,0.1))
        lbl1.pos_hint={'top': 0.9, 'x': 0}
        self.ids['bytime_stacked']=ToggleButton(size_hint_y=None, height=25, size_hint_x=None, width=40,
                                                   allow_no_selection=True, background_color=cboxcol,
                                                   pos_hint={'x': 0.2, 'top': 0.9})
        hbox2.add_widget(lbl1)
        hbox2.add_widget(self.ids['bytime_stacked'])

        hbox3 = BoxLayout(orientation='horizontal')
        lbl1 = ColoredLabel(lbg, color=lfg, text="Percent?", size_hint=(0.2,0.1))
        lbl1.pos_hint={'top': 0.8, 'x': 0}
        self.ids['bytime_percent']=ToggleButton(size_hint_y=None, height=25, size_hint_x=None, width=40,
                                                   allow_no_selection=True, background_color=cboxcol,
                                                   pos_hint={'x': 0.2, 'top': 0.8})
        hbox3.add_widget(lbl1)
        hbox3.add_widget(self.ids['bytime_percent'])

        hbox4 = BoxLayout(orientation='horizontal')
        lbl1 = ColoredLabel(lbg, color=lfg, text="Include no outcome?", size_hint=(0.2,0.1))
        lbl1.pos_hint={'top': 0.7, 'x': 0}
        self.ids['bytime_absence']=ToggleButton(size_hint_y=None, height=25, size_hint_x=None, width=40,
                                                   allow_no_selection=True, background_color=cboxcol,
                                                   pos_hint={'x': 0.2, 'top': 0.7})
        hbox4.add_widget(lbl1)
        hbox4.add_widget(self.ids['bytime_absence'])

        return [hbox1, hbox2, hbox3, hbox4]

    def bytime_checkopt(self, current_figure, current_axis, options, popup, axis):
        if self.ids['bytime_percent'].state == 'down':
            options['percentage']=True
        else:
            options['percentage']=False

        if self.ids['bytime_stacked'].state == 'down':
            options['stacked']=True
        else:
            options['stacked']=False

        if self.ids['bytime_cumulative'].state == 'down':
            options['cumulative']=True
        else:
            options['cumulative']=False

        if self.ids['bytime_absence'].state == 'down':
            options['absence']=True
        else:
            options['absence']=False


    def top_count_by_criteria(self,current_figure, current_axis, options, popup, axis):
        if 'filter' in options:
            filterset=self._ds.query(options['filter'])
        else:
            filterset=self._ds

        if options['special'] == 'symptoms':
            symptomset=self.get_symptoms(filterset)
            xvalues=[k for k, v in sorted(symptomset.items(), key=lambda x: x[1], reverse=True)]
            yvalues=[v for k,v in sorted(symptomset.items(), key=lambda x: x[1], reverse=True)]

        queryfield=options['queryfield']

        if ('regex_remove' in options) and (options['regex_remove'] != ''):
            reBar=options['regex_remove']
            if not options['special']:
                filterset=filterset[~filterset[queryfield].str.contains(reBar)]
            else:
                xmatch=[re.match(reBar, x) is not None for x in xvalues]
                xvalues=[x for i,x in enumerate(xvalues) if not xmatch[i]]
                yvalues=[y for i,y in enumerate(yvalues) if not xmatch[i]]

        if not options['special']:
            newds = filterset.value_counts(queryfield).reset_index(name='count')
        else:
            if ('start' in options) and (options['start'] < len(xvalues)):
                newds=xvalues[options['start']:]
                xvalues = xvalues[options['start']:]
                yvalues = yvalues[options['start']:]
            else:
                newds=xvalues


        if len(newds) < options['max_n']:
            maxrecords=len(newds)
        else:
            maxrecords=options['max_n']

        if 'palsize' in options:
            try:
                palsize=int(options['palsize'])
            except Exception:
                palsize=6
        else:
            palsize=6

        if 'palette' in options:
            mypal: list = sns.color_palette(options['palette'], palsize)[0:min(palsize,maxrecords)]
        else:
            mypal=sns.color_palette('deep',palsize)[0:min(palsize,maxrecords)]

        if ('rpal' in options) and options['rpal']:
            mypal.reverse()

        axis.cla()

        if not options['special']:
            if ('start' in options) and (options['start'] < len(newds)):
                newds = newds.sort_values(by='count', ascending=False).tail(newds.shape[0] - options['start'])
            else:
                newds = newds.sort_values(by='count', ascending=False)
            xvalues=newds[queryfield].iloc[0:maxrecords]
            yvalues=newds['count'].iloc[0:maxrecords]
            try:
                descript=self.md.find_field(queryfield)[1].description
            except Exception:
                descript=queryfield
        else:
            descript="Symptom name"

        if ('orientation' in options) and (options['orientation'] == 'horizontal'):
            sns.barplot(y=xvalues[0:maxrecords], x=yvalues[0:maxrecords], ax=axis, palette=mypal)
            axis.set_xlabel("Total records")
            axis.set_ylabel(descript)
        else:
            if len(xvalues) == 0:
                print(f"Skipping plot of graph {current_figure}/figure {current_axis} as there are no x values")
            else:
                if len(xvalues) < 3:
                    print(f"Plotting graph of {len(xvalues)} records without a palette to prevent problems.")
                    if isinstance(xvalues, list):
                        sns.barplot(x=xvalues[0:maxrecords], y=yvalues[0:maxrecords], ax=axis)
                    else:
                        sns.barplot(x=xvalues.iloc[0:maxrecords], y=yvalues.iloc[0:maxrecords], ax=axis)
                else:
                    if isinstance(xvalues, list):
                        sns.barplot(x=xvalues[0:maxrecords], y=yvalues[0:maxrecords], ax=axis, palette=mypal)
                    else:
                        sns.barplot(x=xvalues.iloc[0:maxrecords], y=yvalues.iloc[0:maxrecords], ax=axis, palette=mypal)
            axis.set_ylabel("Total records")
            axis.set_xlabel(descript)

        if 'start' in options:
            title = f"Records {options['start']}-{options['start']+maxrecords} for {descript}"
        else:
            title=f"Top {maxrecords} for {descript}"

        if 'filter' in options:
            if options['absence']:
                descript="Absence of outcome"
            else:
                filterfield = options['filterfield']
                try:
                    descript = self.md.find_field(filterfield)[1].description
                except Exception:
                    descript=filterfield

            title += f", filtered by {descript}"
        if ('regex_remove' in options) and (options['regex_remove'] != ''):
            title +=", outliers removed"

        if 'title' not in options:
            axis.set_title(title)
        else:
            axis.set_title(options['title'])

        if 'rotatex' in options:
            axis.tick_params(axis="x", rotation=options['rotatex'])

        return xvalues

    def symptom_toggle(self, *args):
        if self.ids['topcount_symptom'].state == 'down':
            self.ids['topcount_fieldname'].disabled=True
        else:
            self.ids['topcount_fieldname'].disabled = False

    def toggle_filterfield(self, *args):
        if self.ids['topcount_absence'].state == 'down':
            self.ids['topcount_filterfield'].disabled=True
        else:
            self.ids['topcount_filterfield'].disabled = False

    def topcount_buildopt(self, current_figure, current_axis, options, popup, axis):
        lbg=get_color_from_hex(self.currapp._vc['label.background'])
        lfg=get_color_from_hex(self.currapp._vc['label.textcolor'])
        tbg=get_color_from_hex(self.currapp._vc['textbox.background'])
        tfg=get_color_from_hex(self.currapp._vc['textbox.textcolor'])
        cboxcol=get_color_from_hex(self.currapp._vc['togglebutton.background'])

        lbl1 = ColoredLabel(lbg, color=lfg, text="Range/Max Records", size_hint=(0.2,0.1))
        lbl1.pos_hint={'top': 1, 'x': 0}
        tinput1=TextInput(background_color=tbg, foreground_color=tfg, size_hint=(0.8, 0.1), text='30')
        self.ids['topcount_maxn']=tinput1
        tinput1.pos_hint= {'top': 1, 'x': 0.2}

        if 'maxn' in options:
            tinput1.text=str(options['maxn'])

        lbl1a= ColoredLabel(lbg, color=lfg, text="Symptom?", size_hint=(0.2,0.1), pos_hint={'x': 0, 'top': 0.9})
        tb1a=ToggleButton(size_hint=(None, None), width=75, height=25,
                          allow_no_selection=True, background_color=cboxcol,
                          pos_hint={'x': 0.2, 'top': 0.9})
        self.ids['topcount_symptom']=tb1a
        tb1a.bind(state=self.symptom_toggle)
        lbl2 = ColoredLabel(lbg, color=lfg, text="Field?", size_hint=(0.2,0.1))
        lbl2.pos_hint={'top': 0.8, 'x': 0}
        spinner1=Spinner(size_hint=(0.8, 0.1), pos_hint={'x': 0.2, 'top': 0.8})
        fieldnames=self._ds.columns.to_list()
        spinner1.values=fieldnames
        if options['queryfield'] != '':
            spinner1.text=options['queryfield']

        self.ids['topcount_fieldname']=spinner1
        lbl3 = ColoredLabel(lbg, color=lfg, text="Outlier Regex?", size_hint=(0.2,0.1))
        lbl3.pos_hint={'top': 0.7, 'x': 0}
        tinput2 = TextInput(background_color=tbg, foreground_color=tfg, size_hint=(0.8, 0.1), text='')
        tinput2.pos_hint = {'top': 0.7, 'x': 0.2}
        self.ids['topcount_outlier']=tinput2

        if 'regex_remove' in options:
            tinput2.text=str(options['regex_remove'])

        lbl4=ColoredLabel(lbg, color=lfg, text="Filter by Outcome?", size_hint=(0.2,0.1))
        lbl4.pos_hint={'top': 0.6, 'x': 0}
        spinner2 = Spinner(size_hint=(0.8, 0.1), pos_hint={'x': 0.2, 'top': 0.6})
        outcomegroup=self.md.datatables['data'].get_group('outcomes')
        if outcomegroup is not None:
            fieldnames=[f.description for f in outcomegroup]
        else:
            fieldnames=[]
        spinner2.values=fieldnames
        self.ids['topcount_filterfield']=spinner2
        lbl4a=ColoredLabel(lbg, color=lfg, text="Absence of outcome?", size_hint=(0.2,0.1))
        lbl4a.pos_hint={'top': 0.5, 'x': 0}
        tb4a=ToggleButton(size_hint=(None, None), width=75, height=25,
                          allow_no_selection=True, background_color=cboxcol,
                          pos_hint={'x': 0.2, 'top': 0.5})
        self.ids['topcount_absence']=tb4a
        tb4a.bind(state=self.toggle_filterfield)
        lbl5=ColoredLabel(lbg, color=lfg, text="Orientation?", size_hint=(0.2,0.1))
        lbl5.pos_hint={'top': 0.4, 'x': 0}
        spinner3=Spinner(size_hint=(0.2, 0.1), pos_hint={'x': 0.2, 'top': 0.4})
        self.ids['topcount_orientation']=spinner3
        spinner3.values=['horizontal', 'vertical']
        if 'orientation' in options:
            spinner3.text=options['orientation']
        else:
            spinner3.text='vertical'

        lbl6=ColoredLabel(lbg, color=lfg, text="X Label Rotation", size_hint=(0.2,0.1))
        lbl6.pos_hint={'top': 0.4, 'x': 0.4}
        tinput3 = TextInput(background_color=tbg, foreground_color=tfg, size_hint=(0.2, 0.1), text='')
        tinput3.pos_hint = {'top': 0.4, 'x': 0.6}
        self.ids['topcount_rotatex']=tinput3
        if 'rotatex' in options:
            tinput3.text=str(options['rotatex'])

        if 'palette' in options:
            paltext=options['palette']
        else:
            paltext='deep'

        lblpal = ColoredLabel(lbg, color=lfg, text="Palette", size_hint=(0.2,0.1),
                              pos_hint={'x': 0.4, 'top': 1})
        tbpal = TextInput(background_color=tbg, foreground_color=tfg, size_hint=(0.4, 0.1),
                          text=paltext, pos_hint={'x': 0.6, 'top': 1})
        self.ids['topcount_pal'] = tbpal

        cbrpal=ToggleButton(
            size_hint=(None, None), width=75, height=25,allow_no_selection=True,
            background_color=cboxcol, pos_hint={'x': 0.6, 'top': 0.9})
        self.ids['topcount_rpal']=cbrpal

        lblrpal=ColoredLabel(lbg, color=lfg, text="Reverse Palette", size_hint=(0.2,0.1),
                              pos_hint={'x': 0.4, 'top': 0.9})

        lblspal=ColoredLabel(lbg, color=lfg, text="Palette Size", size_hint=(0.2,0.1),
                              pos_hint={'x': 0.7, 'top': 0.9})

        if 'palsize' in options:
            palsize=str(options['palsize'])
        else:
            palsize='6'

        tbspal = TextInput(background_color=tbg, foreground_color=tfg, size_hint=(0.1, 0.1),
                          text=palsize, pos_hint={'x': 0.9, 'top': 0.9})
        self.ids['topcount_spal']=tbspal


        return [lbl1, tinput1, lbl1a, tb1a, lbl2, spinner1, lbl3, tinput2,
                lbl4, lbl4a, tb4a, spinner2, lbl5, spinner3, tbpal, lblpal,
                cbrpal, lblrpal, lblspal, tbspal, lbl6, tinput3]

    def topcount_checkopt(self, current_figure, current_axis, options, popup, axis):
        # Pop original title if we're running this via repurpose graph
        options.pop('title', None)
        options.pop('start', None)
        options.pop('rotatex', None)
        maxnstr: str=self.ids['topcount_maxn'].text
        if maxnstr != '':
            maxlist=maxnstr.split('-')
            print(maxlist)
            if len(maxlist) == 2:
                try:
                    options['start']=int(maxlist[0])
                    maxnstr=str(int(maxlist[1])-options['start'])
                except Exception as ex:
                    # If the text is not an int, remove the start index.
                    # The next try block will also fail and fall back to the
                    # default.
                    print(traceback.print_exc())
                    options.pop('start', None)

            try:
                maxnint=int(maxnstr)
            except Exception as ex:
                print(traceback.print_exc())
                if 'max_n' in options:
                    maxnint = options['max_n']
                else:
                    maxnint=30

        options['max_n']=maxnint
        if (self.ids['topcount_symptom'].state == 'down') or (self.ids['topcount_fieldname'].text == 'symptomtext'):
            options['special'] = 'symptoms'
            options['queryfield'] = 'symptomtext'
        else:
            options['special'] = False
            options['queryfield']=self.ids['topcount_fieldname'].text
        options['regex_remove']=self.ids['topcount_outlier'].text
        options['absence'] = False
        outcomegroup = self.md.datatables['data'].get_group('outcomes')
        if self.ids['topcount_filterfield'].text != '':
            ffield=[f.name for f in outcomegroup if f.description == self.ids['topcount_filterfield'].text][0]
            options['filter']=f"{ffield} == 'Y'"
            options['filterfield']=ffield
        elif self.ids['topcount_absence'].state == 'down':
            options['absence']=True
            filterlets=[]
            for field in outcomegroup:
                filterlets.append(f"({field.name} != 'Y')")
            options['filter']=' & '.join(filterlets)
        else:
            options.pop('filter', None)
            options['filterfield']=''

        if self.ids['topcount_orientation'].text == '':
            options['orientation']='vertical'
        else:
            options['orientation'] = self.ids['topcount_orientation'].text

        if self.ids['topcount_rotatex'].text != '':
            try:
                options['rotatex'] = float(self.ids['topcount_rotatex'].text)
            except Exception:
                # Print exception traceback and do not set a default for rotatex
                print(traceback.print_exc())

        if self.ids['topcount_pal'].text == '':
            options.pop('palette', None)
        else:
            options['palette']=self.ids['topcount_pal'].text

        if self.ids['topcount_rpal'].state == 'down':
            options['rpal'] = True
        else:
            options['rpal'] = False

        if self.ids['topcount_spal'].text != '':
            try:
                options['palsize']=int(self.ids['topcount_spal'].text)
                if options['palsize'] < 1:
                    raise ValueError('palsize')
            except Exception:
                raise ValueError("If specified, the palette size must be an integer greater than zero!")
        else:
            options.pop('palsize', None)

    def histograms_runopt(self,current_figure, current_axis, options, popup, axis: plt.Axes):
        axis.cla()
        if 'queryfield' in options:
            queryfield=options['queryfield']

        if 'filter' in options:
            if not isinstance(options['filter'], list):
                filterset=self._ds.query(options['filter'])
            else:
                filterset=None
        else:
            filterset=self._ds

        kwarg=dict()

        minx=0
        maxx=0

        def hist_process(i, q):
            kwarg.clear()
            for field in ['bins', 'binrange', 'binwidth', 'alpha', 'cumulative', 'color']:
                if field in options:
                    if isinstance(queryfield, list):
                        kwarg[field] = options[field][i]
                    else:
                        kwarg[field] = options[field]
            for key in list(kwarg.keys()):
                if kwarg[key] is None:
                    kwarg.pop(key, None)

            try:
                sns.histplot(data=filterset, ax=axis, x=str(q),**kwarg)
            except ValueError as ex:
                if not 'bins' in kwarg:
                    maxval=filterset[str(q)].max()
                    # So it turns out in some instances even if we expicitly
                    # set bins if it was not set, histplot can still raise an
                    # error if there is only one or less values in the result
                    # set, such as with the monkeypox dataset of 53 records
                    # In these cases we ignore the failed histogram and keep
                    # going.
                    if 'binwidth' in kwarg:
                        kwarg['bins']=int(maxval/kwarg['binwidth'])
                        try:
                            sns.histplot(data=filterset, ax=axis, x=str(q), **kwarg)
                        except Exception as ex:
                            print(f"Continuing despite error for histogram for field {q} and kwarg {kwarg}")
                            print(ex)


        if isinstance(queryfield, list):
            for i, query in enumerate(queryfield):
                if ('filter' in options) and isinstance(options['filter'], list):
                    if options['filter'][i] is None:
                        filterset=self._ds
                    else:
                        filterset=self._ds.query(options['filter'][i])
                if len(filterset) == 0:
                    continue
                hist_process(i, query)
                minx = min(minx, filterset[query].min())
                maxx = max(maxx, filterset[query].max())
        else:
            if len(filterset) == 0:
                return list()
            hist_process(0, queryfield)
            minx=filterset[queryfield].min()
            maxx= filterset[queryfield].max()

        if 'title' in options:
            axis.set_title(options['title'])
        else:
            descript=self.md.find_field(queryfield)[1].description
            if 'filterfield' in options:
                descript=f"{descript}, filtered by {self.md.find_field(options['filterfield'])[1].description}"

            axis.set_title(f"Histogram for {descript}")

        if 'xlim' in options:
            axis.set_xlim(*options['xlim'])

        if 'ylim' in options:
            axis.set_ylim(*options['ylim'])

        if 'xlabel' in options:
            axis.set_xlabel(options['xlabel'])

        if 'ylabel' in options:
            axis.set_xlabel(options['ylabel'])

        if isinstance(queryfield, list):
            axis.legend()

        return range(int(minx), int(maxx)+1)

    def histograms_checkopt(self,current_figure, current_axis, options, popup, axis: plt.Axes):
        options['queryfield']=self.ids['hist_queryfield'].text.split(',')
        if len(options['queryfield']) == 1:
            options['queryfield']=options['queryfield'][0]
        elif len(options['queryfield']) == 0:
            raise ValueError("You must specify at least one field to generate a histogram for!")

        if self.ids['hist_cumulative'].state == 'down':
            if isinstance(options['queryfield'], list):
                options['cumulative']=[True]*len(options['queryfield'])
            else:
                options['cumulative']=True
        else:
            if isinstance(options['queryfield'], list):
                options['cumulative']=[False]*len(options['queryfield'])
            else:
                options['cumulative']=False

        def process_value(x: str):
            if re.fullmatch(r'^(\d+)$', str(x)):
                return int(x)
            elif re.fullmatch(r'^[0-9.\-]+$', str(x)):
                return float(x)
            elif str(x) == '':
                return None
            else:
                return x

        for field in ['binrange', 'bins', 'binwidth', 'color', 'alpha']:
            textfield=f"hist_{field}"
            if textfield[-1] != 's':
                textfield += 's'
            if self.ids[textfield].text == '':
                options.pop(field, None)
                continue

            if field == 'binrange':
                values=self.ids[textfield].text.split(';')
                values=[list(map(lambda x: float(x) if x is not None else None,r.split(','))) for r in values]
            else:
                values=self.ids[textfield].text.split(',')

            if len(values) == 0:
                options.pop(field, None)
                continue
            elif len(values) == 1:
                options[field]=process_value(values[0])
            else:
                finalvals=[]
                for v in values:
                    if isinstance(v, list):
                        # Currently only binrange is a list of lists
                        finalvals.append([process_value(v[0]), process_value(v[1])])
                    else:
                        finalvals.append(process_value(v))

                options[field]=finalvals

        xlim=self.ids['hist_xlim'].text.split(',')
        if len(xlim) == 2:
            options['xlim']=[process_value(xlim[0]), process_value(xlim[1])]
        else:
            options.pop('xlim', None)

        filters=self.ids['hist_filters'].text.split('\n')
        if len(filters) > 1:
            options['filter']=[f if len(f) > 0 else None for f in filters]

    def histograms_buildopt(self,current_figure, current_axis, options, popup, axis: plt.Axes):
        lbg=get_color_from_hex(self.currapp._vc['label.background'])
        lfg=get_color_from_hex(self.currapp._vc['label.textcolor'])
        tbg=get_color_from_hex(self.currapp._vc['textbox.background'])
        tfg=get_color_from_hex(self.currapp._vc['textbox.textcolor'])
        cboxcol=get_color_from_hex(self.currapp._vc['togglebutton.background'])

        lbl1 = ColoredLabel(lbg, color=lfg, text="Cumulative?", size_hint=(0.2,0.1))
        lbl1.pos_hint={'top': 1, 'x': 0}
        cbox1=ToggleButton(size_hint_y=None, height=25, size_hint_x=None, width=40, allow_no_selection=True,
                           background_color=cboxcol, pos_hint={'x': 0.2, 'top': 1})
        if 'cumulative' in options:
            if isinstance(options['cumulative'], list):
                cum=options['cumulative'][0]
            else:
                cum=options['cumulative']

            if cum:
                cbox1.state = 'down'
            else:
                cbox1.state = 'normal'

        self.ids['hist_cumulative'] = cbox1

        lbl2 = ColoredLabel(lbg, color=lfg, text="X Bounds", size_hint=(0.2,0.1),
                            pos_hint={'top': 1, 'x': 0.4})
        tbox1 = TextInput(background_color=tbg, foreground_color=tfg, size_hint=(0.2, 0.1),
                          pos_hint = {'top': 1, 'x': 0.6})
        if 'xlim' in options:
            tbox1.text=f"{options['xlim'][0]},{options['xlim'][1]}"

        self.ids['hist_xlim']=tbox1

        if 'color' in options:
            colors=options['color']
            if isinstance(colors, list):
                colors=','.join(map(lambda c: '' if c is None else str(c),colors))
        else:
            colors=''

        lbl3 = ColoredLabel(lbg, color=lfg, text="Colors", size_hint=(0.2,0.1),
                            pos_hint={'top': 0.7, 'x': 0.6})
        tbox2 = TextInput(background_color=tbg, foreground_color=tfg, size_hint=(0.2, 0.1),
                          pos_hint = {'top': 0.7, 'x': 0.8}, text=str(colors))

        self.ids['hist_colors']=tbox2

        if 'alpha' in options:
            alphas=options['alpha']
            if isinstance(alphas, list):
                alphas=','.join(map(lambda c: '' if c is None else str(c),alphas))
        else:
            alphas=''

        lbl4 = ColoredLabel(lbg, color=lfg, text="Alpha", size_hint=(0.2,0.1),
                            pos_hint={'top': 0.9, 'x': 0})
        tbox3 = TextInput(background_color=tbg, foreground_color=tfg, size_hint=(0.2, 0.1),
                          pos_hint = {'top': 0.9, 'x': 0.2}, text=str(alphas))

        self.ids['hist_alphas']=tbox3

        if 'bins' in options:
            bins=options['bins']
            if isinstance(bins, list):
                bins=','.join(map(lambda c: '' if c is None else str(c),bins))
        else:
            bins=''

        lbl5 = ColoredLabel(lbg, color=lfg, text="Bins", size_hint=(0.2,0.1),
                            pos_hint={'top': 0.9, 'x': 0.4})
        tbox4 = TextInput(background_color=tbg, foreground_color=tfg, size_hint=(0.2, 0.1),
                          pos_hint = {'top': 0.9, 'x': 0.6}, text=str(bins))

        self.ids['hist_bins']=tbox4

        if 'binwidth' in options:
            binwidths = options['binwidth']
            if isinstance(binwidths, list):
                binwidths = ','.join(map(lambda c: '' if c is None else str(c), binwidths))
        else:
            binwidths = ''

        lbl6 = ColoredLabel(lbg, color=lfg, text="Bin Widths", size_hint=(0.2, 0.1),
                            pos_hint={'top': 0.8, 'x': 0})
        tbox5 = TextInput(background_color=tbg, foreground_color=tfg, size_hint=(0.2, 0.1),
                          pos_hint={'top': 0.8, 'x': 0.2}, text=str(binwidths))

        self.ids['hist_binwidths'] = tbox5

        if ('binrange' in options) and isinstance(options['binrange'], list):
            binranges = options['binrange']
            if isinstance(binranges[0], list):
                binranges=';'.join(','.join(map(lambda c: '' if c is None else str(c), r)) for r in binranges)
            else:
                binranges = ','.join(map(lambda c: '' if c is None else str(c), binranges))
        else:
            binranges = ''

        lbl7 = ColoredLabel(lbg, color=lfg, text="Bin Ranges", size_hint=(0.2, 0.1),
                            pos_hint={'top': 0.8, 'x': 0.4})
        tbox6 = TextInput(background_color=tbg, foreground_color=tfg, size_hint=(0.2, 0.1),
                          pos_hint={'top': 0.8, 'x': 0.6}, text=binranges)

        self.ids['hist_binranges'] = tbox6

        if ('queryfield' in options) and isinstance(options['queryfield'], list):
            queryfield = ','.join(map(lambda c: '' if c is None else str(c), options['queryfield']))
        else:
            if 'queryfield' in options:
                queryfield = options['queryfield']
            else:
                queryfield = ''

        lbl8 = ColoredLabel(lbg, color=lfg, text="Query Field", size_hint=(0.2, 0.1),
                            pos_hint={'top': 0.7, 'x': 0})
        tbox7 = TextInput(background_color=tbg, foreground_color=tfg, size_hint=(0.4, 0.1),
                          pos_hint={'top': 0.7, 'x': 0.2}, text=queryfield)

        self.ids['hist_queryfield'] = tbox7

        if 'filter' in options:
            filtertext='\n'.join(list(map(lambda f: f if f is not None else '', options['filter'])))
        else:
            filtertext=''

        lbl9 = ColoredLabel(lbg, color=lfg, text="Filters", size_hint=(0.2, 0.2),
                            pos_hint={'top': 0.6, 'x': 0})
        tbox8 = TextInput(background_color=tbg, foreground_color=tfg, size_hint=(0.4, 0.2),
                          pos_hint={'top': 0.6, 'x': 0.2}, text=filtertext)

        self.ids['hist_filters']= tbox8

        return [lbl1, cbox1, lbl2, tbox1, lbl3, tbox2, lbl4, tbox3, lbl5, tbox4, lbl6, tbox5,
                lbl7, tbox6, lbl8, tbox7, lbl9, tbox8]

    def get_symptoms(self, ds: pd.DataFrame, topids: bool = False):
        dfs=self.currapp.df['symptoms']
        idlist=sorted(ds['VAERS_ID'].to_list())
        vid=dfs.VAERS_ID.tolist()
        s=idlist[0]
        e=idlist[-1]
        r=e-s+1
        b=1+r//100         # ie 1 bin of 100 for 99 records
        print(f"s={s},e={e},r={r},b={b}")
        sets=[set() for i in range(b+1)]
        for id in idlist:
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

        symptomset=[]
        if topids:
            v=resultset["VAERS_ID"].tolist()
            recordcounts = dict()
            recordcounts.update({(k, 0) for k in v})
        for i in range(1,6):
            r=resultset[f"SYMPTOM{i}"].evaluate().to_pylist()
            symptomset.extend([x for x in r if x is not None])
            if topids:
                for j, x in enumerate(r):
                    if r is not None:
                        recordcounts[v[j]] += 1
            print(len(symptomset),end=' ')

        c=Counter(symptomset)
        end_time =time.perf_counter()
        print(f"that took {end_time-start_time} secs")

        if topids:
            tophonkers=[k for k, v in sorted(recordcounts.items(), key=lambda x: x[1], reverse=True) if v > 50]
            honkcount = [v for k, v in sorted(recordcounts.items(), key=lambda x: x[1], reverse=True) if v > 50]
            return c, tophonkers, honkcount
        else:
            return c

    def analyse_resultset(self, *args):
        (c, tophonkers, honkcount) = self.get_symptoms(self._ds, True)
        if not 'osdate' in self._ds.columns.to_list():
            self._ds['osdate']=pd.to_datetime(self._ds.RECVDATE, errors='coerce')
            try:
                self._ds['weekdate'] = self._ds['osdate'] - self._ds['osdate'].dt.dayofweek.map(dt.timedelta)
                self._ds['monthdate'] = self._ds['osdate'].dt.to_period("M")
            except Exception as ex:
                print(ex)

        outcomegroup = self.md.datatables['data'].get_group('outcomes')
        filterlets = []
        for field in outcomegroup:
            filterlets.append(f"({field.name} != 'Y')")
        nooutcomefilter = ' & '.join(filterlets)
        nooutcome=len(self._ds.query(nooutcomefilter))

        content = f"Total records without an outcome: {nooutcome} ({nooutcome*100/len(self._ds):.2f}%)\n"
        content += f"Maximum days of onset: {self._ds['NUMDAYS'].max()}\n"
        content += f"Maximum days of hospitalisation: {self._ds['HOSPDAYS'].max()}\n"
        content += f"Youngest/Oldest patient: {self._ds['AGE_YRS'].min()}, {self._ds['AGE_YRS'].max()}\n"
        content += f"Date Range: {self._ds['osdate'].min()}, {self._ds['osdate'].max()}\n"
        content += f"Top Honkers (>50 symptoms):\n{','.join([str(h) for h in tophonkers])}\n"
        content += f"Total {len(tophonkers)} honkers.\n"
        if len(honkcount) == 0:
            content += "No honkers.\n"
        else:
            content += f"Maximum symptom count is {honkcount[0]}.\n"
        self.update_popup_results(content)

    @mainthread
    def update_popup_results(self, resulttext):
        self._popup_results.text=resulttext

    def start_analysis_thread(self, *args):
        self._popup_results=TextInput()
        vbox1=BoxLayout(orientation='vertical')
        vbox1.add_widget(self._popup_results)
        self._popup=Popup(size_hint=(0.9,0.3), content=vbox1, title="Analysing dataset...")
        self.currapp.start_thread_once(name='analysis thread', target=self.analyse_resultset)
        self._popup.open()


    def stats_thread(self):
        dfs=self.currapp.df['symptoms']
        dfd=self.currapp.df['data']
        pcounter=time.perf_counter()

        def statusupdate(txt,stp):
            self._popup_status.text = f"{pcounter-time.perf_counter():.3} {txt}"
            self._popup_progress.value = int(stp)

        statusupdate("CREATING GRAPHS",1)
        plt.cla()
        plt.clf()

        fig, (ax)=plt.subplots(3,3, figsize=(26,25), dpi=100)
        fig=plt.figure(figsize=(26,25), dpi=100)
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

        statusupdate("MPL SETUP DONE, EXTRACTING DATA",4)
        if not 'osdate' in self._ds.columns.to_list():
            self._ds['osdate']=pd.to_datetime(self._ds.RECVDATE, errors='coerce')
            try:
                self._ds['weekdate']=self._ds['osdate']-self._ds['osdate'].dt.dayofweek.map(dt.timedelta)
                self._ds['monthdate'] = self._ds['osdate'].dt.to_period("M")
            except Exception as ex:
                print(ex)

        if not 'country_code' in self._ds.columns.to_list():
            try:
                self._ds['country_code'] = self._ds['SPLTTYPE'].str[0:2]
            except Exception as ex:
                print(traceback.print_exc())

        DIED=len(self._ds[self._ds.DIED == 'Y'])
        HOSPITAL=len(self._ds[self._ds.HOSPITAL == 'Y'])
        ERVISITS=len(self._ds[(self._ds.ER_VISIT == 'Y') | (self._ds.ER_ED_VISIT=='Y')])
        DISABLED=len(self._ds[self._ds.DISABLE == 'Y'])
        OFCVISITS=len(self._ds[self._ds.OFC_VISIT == 'Y'])
        BIRTHDEFECTS=len(self._ds[self._ds.BIRTH_DEFECT == 'Y'])
        LTHREAT=len(self._ds[self._ds.L_THREAT == 'Y'])
        statusupdate("SIMPLE FILTERS DONE",5)
        xsummary=['Deaths','Hospitalisations','Life-threatening?','ER visits','Disabled','Birth Defects','Office/Clinic visits']
        ysummary=[DIED, HOSPITAL, LTHREAT, ERVISITS, DISABLED, BIRTHDEFECTS, OFCVISITS]
        xsummary=[xsummary[i] for i, y in sorted(enumerate(ysummary), key=lambda y: y[1], reverse=True)]
        ysummary=sorted(ysummary, reverse=True)

        mypal = sns.color_palette('deep')[0:50]
        navals = self._ds.isnull().sum().sort_values().reset_index()
        xdata=[[]]
        graph_options=[[]]
        topnkeys={'buildopt': self.topcount_buildopt, 'runopt': self.top_count_by_criteria,
                  'checkopt': self.topcount_checkopt}

        histkeys={'buildopt': self.histograms_buildopt, 'runopt': self.histograms_runopt,
                  'checkopt': self.histograms_checkopt}

        plt.rcParams['axes.grid']=True
        # NA values - graph at top left
        statusupdate("MPL STARTING",7)
        xdata[0].append(navals[0].to_list())
        graph_options[0].append({})
        sns.barplot(y=navals['index'].to_list(), x=navals[0].to_list(), ax=ax0)
        ax0.set_title("Data Insights by % filled")
        # Top symptoms - left, middle
        symopt={'regex_remove': '', 'orientation': 'horizontal', 'special': 'symptoms',
                'max_n': 30, 'queryfield': 'symptomtext'}
        symopt.update(topnkeys)
        xdat=self.top_count_by_criteria(0, 1, symopt, None, ax1)
        xdata[0].append(xdat)
        graph_options[0].append(symopt)
        # Incidents by manufacturer - bottom left.
        symopt={'regex_remove': '', 'orientation': 'horizontal', 'special': False,
                'queryfield': 'VAX_MANU', 'max_n': 30}
        symopt.update(topnkeys)
        xdat=self.top_count_by_criteria(0, 2, symopt, None, ax2)
        graph_options[0].append(symopt)
        xdata[0].append(xdat)
        statusupdate("MPL 3 of 10",8)
        # Histograms and final summary
        statusupdate("MPL MULTIPLOT",9)
        symopt={'queryfield': ['AGE_YRS', 'CAGE_YR'], 'bins': [24,24], 'alpha': [None, 0.2], 'title': "Age distribution"}
        symopt.update(histkeys)
        xdat = self.histograms_runopt(0, 3, symopt, None, ax3)
        graph_options[0].append(symopt)
        xdata[0].append(xdat)

        symopt={'queryfield': 'HOSPDAYS', 'binwidth': 1, 'xlim': [0, 49], 'title': "Hospital Stays"}
        symopt.update(histkeys)
        xdat = self.histograms_runopt(0, 4, symopt, None, ax4)
        graph_options[0].append(symopt)
        xdata[0].append(xdat)

        # Numdays cumulative - upper middle
        out=self._ds
        symopt={
            'filter': ["DIED == 'Y'","HOSPITAL == 'Y'","(DISABLE == 'Y') | (L_THREAT == 'Y')", "(ER_VISIT == 'Y') | (ER_ED_VISIT == 'Y')"],
            'queryfield': ['NUMDAYS']*4, 'color': ['red','blue','orange','green'], 'cumulative': [True]*4,
            'alpha': [None,0.7, 0.5, 0.2], 'title': 'Cumulative by days onset', 'xlabel': 'Days since vaccination',
            'binwidth': [1]*4, 'xlim': [0, 60], 'binrange': [[0,365], [0,365], [0,365], [0,365]]
        }
        symopt.update(histkeys)
        xdat = self.histograms_runopt(0, 5, symopt, None, ax5)
        graph_options[0].append(symopt)
        xdata[0].append(xdat)

        sns.barplot(x=xsummary, y=ysummary, palette=mypal, ax=ax6)
        ax6.set_title("At a glance")

        xdata[0].append(xsummary)
        graph_options[0].append({})

        statusupdate("MPL HISTS DONE",10)

        symopt={'regex_remove': '', 'orientation': 'vertical', 'special': False,
                'queryfield': 'STATE', 'max_n': 40, 'title': 'Top 40 States in Dataset'}
        symopt.update(topnkeys)
        xdat=self.top_count_by_criteria(0, 7, symopt, None, ax7)
        graph_options[0].append(symopt)
        xdata[0].append(xdat)

        symopt={'regex_remove': '', 'orientation': 'vertical', 'special': False,
                'queryfield': 'VAX_LOT', 'max_n': 40, 'rotatex': 45, 'title': 'Top 40 Batches'}
        symopt.update(topnkeys)
        xdat=self.top_count_by_criteria(0, 8, symopt, None, ax8)
        graph_options[0].append(symopt)
        xdata[0].append(xdat)

        statusupdate("MPL PLOT PAGE 1/2 COMPLETE",11)

        ax6.tick_params(axis="x", rotation=45)

        ax0.set_xlabel("Column")
        ax0.set_ylabel("Missing values")
        ax5.set_xlabel("Days since vaccination")
        ax2.set_ylabel("Manufacturer")
        ax2.set_xlabel("Number of incidents")

        ax3.set_xlabel("Age at vaccination")

        fig2 = plt.figure(figsize=(15, 15), dpi=100)
        gs2 = fig2.add_gridspec(7, 7)
        ts=[]
        ts.append(fig2.add_subplot(gs2[2:5,2:5]))
        ts.append(fig2.add_subplot(gs2[0:2,0:7]))
        ts.append(fig2.add_subplot(gs2[2:5,0:2]))
        ts.append(fig2.add_subplot(gs2[2:5,5:7]))
        ts.append(fig2.add_subplot(gs2[5:7, 0:7]))

        out['lensym']= out['SYMPTOM_TEXT'].str.len()
        out['lenlab']= out['LAB_DATA'].str.len()
        out['lenhist'] = out['HISTORY'].str.len()
        out['lenmed'] = out['OTHER_MEDS'].str.len()
        tsindex=0
        xdata.append([])
        graph_options.append([])
        plt.tight_layout(pad=5.0)

        colors=sns.color_palette("muted",10)

        sns.histplot(
            data=out, x="lensym", ax=ts[tsindex], alpha=0.5, color=colors[0], bins=640, binrange=[0,31999], label="Symptom text")
        sns.histplot(
            data=out, x="lenlab", ax=ts[tsindex], alpha=0.5, color=colors[1], bins=640, binrange=[0,31999], label="Lab data")

        sns.histplot(
            data=out, x="lenhist", ax=ts[tsindex], alpha=0.5, color=colors[2], bins=640, binrange=[0,31999], label="Medical history")

        sns.histplot(
            data=out, x="lenmed", ax=ts[tsindex], alpha=0.5, color=colors[3], bins=640, binrange=[0,31999], label="Other meds")

        ts[tsindex].set_xlabel("Length of corpus")
        ts[tsindex].set_ylabel("Number of reports")
        ts[tsindex].legend()
        statusupdate("MPL PLOT PAGE 2/2 MULTIHIST DONE", 12)
        xdata[1].append(range(0,int(out['lensym'].max()), 10))
        graph_options[1].append({})
        tsindex += 1

        BATCHES=xdata[0][8]
        STATES=xdata[0][7]
        dq=self.currapp.manager.get_screen('dataqueryscreen')
        if (len(BATCHES) == 1) or (dq.ids['VAX_LOT'].tbox.text != ''):
            gby = self._ds.value_counts(['weekdate', 'VAX_LOT'], dropna=False).reset_index(name='count')
            pivot = gby.pivot_table(index='weekdate', columns=['VAX_LOT'], values='count', dropna=False)
            pivot.fillna(value=0, inplace=True)

            unique_axes=gby['VAX_LOT'].unique()
            seriez=[pivot[y].to_list() for y in pivot.columns]

            ts[tsindex].stackplot(pivot.index, *seriez, labels=unique_axes)

            ts[tsindex].set_title("Reports for batch by time")
            ts[tsindex].set_xlabel("Week")
            ts[tsindex].set_ylabel("Number of reports")
            ts[tsindex].legend()
            xmin=gby['weekdate'].min()
            xmax=gby['weekdate'].max()
            ts[tsindex].set_xlim(left=xmin, right=xmax)
            xdata[1].append(pivot.index)
            graph_options[1].append({})

            tsindex += 1
        elif (len(STATES) == 1) or (dq.ids['STATE'].text != ''):
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
            ts[tsindex].set_xlabel("Week")
            ts[tsindex].set_ylabel("Number of reports")
            ts[tsindex].legend()
            xdata[1].append(pivot.index)
            graph_options[1].append({})

            tsindex += 1
        else:
            gby = self._ds.value_counts(['weekdate'], dropna=False).reset_index(name='count')
            gby.fillna(value=0, inplace=True)
            pp = pprint.PrettyPrinter(indent=4)
            ourdata=gby.to_dict()
            ourx=ourdata['weekdate']
            oury=ourdata['count']
            oury=[oury[k] for k, v in sorted(ourx.items(), key=lambda x: x[1])]
            ourx=[x.date() for x in sorted(ourx.values())]

            myax: plt.Axes = ts[tsindex]
            myax.bar(ourx,oury)
            xmin=min(ourx)
            xmax=max(ourx)

            ts[tsindex].set_xlim(left=xmin, right=xmax)
            ts[tsindex].set_title("Reports by time")
            xdata[1].append(ourx)
            graph_options[1].append({})

            tsindex += 1

        statusupdate("MPL PLOT PAGE 2/2 BY TIME DONE", 13)

        symopt={'regex_remove': '', 'orientation': 'horizontal', 'special': False,
                'queryfield': 'VAX_TYPE', 'max_n': 10, 'title': 'Incidents by Vaccine Type',
                'palette': "ch:s=2.9,r=-0.5,h=0.8,l=0.7,d=0.2"}
        symopt.update(topnkeys)
        xdat=self.top_count_by_criteria(1, 2, symopt, None, ts[tsindex])
        graph_options[1].append(symopt)
        xdata[1].append(xdat)
        ts[tsindex].set_xlabel("Number of incidents")
        ts[tsindex].set_ylabel("Vaccine Type")
        tsindex += 1

        statusupdate("MPL PLOT PAGE 2/2 BY VAX_TYPE DONE", 14)

        symopt={'regex_remove': '', 'orientation': 'horizontal', 'special': False,
                'queryfield': 'VAX_DOSE_SERIES', 'max_n': 10, 'title': 'Incidents by Dose Number',
                'palette': "ch:s=2.9,r=-0.5,h=0.8,l=0.7,d=0.2"}
        symopt.update(topnkeys)
        xdat=self.top_count_by_criteria(1, 3, symopt, None, ts[tsindex])
        graph_options[1].append(symopt)
        xdata[1].append(xdat)
        ts[tsindex].set_xlabel("Number of incidents")
        ts[tsindex].set_ylabel("Dose number")
        tsindex += 1

        statusupdate("MPL PLOT PAGE 2/2 BY DOSE DONE", 15)

        limited_ds=self._ds[['DIED','HOSPITAL','DISABLE', 'ER_ED_VISIT', 'L_THREAT', 'weekdate']].groupby('weekdate').count()
        sns.lineplot(data=limited_ds, ax=ts[tsindex])
        xdata[1].append(limited_ds.reset_index()['weekdate'].to_list())
        graph_options[1].append({'buildopt': self.bytime_buildopt, 'runopt': self.patient_outcomes_by_time,
                                 'checkopt': self.bytime_checkopt
                                 })
        ts[tsindex].set_title("Key patient outcomes by time")
        ts[tsindex].set_ylabel("Number of reports")
        ts[tsindex].set_xlabel("Week")
        tsindex +=1

        statusupdate("MPL PLOT PAGE 2/2 COMPLETE",20)
        figs.append(fig2)
        self.showplot(figs, xdata, graph_options)

    def statsscreen(self, *args):
        self._popup_progress=ProgressBar(max=20)
        self._popup_status=Label()
        hbox1=BoxLayout(orientation='vertical')
        hbox1.add_widget(self._popup_progress)
        hbox1.add_widget(self._popup_status)
        self._popup=Popup(size_hint=(0.9,0.3), content=hbox1, title="Preparing statistics...")
        self.currapp.start_thread_once(name='stats generation', target=self.stats_thread)
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
        self.buttons['back']=btn1

        btn2=ColoredButton(rgba,text='Stats', color=[1,1,1,1],bold=True,size_hint=[None,None],
                                   width=75, height=30)

        btn2.bind(on_press=self.statsscreen)
        self.buttons['stats']=btn2

        navstrip.add_widget(btn2)

        btn3=ColoredButton(bbbg,text='To Clipboard', color=bbfg,bold=True,size_hint=[None,None],
                                   width=90, height=30)

        btn3.bind(on_press=self.copy_to_clipboard)

        navstrip.add_widget(btn3)
        self.buttons['clipboard']=btn3

        btn4=ColoredButton(rgba,text='To CSV', color=[1,1,1,1],bold=True,size_hint=[None,None],
                                   width=90, height=30)

        hms=self.currapp.manager.get_screen('heatmapscreen')

        btn4.bind(on_press=hms.save_csv_dialog)

        navstrip.add_widget(btn4)
        self.buttons['savecsv']=btn4

        btn5=ColoredButton(bbbg,text='Analyse Dataset', color=bbfg,bold=True,size_hint=[None,None],
                                   width=100, height=30)

        btn5.bind(on_press=self.start_analysis_thread)

        navstrip.add_widget(btn5)
        self.buttons['analysis']=btn5

        lbl1=ColoredLabel(rhbg, color=rhfg)
        lbl1.text= self.record_header()

        navstrip.add_widget(lbl1)
        self._rh=lbl1

        butNavLeft = ColoredButton(navbg,text=' < ', color=navfg,bold=True,size_hint=[None,None],
                                   width=30, height=30)
        butNavLeft.bind(on_press=self.navLeft)
        self.buttons['navleft']=butNavLeft

        navstrip.add_widget(butNavLeft)
        navIndex=TextInput(multiline=False, size_hint=[None,None], width=60, height=30, halign='center',
                            text=str(self.start_index))
        navstrip.add_widget(navIndex)
        self._navIndex=navIndex
        self._navIndex.bind(on_text_validate=self.attempt_navigate)
        butNavRight=ColoredButton(navbg,text=' > ', color=navfg, bold = True, size_hint=[None,None],
                                  width=30, height=30)

        butNavRight.bind(on_press=self.navRight)
        self.buttons['navright']=butNavRight
        navstrip.add_widget(butNavRight)
        return navstrip

    def build_record_panel(self):
        vbox1=BoxLayout(orientation='vertical')
        hbox1=BoxLayout(orientation='horizontal', padding=5)

        self.md=ModularDataset(self,self.recordFormat,'vaers')
        for content in self.md.content:
            vbox1.add_widget(content)

        return vbox1


    def size_symptoms(self, instance, *args):
        self.ids['patient'].text_size=(self.currapp.root.width, 150)

    def styles_callback(self, key):
        if key == 'recordheader.textcolor':
            self._rh.color = get_color_from_hex(self.currapp._vc[key])
        elif key == 'recordheader.background':
            self._rh.set_bgcolor(get_color_from_hex(self.currapp._vc[key]))
        elif key == 'backbutton.background':
            col=get_color_from_hex(self.currapp._vc[key])
            self.buttons['back'].set_bgcolor(col)
            self.buttons['clipboard'].set_bgcolor(col)
        elif key == 'backbutton.textcolor':
            col=get_color_from_hex(self.currapp._vc[key])
            self.buttons['back'].set_fgcolor(col)
            self.buttons['clipboard'].set_fgcolor(col)
        elif key == 'navbutton.textcolor':
            col=get_color_from_hex(self.currapp._vc[key])
            self.buttons['navleft'].set_fgcolor(col)
            self.buttons['navright'].set_fgcolor(col)
        elif key == 'navbutton.background':
            col=get_color_from_hex(self.currapp._vc[key])
            self.buttons['navleft'].set_bgcolor(col)
            self.buttons['navright'].set_bgcolor(col)

    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.buttons = dict()
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
        self.currapp.styles.register_callback(self, 'backbutton.textcolor', self.styles_callback)
        self.currapp.styles.register_callback(self, 'backbutton.background', self.styles_callback)
        self.currapp.styles.register_callback(self, 'navbutton.textcolor', self.styles_callback)
        self.currapp.styles.register_callback(self, 'navbutton.background', self.styles_callback)
        self.currapp.styles.register_callback(self, 'recordheader.textcolor', self.styles_callback)
        self.currapp.styles.register_callback(self, 'recordheader.background', self.styles_callback)