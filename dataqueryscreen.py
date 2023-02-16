import datetime
import re

import numpy as np
from kivy.clock import Clock, mainthread
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
import threading
import time
from kivy.utils import get_color_from_hex

from dataframegridview import ColoredButton, ColoredLabel, StyledSpinnerOption
from kivy.app import App
import vaex as vx
from kivy.uix.spinner import Spinner
import traceback
from dataqueryresultscreen import DataQueryResultScreen
from fluxcapacitor import FluxCapacitor
from rangednumericfield import RangedNumericField
from regextextfield import RegexTextField


class DataQueryViewScreen(Screen):
    def goback(self, *args):
        self.manager.transition.direction = 'right'
        self.manager.current = 'mainscreen'

    @mainthread
    def popout_results_screen(self):
        currapp=App.get_running_app()
        resultscreen=currapp.manager.get_screen('resultscreen')
        resultscreen.start_index=0
        resultscreen.set_ds(currapp.ids['graphdata'])
        currapp.manager.current = 'resultscreen'

    def query_final_sanity_check(self, filterset, rs_stats):
        currapp=self.currapp
        if len(filterset) == rs_stats[1]:
            self._statusfield.text = f"No change to the size of the result set {rs_stats[1]}!"
            return None
        else:
            if len(filterset) == 0:
                self._statusfield.text = f"No results found!  Try again hotshot..."
                return None
            currapp.ids['graphdata'] = filterset.drop(['pdate', 'ydate']).to_pandas_df()
            currapp.update_status(f"{len(currapp.ids['graphdata'])} records stored in graphdata store")
            self._statusfield.text = f"{len(currapp.ids['graphdata'])} records found {' '.join(str(x) for x in rs_stats)}."

        print(' '.join(str(x) for x in rs_stats))
        self.popout_results_screen()
        return None

    def exec_vaex_query(self, *args):
        currapp=App.get_running_app()

        self._statusfield.text="Please wait..."

        filterset=currapp.df['data']
        rs_stats=['START',len(filterset)]
        # This requires some explanation.  In order to fix a bug in vaex we encountered, as well as
        # coincidentally to speed up the calculation, we break down otherwise bracketed expressions
        # into chained single equalities/inequalities, reducing the amount of memory mapping required,
        # by transforming previously logical ors into setwise ors, ditto for ands.  For this to work,
        # the order of operations needs to be changed for the emergency fields to respect operator
        # symmetry in the operator chaining.

        if self.ids['V_ID'].text != '':
            if re.match(r'^[0-9, ]+$', self.ids['V_ID'].text):
                vids: list=str(self.ids['V_ID'].text).split(',')
                if len(vids) == 1:
                    filterset = filterset.filter(f"VAERS_ID == {self.ids['V_ID'].text}", 'and')
                    print(f"filterset length {len(filterset)} after VAERS_ID == {self.ids['V_ID'].text}")
                else:
                    filterset=filterset.filter(f"VAERS_ID == {vids[0]}",'and')
                    for vid in vids[1:len(vids)]:
                        filterset = filterset.filter(f"VAERS_ID == {vid}", 'or')
                return self.query_final_sanity_check(filterset, rs_stats)

        fr=self.lorraine.filter_result()
        if fr is not None:
            filterset=fr
            rs_stats.extend(['FLUX',len(filterset)])

        fenumdays=self.ids['NUMDAYS'].filter_expression()
        fehospdays = self.ids['HOSPDAYS'].filter_expression()
        fecageyears = self.ids['CAGE_YR'].filter_expression()
        feageyears = self.ids['AGE_YRS'].filter_expression()

        if fenumdays is not None:
            filterset=filterset.filter(fenumdays,'and')
            rs_stats.extend(['NUMDAYS', len(filterset)])

        if fehospdays is not None:
            filterset=filterset.filter(fehospdays,'and')
            rs_stats.extend(['HOSPDAYS', len(filterset)])

        if fecageyears is not None:
            filterset=filterset.filter(fecageyears,'and')
            rs_stats.extend(['CAGE_YR', len(filterset)])

        if feageyears is not None:
            filterset=filterset.filter(feageyears,'and')
            rs_stats.extend(['AGE_YRS', len(filterset)])

        if self.ids['SPLTTYPE'].text != '':
            filterset=filterset.filter(f"str_contains(SPLTTYPE,'{self.ids['SPLTTYPE'].text}')",'and')
            rs_stats.extend(['RELAB', len(filterset)])

        if self.checks['relab'].state == 'down':
            filterset=filterset.filter(f"str_contains(LAB_DATA,'{self.ids['relabtxt'].text}')",'and')
            rs_stats.extend(['RELAB', len(filterset)])

        self._statusfield.text=f"{len(filterset)} records..."

        if self.checks['symptomfield'].state == 'down':
            filterset=filterset.filter(f"str_contains(SYMPTOM_TEXT,'{self.ids['symptomfield'].text}')",'and')
            rs_stats.extend(['symptomfield',len(filterset)])

        self._statusfield.text=f"{len(filterset)} records..."

        if self.checks['HISTORY'].state == 'down':
            filterset=filterset.filter(f"str_contains(HISTORY,'{self.ids['HISTORY'].text}')",'and')
            rs_stats.extend(['HISTORY',len(filterset)])

        self._statusfield.text=f"{len(filterset)} records..."

        if self.checks['OTHER_MEDS'].state == 'down':
            filterset=filterset.filter(f"str_contains(OTHER_MEDS,'{self.ids['OTHER_MEDS'].text}')",'and')
            rs_stats.extend(['OTHER_MEDS',len(filterset)])

        self._statusfield.text=f"{len(filterset)} records..."

        if self.checks['CUR_ILL'].state == 'down':
            filterset=filterset.filter(f"str_contains(CUR_ILL,'{self.ids['CUR_ILL'].text}')",'and')
            rs_stats.extend(['CUR_ILL',len(filterset)])

        self._statusfield.text=f"{len(filterset)} records..."

        if self.checks['ALLERGIES'].state == 'down':
            filterset=filterset.filter(f"str_contains(ALLERGIES,'{self.ids['ALLERGIES'].text}')",'and')
            rs_stats.extend(['ALLERGIES',len(filterset)])

        self._statusfield.text=f"{len(filterset)} records..."

        if self.checks['SEX'].state == 'down':
            filterset=filterset.filter(f"SEX=='{self.spinners['SEX'].text}'",'and')
            rs_stats.extend(['SEX',len(filterset)])

        self._statusfield.text=f"{len(filterset)} records..."

        if self.checks['VAX_TYPE'].state == 'down':
            filterset=filterset.filter(f"VAX_TYPE=='{self.spinners['VAX_TYPE'].text}'",'and')
            rs_stats.extend(['VAX_TYPE',len(filterset)])

        self._statusfield.text=f"{len(filterset)} records..."

        if self.checks['VAX_MANU'].state == 'down':
            filterset=filterset.filter(f"VAX_MANU=='{self.spinners['VAX_MANU'].text}'",'and')
            rs_stats.extend(['VAX_MANU',len(filterset)])

        self._statusfield.text=f"{len(filterset)} records..."

        if self.checks['VAX_DOSE_SERIES'].state == 'down':
            filterset=filterset.filter(f"VAX_DOSE_SERIES=='{self.spinners['VAX_DOSE_SERIES'].text}'",'and')
            rs_stats.extend(['VAX_DOSE_SERIES',len(filterset)])

        self._statusfield.text=f"{len(filterset)} records..."

        fevlot=self.ids['VAX_LOT'].filter_expression()
        if fevlot is not None:
            filterset = filterset.filter(fevlot, 'and')
            rs_stats.extend(['VAX_LOT',len(filterset)])

        self._statusfield.text=f"{len(filterset)} records..."

        if self.ids['STATE'].text != '':
            filterset=filterset.filter(f"str_upper(STATE)=='{str.upper(self.ids['STATE'].text)}'",'and')
            rs_stats.extend(['STATE',len(filterset)])

        self._statusfield.text=f"{len(filterset)} records..."

        if self.ids['symptomregex'].text != '':
            symptom =self.ids['symptomregex'].text
            fset = currapp.df['symptoms'].filter(f"str_contains(str_lower(SYMPTOM1),'{symptom}')")
            self._statusfield.text=f"Identifying records matching symptom regex: {len(fset)}"
            fset = fset.filter(f"str_contains(str_lower(SYMPTOM2),'{symptom}')", 'or')
            self._statusfield.text = f"Identifying records matching symptom regex: {len(fset)}"
            fset = fset.filter(f"str_contains(str_lower(SYMPTOM3),'{symptom}')", 'or')
            self._statusfield.text = f"Identifying records matching symptom regex: {len(fset)}"
            fset = fset.filter(f"str_contains(str_lower(SYMPTOM4),'{symptom}')", 'or')
            self._statusfield.text = f"Identifying records matching symptom regex: {len(fset)}"
            fset = fset.filter(f"str_contains(str_lower(SYMPTOM5),'{symptom}')", 'or')
            self._statusfield.text = f"Identifying records matching symptom regex: {len(fset)}"

            reports=sorted(fset.VAERS_ID.unique())

            vid = filterset.VAERS_ID.tolist()
            s = reports[0]
            e = reports[-1]
            r = e - s + 1
            b = 1 + r // 100  # ie 1 bin of 100 for 99 records
            print(f"s={s},e={e},r={r},b={b}")
            sets = [set() for i in range(b + 1)]
            for id in reports:
                sets[(id - s) // b].add(id)

            start_time = time.perf_counter()
            print('List of list enumeration...')
            idx = []
            for i, y in enumerate(vid):
                try:
                    if (y >= s) and (y <= e) and (y in sets[(y - s) // b]):
                        idx.append(i)
                except Exception as ex:
                    print(f"Exception caught at {i}, {y}, {y - s}//{b}")

            print("taking results...")
            filterset = filterset.take(idx)
            end_time = time.perf_counter()
            rs_stats.extend(['SYMPTOM',len(filterset)])

        self._statusfield.text=f"{len(filterset)} records..."

        if self.ids['daterange'].text != '':
            drtext=self.ids['daterange'].text
            re_search=re.compile(r'^(\d{4})(\d{2})(\d{2})-(\d{4})(\d{2})(\d{2})$')
            re_match=re_search.fullmatch(drtext)
            if re_match:
                try:
                    startdate=np.datetime64(f"{re_match.group(1)}-{re_match.group(2)}-{re_match.group(3)}")
                    enddate=np.datetime64(f"{re_match.group(4)}-{re_match.group(5)}-{re_match.group(6)}")
                    filterset = filterset.filter(filterset.pdate >= startdate, 'and' )
                    filterset = filterset.filter(filterset.pdate <= enddate, 'and' )
                    rs_stats.extend(['DATERANGE', len(filterset)])
                except Exception as ex:
                    print(ex)
            else:
                print(f"{drtext} did not match {re_search}")
        else:
            print(f"daterange is {self.ids['daterange'].text}")
        self._statusfield.text=f"{len(filterset)} records..."

        try:
            return self.query_final_sanity_check(filterset, rs_stats)
        except Exception as ex:
            print("Exception triggered")
            print(ex)

    def execute_query(self, *args):
        self.currapp.start_thread_once(name='execute query', target=self.exec_vaex_query)

    def set_checkbox(self,cbname,cbstate):
        print(f"Setting {cbname} to {cbstate}")
        self.checks[cbname].state=cbstate

    def set_textinput(self,tbname,tbval):
        print(f"Setting {tbname} to {tbval}")
        self.ids[tbname].text=tbval

    def set_spinner_on(self,spname,sptext):
        self.spinners[spname].text=sptext
        self.spinners[spname].state='down'

    def spinner_on_set(self, instance: Spinner, *args):
        if instance.text != '':
            spinnerkey=next(i for i in self.spinners.items() if i[1] is instance)[0]
            self.checks[spinnerkey].state='down'

    def build_spinners(self,*args):
        myapp=App.get_running_app()
        spinbg=myapp._vc['spinner.background']
        spinfg = myapp._vc['spinner.textcolor']
        if not hasattr(self,'spinners'):
            self.spinners=dict()
            self.spinners['SEX'] = Spinner(size_hint_x=0.3, size_hint_y = None, height=60,
                                           option_cls=StyledSpinnerOption, background_normal='',
                                           background_color=spinbg, color=spinfg)
            self.spinners['VAX_TYPE']=Spinner(size_hint_x=0.3, size_hint_y = None, height=60,
                                              option_cls=StyledSpinnerOption, background_normal='',
                                              background_color=spinbg, color=spinfg)
            self.spinners['VAX_DOSE_SERIES']=Spinner(size_hint_x=0.3, size_hint_y = None, height=60,
                                                     option_cls=StyledSpinnerOption, background_normal='',
                                                     background_color=spinbg, color=spinfg)
            self.spinners['VAX_MANU']=Spinner(size_hint_x=0.3, size_hint_y = None, height=60,
                                              option_cls=StyledSpinnerOption, background_normal='',
                                              background_color=spinbg, color=spinfg)
            for s in self.spinners.values():
                s.bind(text=self.spinner_on_set)
        if 'data' not in myapp.df:
            Clock.schedule_once(self.build_spinners, 5)
        else:
            if 'VAX_TYPE' in myapp.df['data'].column_names:
                vaxtypevals=sorted(myapp.df['data']['VAX_TYPE'].unique(dropmissing=True))
                vaxmanuvals = sorted(myapp.df['data']['VAX_MANU'].unique(dropmissing=True))
                vaxdoseval=sorted(myapp.df['data']['VAX_DOSE_SERIES'].unique(dropmissing=True))
                sexspinval=sorted(myapp.df['data']['SEX'].unique(dropmissing=True))
                self.spinners['SEX'].values=sexspinval
                self.spinners['VAX_TYPE'].values=vaxtypevals
                self.spinners['VAX_MANU'].values = vaxmanuvals
                self.spinners['VAX_DOSE_SERIES'].values=vaxdoseval
            else:
                Clock.schedule_once(self.build_spinners,2)

    @mainthread
    def reset_form(self):
        print("Reset form called")

        # boolcolumns = ['deaths', 'hosp', 'disabled', 'emergency']
        # for b in boolcolumns:
        #     self.checks[f"{b}2"].state='down'
        #     self.checks[f"{b}0"].state = 'normal'
        #     self.checks[f"{b}1"].state = 'normal'

        for field in ['SEX','VAX_MANU', 'VAX_TYPE','VAX_DOSE_SERIES']:
            self.spinners[field].text=''
            self.checks[field].state='normal'

        for field in ['symptomfield', 'CUR_ILL','HISTORY', 'OTHER_MEDS', 'ALLERGIES']:
            self.checks[field].state='normal'
            self.ids[field].text=''

        self.checks['relab'].state = 'normal'
        self.ids['relabtxt'].text = ''
        self.ids['STATE'].text=''
        #self.ids['VAX_LOT'].text = ''
        #self.checks['VAX_LOT'].state = 'normal'
        currapp=App.get_running_app()
        if hasattr(currapp,'rangedfields'):
            for fld in currapp.rangedfields.values():
                fld.reset_form()

        if hasattr(currapp,'regexfields'):
            for fld in currapp.regexfields.values():
                fld.reset_form()

    def style_callback(self, key):
        if key == 'button.background':
            bgcolor=get_color_from_hex(self.currapp._vc[key])
            for node in self.walk():
                if isinstance(node,ColoredButton):
                    node.set_bgcolor(bgcolor)
        elif key == 'button.textcolor':
            fgcolor=get_color_from_hex(self.currapp._vc[key])
            for node in self.walk():
                if isinstance(node, ColoredButton):
                    node.set_fgcolor(fgcolor)
        elif key == 'label.textcolor':
            for node in self.walk():
                if isinstance(node, ColoredLabel):
                    node.color = get_color_from_hex(self.currapp._vc[key])
        elif key == 'label.background':
            for node in self.walk():
                if isinstance(node, ColoredLabel):
                    node.set_bgcolor(get_color_from_hex(self.currapp._vc[key]))
        elif key == 'textbox.textcolor':
            for node in self.walk():
                if isinstance(node, TextInput):
                    node.color = get_color_from_hex(self.currapp._vc[key])
        elif key == 'textbox.background':
            print("Updating background color")
            for node in self.walk():
                if isinstance(node, TextInput):
                    node.background_color = get_color_from_hex(self.currapp._vc[key])
        elif key == 'togglebutton.background':
            for node in self.walk():
                if isinstance(node,ToggleButton):
                    node.background_color = get_color_from_hex(self.currapp._vc[key])
        elif key == 'spinner.background':
            # Spinners are notified of style changes elsewhere for the SpinnerOptions
            # However we must style the closed spinners themselves directly.
            col=get_color_from_hex(self.currapp._vc[key])
            for node in self.spinners.values():
                node.background_color=col
        elif key == 'spinner.textcolor':
            col=get_color_from_hex(self.currapp._vc[key])
            for node in self.spinners.values():
                node.color=col


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.checks=dict()
        self.build_spinners()
        vbox=BoxLayout(orientation='vertical', size_hint=(1, None))
        vbox.bind(minimum_height=vbox.setter('height'))

        hbox1=BoxLayout(orientation='horizontal', size_hint = [1, None], height=50)
        currapp=App.get_running_app()
        rgba = get_color_from_hex(currapp._vc['label.background'])
        textcolor = currapp._vc['label.textcolor']
        brgba = get_color_from_hex(currapp._vc['button.background'])
        bcolor= currapp._vc['button.textcolor']
        cboxcol= get_color_from_hex(currapp._vc['togglebutton.background'])
        tboxbg = get_color_from_hex(currapp._vc['textbox.background'])
        tboxfg = get_color_from_hex(currapp._vc['textbox.textcolor'])

        btn1=ColoredButton(brgba,text="Go Back", size_hint= [None,None], width=60, height=50, color=bcolor)
        btn1.bind(on_press=self.goback)
        hbox1.add_widget(btn1)
        hbox1.add_widget(Label(size_hint_y=None, height=50))
        vbox.add_widget(hbox1)

        hbox1 = GridLayout(size_hint=[1, None], height=400, cols=5)
        self.marty = FluxCapacitor('DIED','fluxdeath',['Yes', 'No', "Don't Care"],
                              ["{name} == 'Y'", "~str_contains({name},'^Y$')", None], [], fluxtext='Deaths')

        self.jennifer = FluxCapacitor('HOSPITAL','fluxhosp',['Yes', 'No', "Don't Care"],
                              ["{name} == 'Y'", "~str_contains({name},'^Y$')", None], [], fluxtext='Hospitalisations')

        self.doc = FluxCapacitor('DISABLE','fluxdisable',['Yes', 'No', "Don't Care"],
                              ["{name} == 'Y'", "~str_contains({name},'^Y$')", None], [], fluxtext='Disabled')

        self.needles = FluxCapacitor('L_THREAT','fluxthreat',['Yes', 'No', "Don't Care"],
                              ["{name} == 'Y'", "~str_contains({name},'^Y$')", None], [], fluxtext='Life Threatening')

        self.jailbird = FluxCapacitor('ER_VISIT','fluxer1',['Yes', 'No', "Don't Care"],
                              ["{name} == 'Y'", "~str_contains({name},'^Y$')", None], [], fluxtext='ER Visit (VAERS 1)')

        self.joey = FluxCapacitor('ER_ED_VISIT','fluxer2',['Yes', 'No', "Don't Care"],
                              ["{name} == 'Y'", "~str_contains({name},'^Y$')", None], [], fluxtext='ER Visit (VAERS 2+)')

        self.strickland = FluxCapacitor('OFC_VISIT','fluxofc',['Yes', 'No', "Don't Care"],
                              ["{name} == 'Y'", "~str_contains({name},'^Y$')", None], [], fluxtext='Office/Clinic visit')

        self.george = FluxCapacitor('BIRTH_DEFECT','fluxbirth',['Yes', 'No', "Don't Care"],
                              ["{name} == 'Y'", "~str_contains({name},'^Y$')", None], [], fluxtext='Birth Defect?')

        self.lorraine = FluxCapacitor('SYMPTOM_TEXT','fluxlen',['Short', 'Long', "Don't Care"],
                              ["str_len(SYMPTOM_TEXT) < 2000", "str_len(SYMPTOM_TEXT) >= 2000", None], [],
                            fluxtext='Level of detail?')

        #self.compounded = FluxCapacitor('ER_ED_VISIT','fluxer',['Yes', 'No', "Don't Care"],
        #                      [["ER_ED_VISIT== 'Y'", "ER_VISIT== 'Y'"],
        #                       ["~str_contains(ER_ED_VISIT,'^Y$')", "~str_contains(ER_VISIT,'^Y$')"],
        #                          None], [],
        #                    fluxtext='Emergency Room Visits?', compoundop='||')

        hbox1.add_widget(self.marty)
        hbox1.add_widget(self.jennifer)
        hbox1.add_widget(self.doc)
        hbox1.add_widget(self.needles)
        hbox1.add_widget(self.jailbird)
        hbox1.add_widget(self.joey)
        hbox1.add_widget(self.strickland)
        hbox1.add_widget(self.george)
        hbox1.add_widget(self.lorraine)
        self.flux=dict()
        self.flux['deaths']=self.marty
        self.flux['hospital']=self.jennifer
        self.flux['disable']=self.doc
        self.flux['lthreat']=self.needles
        self.flux['er0']=self.jailbird
        self.flux['er1']=self.joey
        #hbox1.add_widget(self.compounded)
        self.jennifer.notify_downstream(self.marty)
        self.doc.notify_downstream(self.jennifer)
        self.needles.notify_downstream(self.doc)
        self.jailbird.notify_downstream(self.needles)
        self.joey.notify_downstream(self.jailbird)
        self.strickland.notify_downstream(self.joey)
        self.george.notify_downstream(self.strickland)
        self.lorraine.notify_downstream(self.george)
        #self.compounded.notify_downstream(self.lorraine)
        vbox.add_widget(hbox1)

        glayout = GridLayout(cols=6, size_hint_x=1, size_hint_y=None, padding=5, height=60)

        # Lab data
        hbox2 = BoxLayout(orientation='horizontal', size_hint_x=1, size_hint_y=None, padding=5, height=60)
        label1 = ColoredLabel(rgba, size_hint_x=0.2, size_hint_y=None, height=50, color=textcolor,
                            text="Search lab text?"
                            )
        glayout.add_widget(label1)
        cbox = ToggleButton(size_hint_y=None, height=25, size_hint_x=None, width=40,
                             allow_no_selection=True, background_color=cboxcol)
        glayout.add_widget(cbox)
        self.checks['relab']=cbox
        tinput=TextInput(size_hint_x=0.2, size_hint_y = None, height=50, foreground_color=tboxfg, background_color=tboxbg)
        glayout.add_widget(tinput)
        self.ids['relabtxt']=tinput

        # Symptom text
        label1 = ColoredLabel(rgba, size_hint_x=0.2, size_hint_y=None, height=50, color=textcolor,
                            text="Search symptom text?"
                            )
        glayout.add_widget(label1)
        cbox = ToggleButton(size_hint_y=None, height=25, size_hint_x=None, width=40,
                            allow_no_selection=True, background_color=cboxcol)
        glayout.add_widget(cbox)
        self.checks['symptomfield']=cbox
        tinput = TextInput(size_hint_x=0.2, size_hint_y=None, height=50, foreground_color=tboxfg, background_color=tboxbg)
        self.ids['symptomfield']=tinput
        glayout.add_widget(tinput)
        # Grid Layout 1
        #hbox2.add_widget(glayout)
        vbox.add_widget(glayout)

        # Textual fields continue
        glayout = GridLayout(cols=6, size_hint_x=1, size_hint_y=None, padding=5, height=60)

        hbox2 = BoxLayout(orientation='horizontal', size_hint_x=1, size_hint_y=None, padding=5, height=60)

        # Medications
        label1 = ColoredLabel(rgba, size_hint_x=0.2, size_hint_y=None, height=50, color=textcolor,
                            text="Search medications?"
                            )
        glayout.add_widget(label1)
        cbox = ToggleButton(size_hint_y=None, height=25, size_hint_x=None, width=40,
                            allow_no_selection=True, background_color=cboxcol)
        glayout.add_widget(cbox)
        self.checks['OTHER_MEDS']=cbox
        tinput = TextInput(size_hint_x=0.2, size_hint_y=None, height=50, foreground_color=tboxfg, background_color=tboxbg)
        self.ids['OTHER_MEDS']=tinput
        glayout.add_widget(tinput)

        # History
        label1 = ColoredLabel(rgba, size_hint_x=0.2, size_hint_y=None, height=50, color=textcolor,
                            text="Search pre-existing?"
                            )
        glayout.add_widget(label1)
        cbox = ToggleButton(size_hint_y=None, height=25, size_hint_x=None, width=40,
                            allow_no_selection=True, background_color=cboxcol)
        glayout.add_widget(cbox)
        self.checks['HISTORY']=cbox
        tinput = TextInput(size_hint_x=0.2, size_hint_y=None, height=50, foreground_color=tboxfg, background_color=tboxbg)
        self.ids['HISTORY']=tinput
        glayout.add_widget(tinput)

        # Grid Layout 2
        #hbox2.add_widget(glayout)
        vbox.add_widget(glayout)

        # Textual fields continue
        glayout = GridLayout(cols=6, size_hint_x=1, size_hint_y = None, padding=5, height=60)
        glayout.bind(minimum_height=self.setter('height'))
        hbox2 = BoxLayout(orientation='horizontal', size_hint_x=1, size_hint_y=None, padding=5, height=60)

        # Medications
        label1 = ColoredLabel(rgba, size_hint_x=0.2, size_hint_y=None, height=50,
                            text="Search existing?", color=textcolor
                            )
        glayout.add_widget(label1)
        cbox = ToggleButton(size_hint_y=None, height=25, size_hint_x=None, width=40,
                            allow_no_selection=True, background_color=cboxcol)
        glayout.add_widget(cbox)
        self.checks['CUR_ILL']=cbox
        tinput = TextInput(size_hint_x=0.2, size_hint_y=None, height=50, foreground_color=tboxfg, background_color=tboxbg)
        self.ids['CUR_ILL']=tinput
        glayout.add_widget(tinput)

        # Allergies
        label1 = ColoredLabel(rgba, size_hint_x=0.2, size_hint_y=None, height=50, color=textcolor,
                            text="Search allergies?"
                            )
        glayout.add_widget(label1)
        cbox = ToggleButton(size_hint_y=None, height=25, size_hint_x=None, width=40,
                            allow_no_selection=True, background_color=cboxcol)
        glayout.add_widget(cbox)
        self.checks['ALLERGIES']=cbox
        tinput = TextInput(size_hint_x=0.2, size_hint_y=None, height=50, foreground_color=tboxfg, background_color=tboxbg)
        self.ids['ALLERGIES']=tinput
        glayout.add_widget(tinput)

        # Grid Layout 3
        #hbox2.add_widget(glayout)
        vbox.add_widget(glayout)
        # Spinners begin
        glayout = GridLayout(cols=6, size_hint_x=1, size_hint_y=None, padding=11, height=60)
        hbox2 = BoxLayout(orientation='horizontal', size_hint_x=1, size_hint_y=None, padding=5, height=60)

        # Sex
        label1 = ColoredLabel(rgba, size_hint_x=0.2, size_hint_y=None, height=50, color=textcolor,
                              text='Sex'
                              )

        glayout.add_widget(label1)
        #hbox2.add_widget(glayout)
        cbox = ToggleButton(size_hint_y=None, height=25, size_hint_x=None, width=40,
                            allow_no_selection=True, background_color=cboxcol)
        self.checks['SEX']=cbox
        glayout.add_widget(cbox)

        glayout.add_widget(self.spinners['SEX'])
        # Vax Dose
        label1 = ColoredLabel(rgba, size_hint_x=0.2, size_hint_y=None, height=50, color=textcolor,
                              text='Dose'
                              )
        glayout.add_widget(label1)
        cbox = ToggleButton(size_hint_y=None, height=25, size_hint_x=None, width=40,
                            allow_no_selection=True, background_color=cboxcol)
        self.checks['VAX_DOSE_SERIES']=cbox
        glayout.add_widget(cbox)
        glayout.add_widget(self.spinners['VAX_DOSE_SERIES'])

        # Grid Layout 4
        vbox.add_widget(glayout)
        # Spinners continue
        glayout = GridLayout(cols=6, size_hint_x=1, size_hint_y=None, padding=11, height=60)
        glayout.bind(minimum_height=self.setter('height'))
        hbox2 = BoxLayout(orientation='horizontal', size_hint_x=1, size_hint_y=None, padding=5, height=60)

        # Vax Type
        label1 = ColoredLabel(rgba, size_hint_x=0.2, size_hint_y=None, height=50, color=textcolor,
                              text='Vax Type'
                              )
        glayout.add_widget(label1)
        cbox = ToggleButton(size_hint_y=None, height=25, size_hint_x=None, width=40,
                            allow_no_selection=True, background_color=cboxcol)
        self.checks['VAX_TYPE']=cbox
        glayout.add_widget(cbox)
        glayout.add_widget(self.spinners['VAX_TYPE'])
        # Vax Manufacturer
        label1 = ColoredLabel(rgba, size_hint_x=0.2, size_hint_y=None, height=50, color=textcolor,
                              text='Vax Manufacturer'
                              )
        glayout.add_widget(label1)
        cbox = ToggleButton(size_hint_y=None, height=25, size_hint_x=None, width=40,
                            allow_no_selection=True, background_color=cboxcol)
        self.checks['VAX_MANU']=cbox
        glayout.add_widget(cbox)
        glayout.add_widget(self.spinners['VAX_MANU'])

        vbox.add_widget(glayout)

        cbox = ToggleButton(size_hint_y=None, height=25, size_hint_x=None, width=40,
                            allow_no_selection=True, background_color=cboxcol)

        self.checks['VAX_LOT']=cbox
        #self.ids['VAX_LOT']=TextInput(size_hint_y=None, height=50, foreground_color=tboxfg, background_color=tboxbg)
        self.ids['VAX_LOT']=RegexTextField('VAX_LOT', size_hint_x = 0.4)
        currapp.regexfields['regexbatch']=self.ids['VAX_LOT']
        #hbox1.add_widget(self.ids['regexbatch'])

        vl=self.ids['VAX_LOT']

        self.ids['STATE']=TextInput(size_hint_y=None, height=50, foreground_color=tboxfg,
                                    background_color=tboxbg, size_hint_x=0.4)

        hbox1=BoxLayout(orientation='horizontal', size_hint_y=None, height=60, padding=11)
        hbox1.add_widget(ColoredLabel(rgba, size_hint_x=0.2, size_hint_y=None, height=50,
                                      text='Vax Lot:', color=textcolor))

        hbox1.add_widget(vl)
        hbox1.add_widget(ColoredLabel(rgba, size_hint_x=0.2, size_hint_y=None, height=50,
                                      text='State:', color=textcolor))
        hbox1.add_widget(self.ids['STATE'])
        vbox.add_widget(hbox1)

        hbox1=BoxLayout(orientation='horizontal', size_hint_y=None, height=60, padding=11)
        hbox1.add_widget(
            ColoredLabel(rgba, size_hint_x=0.25, size_hint_y=None, height=50, text='Days of onset:', color=textcolor))

        currapp.rangedfields['NUMDAYS']=RangedNumericField('NUMDAYS', size_hint_x = 0.2)
        hbox1.add_widget(currapp.rangedfields['NUMDAYS'])
        self.ids['NUMDAYS']=currapp.rangedfields['NUMDAYS']

        hbox1.add_widget(
            ColoredLabel(rgba, size_hint_x=0.25, size_hint_y=None, height=50, text='Days hospitalised:', color=textcolor))

        currapp.rangedfields['HOSPDAYS']=RangedNumericField('HOSPDAYS', size_hint_x = 0.2)
        hbox1.add_widget(currapp.rangedfields['HOSPDAYS'])
        self.ids['HOSPDAYS']=currapp.rangedfields['HOSPDAYS']

        vbox.add_widget(hbox1)

        hbox1=BoxLayout(orientation='horizontal', size_hint_y=None, height=60, padding=11)
        hbox1.add_widget(
            ColoredLabel(rgba, size_hint_x=0.25, size_hint_y=None, height=50, text='Age (CAGE_YR):', color=textcolor))

        currapp.rangedfields['CAGE_YR']=RangedNumericField('CAGE_YR', size_hint_x = 0.2)
        hbox1.add_widget(currapp.rangedfields['CAGE_YR'])
        self.ids['CAGE_YR']=currapp.rangedfields['CAGE_YR']

        hbox1.add_widget(
            ColoredLabel(rgba, size_hint_x=0.25, size_hint_y=None, height=50, text='Age (AGE_YRS):', color=textcolor))

        currapp.rangedfields['AGE_YRS']=RangedNumericField('AGE_YRS', size_hint_x = 0.2)
        hbox1.add_widget(currapp.rangedfields['AGE_YRS'])
        self.ids['AGE_YRS']=currapp.rangedfields['AGE_YRS']

        vbox.add_widget(hbox1)

        hbox1=BoxLayout(orientation='horizontal', size_hint_y=None, height=60, padding=11)
        self.ids['symptomregex']=TextInput(size_hint_y=None, height=50, foreground_color=tboxfg,
                                            background_color=tboxbg, size_hint_x=0.4)
        hbox1.add_widget(ColoredLabel(rgba, size_hint_x=0.2, size_hint_y=None, height=50,
                                      text='Symptom regex:', color=textcolor))
        hbox1.add_widget(self.ids['symptomregex'])
        vbox.add_widget(hbox1)

        hbox1=BoxLayout(orientation='horizontal', size_hint_y=None, height=60, padding=11)
        self.ids['daterange']=TextInput(size_hint_y=None, height=50, foreground_color=tboxfg,
                                            background_color=tboxbg, size_hint_x=0.4)
        hbox1.add_widget(ColoredLabel(rgba, size_hint_x=0.2, size_hint_y=None, height=50,
                                      text='Date range:', color=textcolor))
        hbox1.add_widget(self.ids['daterange'])
        vbox.add_widget(hbox1)

        hbox1=BoxLayout(orientation='horizontal', size_hint_y=None, height=60, padding=11)
        self.ids['V_ID']=TextInput(size_hint_y=None, height=50, foreground_color=tboxfg,
                                   background_color=tboxbg, size_hint_x=0.4)
        hbox1.add_widget(ColoredLabel(rgba, size_hint_x=0.2, size_hint_y=None, height=50,
                                      text='VAERS IDs:', color=textcolor))
        hbox1.add_widget(self.ids['V_ID'])
        vbox.add_widget(hbox1)

        hbox1=BoxLayout(orientation='horizontal', size_hint_y=None, height=60, padding=11)
        self.ids['SPLTTYPE']=TextInput(size_hint_y=None, height=50, foreground_color=tboxfg,
                                        background_color=tboxbg, size_hint_x=0.4)
        hbox1.add_widget(ColoredLabel(rgba, size_hint_x=0.2, size_hint_y=None, height=50,
                                      text='Report number:', color=textcolor))
        hbox1.add_widget(self.ids['SPLTTYPE'])
        vbox.add_widget(hbox1)

        #hbox1=BoxLayout(orientation='horizontal', size_hint_y=None, height=60, padding=11)
        #hbox1.add_widget(
         #   ColoredLabel(rgba, size_hint_x=0.25, size_hint_y=None, height=55, text='Regex batch:', color=textcolor))


        #vbox.add_widget(hbox1)

        statusfield=Label(size_hint=[1,None], height=40, text="Ready")
        self._statusfield=statusfield
        vbox.add_widget(statusfield)
        btn1=ColoredButton(brgba,text="Submit Query", size_hint_y = None, height=50, color=bcolor)
        vbox.add_widget(btn1)
        btn1.bind(on_press=self.execute_query)
        self.currapp=currapp
        currapp.styles.register_callback(self,'button.background', self.style_callback)
        currapp.styles.register_callback(self,'button.textcolor', self.style_callback)
        currapp.styles.register_callback(self,'label.background', self.style_callback)
        currapp.styles.register_callback(self,'label.textcolor', self.style_callback)
        currapp.styles.register_callback(self,'textbox.background', self.style_callback)
        currapp.styles.register_callback(self,'textbox.textcolor', self.style_callback)
        currapp.styles.register_callback(self,'togglebutton.background', self.style_callback)
        currapp.styles.register_callback(self,'spinner.background', self.style_callback)
        currapp.styles.register_callback(self,'spinner.textcolor', self.style_callback)

        sv=ScrollView(size_hint=(1, None), size=(Window.width, Window.height))
        sv.add_widget(vbox)
        self.add_widget(sv)
        self._sv = sv

# rgb(26, 32, 170) | HEX #1A20AA
# rgb(86, 202, 184) | HEX #56CAB8
# rgb(0, 251, 250) | HEX #00FBFA
# rgb(31, 83, 77) | HEX #1F534D
# rgb(0, 51, 52) | HEX #003334
# rgb(31, 247, 252) | HEX #1FF7FC
# rgb(3, 248, 252) | HEX #03F8FC
# rgb(0, 102, 96) | HEX #006660
# rgb(0, 16, 15) | HEX #00100F