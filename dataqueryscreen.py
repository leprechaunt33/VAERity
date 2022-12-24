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
from dataframegridview import ColoredButton, ColoredLabel
from kivy.app import App
import vaex as vx
from kivy.uix.spinner import Spinner
import traceback
from dataqueryresultscreen import DataQueryResultScreen


class DataQueryViewScreen(Screen):
    def goback(self, *args):
        self.manager.transition.direction = 'right'
        self.manager.current = 'mainscreen'

    @mainthread
    def popout_results_screen(self):
        currapp=App.get_running_app()
        resultscreen=currapp.manager.get_screen('resultscreen')
        resultscreen.set_ds(currapp.ids['graphdata'])
        currapp.manager.current = 'resultscreen'

    def exec_vaex_query(self, *args):
        currapp=App.get_running_app()

        self._statusfield.text="Please wait..."
        print(f"VAX_LOT is {self.ids['VAX_LOT'].text}")
        print(f"STATE is {self.ids['STATE'].text}")

        filterset=currapp.df['data']
        rs_stats=['START',len(filterset)]
        # This requires some explanation.  In order to fix a bug in vaex we encountered, as well as
        # coincidentally to speed up the calculation, we break down otherwise bracketed expressions
        # into chained single equalities/inequalities, reducing the amount of memory mapping required,
        # by transforming previously logical ors into setwise ors, ditto for ands.  For this to work,
        # the order of operations needs to be changed for the emergency fields to respect operator
        # symmetry in the operator chaining.
        # TODO: Test all use cases to ensure correct result set filtering was applied.
        if self.checks['emergency0'].state == 'down':
            filterset=filterset.filter("ER_VISIT == 'Y'","or")
            rs_stats.extend(['ER_VISIT',len(filterset)])
            filterset=filterset.filter("ER_ED_VISIT == 'Y'","or")
            rs_stats.extend(['ER_ED_VISIT',len(filterset)])

        if self.checks['deaths0'].state == 'down':
            filterset=filterset.filter("DIED == 'Y'",'or')
            rs_stats.extend(['DEATHS0',len(filterset)])
        elif self.checks['deaths1'].state == 'down':
            filterset=filterset.filter("DIED != 'Y'",'or')
            rs_stats.extend(['DEATHS1',len(filterset)])

        self._statusfield.text=f"{len(filterset)} records..."

        if self.checks['hosp0'].state == 'down':
            filterset=filterset.filter("HOSPITAL == 'Y'",'or')
            rs_stats.extend(['HOSP0',len(filterset)])
        elif self.checks['hosp1'].state == 'down':
            filterset=filterset.filter("HOSPITAL != 'Y'",'or')
            rs_stats.extend(['HOSP1',len(filterset)])

        self._statusfield.text=f"{len(filterset)} records..."

        if self.checks['disabled0'].state == 'down':
            filterset=filterset.filter("DISABLE == 'Y'",'or')
            rs_stats.extend(['DISABLED0',len(filterset)])
        elif self.checks['disabled1'].state == 'down':
            filterset=filterset.filter("DiSABLE != 'Y'",'or')
            rs_stats.extend(['DISABLED1',len(filterset)])

        if self.checks['emergency1'].state == 'down':
            filterset=filterset.filter("ER_VISIT != 'Y'", 'amd').filter("ER_ED_VISIT != 'Y'",'amd')
            rs_stats.extend(['EMERGENCY1',len(filterset)])

        self._statusfield.text=f"{len(filterset)} records..."

        if self.checks['relab'].state == 'down':
            filterset=filterset.filter(f"str_contains(LAB_DATA,'{self.ids['relabtxt'].text}')",'and')
            rs_stats.extend(['RELAB', len(filterset)])

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

        if self.checks['CUR_ILL'].state == 'down':
            filterset=filterset.filter(f"str_contains(CUR_ILL,'{self.ids['CUR_ILL'].text}')",'and')
            rs_stats.extend(['CUR_ILL',len(filterset)])

        self._statusfield.text=f"{len(filterset)} records..."

        if self.checks['ALLERGIES'].state == 'down':
            filterset=filterset.filter(f"str_contains(ALLERGIES,'{self.ids['ALLERGIES'].text}')",'and')
            rs_stats.extend(['ALLERGIES',len(filterset)])

        if self.checks['SEX'].state == 'down':
            filterset=filterset.filter(f"SEX=='{self.spinners['SEX'].text}'",'and')
            rs_stats.extend(['SEX',len(filterset)])

        self._statusfield.text=f"{len(filterset)} records..."

        if self.checks['VAX_TYPE'].state == 'down':
            filterset=filterset.filter(f"VAX_TYPE=='{self.spinners['VAX_TYPE'].text}'",'and')
            rs_stats.extend(['VAX_TYPE',len(filterset)])

        if self.checks['VAX_MANU'].state == 'down':
            filterset=filterset.filter(f"VAX_MANU=='{self.spinners['VAX_MANU'].text}'",'and')
            rs_stats.extend(['VAX_MANU',len(filterset)])

        if self.checks['VAX_DOSE_SERIES'].state == 'down':
            filterset=filterset.filter(f"VAX_DOSE_SERIES=='{self.spinners['VAX_DOSE_SERIES'].text}'",'and')
            rs_stats.extend(['VAX_DOSE_SERIES',len(filterset)])

        if self.checks['VAX_LOT'].state == 'down':
            filterset=filterset.filter(f"str_upper(VAX_LOT)=='{str.upper(self.ids['VAX_LOT'].text)}'",'and')
            rs_stats.extend(['VAX_LOT',len(filterset)])

        if self.ids['STATE'].text != '':
            filterset=filterset.filter(f"str_upper(STATE)=='{str.upper(self.ids['STATE'].text)}'",'and')
            rs_stats.extend(['STATE',len(filterset)])

        self._statusfield.text=f"{len(filterset)} records..."

        try:
            if len(filterset) == rs_stats[1]:
                self._statusfield.text = f"No change to the size of the result set {rs_stats[1]}!"
                return None
            else:
                currapp.ids['graphdata']=filterset.drop(['pdate','ydate']).to_pandas_df()
                currapp.update_status(f"{len(currapp.ids['graphdata'])} records stored in graphdata store")
                self._statusfield.text=f"{len(currapp.ids['graphdata'])} records found {' '.join(str(x) for x in rs_stats)}."

            print(' '.join(str(x) for x in rs_stats))
            print(f"VAX_LOT is {self.ids['VAX_LOT'].text}")
            print(f"STATE is {self.ids['STATE'].text}")
            self.popout_results_screen()
        except Exception as ex:
            print("Exception triggered")
            print(ex)

    def execute_query(self, *args):
        print(f"VAX_LOT is {self.ids['VAX_LOT'].text}")
        print(f"STATE is {self.ids['STATE'].text}")
        threading.Thread(target=self.exec_vaex_query).start()

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
        if not hasattr(self,'spinners'):
            self.spinners=dict()
            self.spinners['SEX'] = Spinner(size_hint_x=0.3, size_hint_y = None, height=60)
            self.spinners['VAX_TYPE']=Spinner(size_hint_x=0.3, size_hint_y = None, height=60)
            self.spinners['VAX_DOSE_SERIES']=Spinner(size_hint_x=0.3, size_hint_y = None, height=60)
            self.spinners['VAX_MANU']=Spinner(size_hint_x=0.3, size_hint_y = None, height=60)
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
        #traceback.print_stack()
        boolcolumns = ['deaths', 'hosp', 'disabled', 'emergency']
        for b in boolcolumns:
            self.checks[f"{b}2"].state='down'
            self.checks[f"{b}0"].state = 'normal'
            self.checks[f"{b}1"].state = 'normal'

        for field in ['SEX','VAX_MANU', 'VAX_TYPE','VAX_DOSE_SERIES']:
            self.spinners[field].text=''
            self.checks[field].state='normal'

        for field in ['symptomfield', 'CUR_ILL','HISTORY', 'OTHER_MEDS', 'ALLERGIES']:
            self.checks[field].state='normal'
            self.ids[field].text=''

        self.checks['relab'].state = 'normal'
        self.ids['relabtxt'].text = ''
        self.ids['STATE'].text=''
        self.ids['VAX_LOT'].text = ''
        self.checks['VAX_LOT'].state = 'normal'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.checks=dict()
        self.build_spinners()
        vbox=BoxLayout(orientation='vertical', size_hint=(1, None))
        vbox.bind(minimum_height=vbox.setter('height'))

        hbox1=BoxLayout(orientation='horizontal', size_hint = [1, None], height=50)
        rgba = [x / 255.0 for x in [9, 46, 91, 255]]
        btn1=ColoredButton(rgba,text="Go Back", size_hint= [None,None], width=60, height=50)
        btn1.bind(on_press=self.goback)
        hbox1.add_widget(btn1)
        hbox1.add_widget(Label(size_hint_y=None, height=50))
        vbox.add_widget(hbox1)

        # Booleans - deaths, hospitalisations, disabled and emergency room visits
        answers=['Yes','No',"Don't Care"]
        boolcolumns=['deaths','hosp','disabled','emergency']
        coldesc=['Deaths','Hospitalisations','Disabled','Emergency Room Visit?']
        for option2 in boolcolumns:
            glayout = GridLayout(cols=7, size_hint_x=1, size_hint_y=None, padding=5, height=60)
            hbox2 = BoxLayout(orientation='horizontal', size_hint_x=1, size_hint_y=None, padding=5, height=60)
            label1 = ColoredLabel([0.15, 0.15, 0.15, 1], size_hint_x=0.2, size_hint_y=None, height=50,
                                  text=coldesc[boolcolumns.index(option2)]
                                  )

            glayout.add_widget(label1)

            for option1 in answers:
                boxname=f"{option2}{answers.index(option1)}"
                cbox=ToggleButton(group=option2, size_hint_y=None, height=25, size_hint_x=None, width=40,
                                  allow_no_selection = False)
                if answers.index(option1) == 2:
                    cbox.state='down'
                cblabel= Label(text=option1, size_hint_y = None, height=50, size_hint_x = 0.15)
                glayout.add_widget(cbox)
                glayout.add_widget(cblabel)
                self.checks[boxname]=cbox

            #hbox2.add_widget(glayout)
            vbox.add_widget(glayout)

        glayout = GridLayout(cols=6, size_hint_x=1, size_hint_y=None, padding=5, height=60)

        # Lab data
        hbox2 = BoxLayout(orientation='horizontal', size_hint_x=1, size_hint_y=None, padding=5, height=60)
        label1 = ColoredLabel([0.15, 0.15, 0.15, 1], size_hint_x=0.2, size_hint_y=None, height=50,
                            text="Search lab text?"
                            )

        glayout.add_widget(label1)
        cbox = ToggleButton(size_hint_y=None, height=25, size_hint_x=None, width=40,
                             allow_no_selection=True)
        glayout.add_widget(cbox)
        self.checks['relab']=cbox
        tinput=TextInput(size_hint_x=0.2, size_hint_y = None, height=50)
        glayout.add_widget(tinput)
        self.ids['relabtxt']=tinput

        # Symptom text
        label1 = ColoredLabel([0.15, 0.15, 0.15, 1], size_hint_x=0.2, size_hint_y=None, height=50,
                            text="Search symptom text?"
                            )
        glayout.add_widget(label1)
        cbox = ToggleButton(size_hint_y=None, height=25, size_hint_x=None, width=40,
                            allow_no_selection=True)
        glayout.add_widget(cbox)
        self.checks['symptomfield']=cbox
        tinput = TextInput(size_hint_x=0.2, size_hint_y=None, height=50)
        self.ids['symptomfield']=tinput
        glayout.add_widget(tinput)
        # Grid Layout 1
        #hbox2.add_widget(glayout)
        vbox.add_widget(glayout)

        # Textual fields continue
        glayout = GridLayout(cols=6, size_hint_x=1, size_hint_y=None, padding=5, height=60)

        hbox2 = BoxLayout(orientation='horizontal', size_hint_x=1, size_hint_y=None, padding=5, height=60)

        # Medications
        label1 = ColoredLabel([0.15, 0.15, 0.15, 1], size_hint_x=0.2, size_hint_y=None, height=50,
                            text="Search medications?"
                            )
        glayout.add_widget(label1)
        cbox = ToggleButton(size_hint_y=None, height=25, size_hint_x=None, width=40,
                            allow_no_selection=True)
        glayout.add_widget(cbox)
        self.checks['OTHER_MEDS']=cbox
        tinput = TextInput(size_hint_x=0.2, size_hint_y=None, height=50)
        self.ids['OTHER_MEDS']=tinput
        glayout.add_widget(tinput)

        # History
        label1 = ColoredLabel([0.15, 0.15, 0.15, 1], size_hint_x=0.2, size_hint_y=None, height=50,
                            text="Search pre-existing?"
                            )
        glayout.add_widget(label1)
        cbox = ToggleButton(size_hint_y=None, height=25, size_hint_x=None, width=40,
                            allow_no_selection=True)
        glayout.add_widget(cbox)
        self.checks['HISTORY']=cbox
        tinput = TextInput(size_hint_x=0.2, size_hint_y=None, height=50)
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
        label1 = ColoredLabel([0.15, 0.15, 0.15, 1], size_hint_x=0.2, size_hint_y=None, height=50,
                            text="Search existing?"
                            )
        glayout.add_widget(label1)
        cbox = ToggleButton(size_hint_y=None, height=25, size_hint_x=None, width=40,
                            allow_no_selection=True)
        glayout.add_widget(cbox)
        self.checks['CUR_ILL']=cbox
        tinput = TextInput(size_hint_x=0.2, size_hint_y=None, height=50)
        self.ids['CUR_ILL']=tinput
        glayout.add_widget(tinput)

        # Allergies
        label1 = ColoredLabel([0.15, 0.15, 0.15, 1], size_hint_x=0.2, size_hint_y=None, height=50,
                            text="Search allergies?"
                            )
        glayout.add_widget(label1)
        cbox = ToggleButton(size_hint_y=None, height=25, size_hint_x=None, width=40,
                            allow_no_selection=True)
        glayout.add_widget(cbox)
        self.checks['ALLERGIES']=cbox
        tinput = TextInput(size_hint_x=0.2, size_hint_y=None, height=50)
        self.ids['ALLERGIES']=tinput
        glayout.add_widget(tinput)

        # Grid Layout 3
        #hbox2.add_widget(glayout)
        vbox.add_widget(glayout)
        # Spinners begin
        glayout = GridLayout(cols=6, size_hint_x=1, size_hint_y=None, padding=5, height=60)
        hbox2 = BoxLayout(orientation='horizontal', size_hint_x=1, size_hint_y=None, padding=5, height=60)

        # Sex
        label1 = ColoredLabel([0.15, 0.15, 0.15, 1], size_hint_x=0.2, size_hint_y=None, height=50,
                              text='Sex'
                              )

        glayout.add_widget(label1)
        #hbox2.add_widget(glayout)
        cbox = ToggleButton(size_hint_y=None, height=25, size_hint_x=None, width=40,
                            allow_no_selection=True)
        self.checks['SEX']=cbox
        glayout.add_widget(cbox)

        glayout.add_widget(self.spinners['SEX'])
        # Vax Dose
        label1 = ColoredLabel([0.15, 0.15, 0.15, 1], size_hint_x=0.2, size_hint_y=None, height=50,
                              text='Dose'
                              )
        glayout.add_widget(label1)
        cbox = ToggleButton(size_hint_y=None, height=25, size_hint_x=None, width=40,
                            allow_no_selection=True)
        self.checks['VAX_DOSE_SERIES']=cbox
        glayout.add_widget(cbox)
        glayout.add_widget(self.spinners['VAX_DOSE_SERIES'])

        # Grid Layout 4
        vbox.add_widget(glayout)
        # Spinners continue
        glayout = GridLayout(cols=6, size_hint_x=1, size_hint_y=None, padding=5, height=60)
        glayout.bind(minimum_height=self.setter('height'))
        hbox2 = BoxLayout(orientation='horizontal', size_hint_x=1, size_hint_y=None, padding=5, height=60)

        # Vax Type
        label1 = ColoredLabel([0.15, 0.15, 0.15, 1], size_hint_x=0.2, size_hint_y=None, height=50,
                              text='Vax Type'
                              )
        glayout.add_widget(label1)
        cbox = ToggleButton(size_hint_y=None, height=25, size_hint_x=None, width=40,
                            allow_no_selection=True)
        self.checks['VAX_TYPE']=cbox
        glayout.add_widget(cbox)
        glayout.add_widget(self.spinners['VAX_TYPE'])
        # Vax Manufacturer
        label1 = ColoredLabel([0.15, 0.15, 0.15, 1], size_hint_x=0.2, size_hint_y=None, height=50,
                              text='Vax Manufacturer'
                              )
        glayout.add_widget(label1)
        cbox = ToggleButton(size_hint_y=None, height=25, size_hint_x=None, width=40,
                            allow_no_selection=True)
        self.checks['VAX_MANU']=cbox
        glayout.add_widget(cbox)
        glayout.add_widget(self.spinners['VAX_MANU'])

        vbox.add_widget(glayout)

        cbox = ToggleButton(size_hint_y=None, height=25, size_hint_x=None, width=40,
                            allow_no_selection=True)
        self.checks['VAX_LOT']=cbox
        self.ids['VAX_LOT']=TextInput(size_hint_y=None, height=50)
        self.ids['STATE']=TextInput(size_hint_y=None, height=50)

        hbox1=BoxLayout(orientation='horizontal', size_hint_y=None, height=60)
        hbox1.add_widget(
            ColoredLabel([0.15, 0.15, 0.15, 1], size_hint_x=0.2, size_hint_y=None, height=50, text='Vax Lot:'))
        hbox1.add_widget(self.checks['VAX_LOT'])
        hbox1.add_widget(self.ids['VAX_LOT'])
        hbox1.add_widget(
            ColoredLabel([0.15, 0.15, 0.15, 1], size_hint_x=0.2, size_hint_y=None, height=50,text='State:'))
        hbox1.add_widget(self.ids['STATE'])
        vbox.add_widget(hbox1)
        statusfield=Label(size_hint=[1,None], height=40, text="Ready")
        self._statusfield=statusfield
        vbox.add_widget(statusfield)
        btn1=ColoredButton(rgba,text="Submit Query", size_hint_y = None, height=50)
        vbox.add_widget(btn1)
        btn1.bind(on_press=self.execute_query)


        sv=ScrollView(size_hint=(1, None), size=(Window.width, Window.height))
        sv.add_widget(vbox)
        self.add_widget(sv)

# rgb(26, 32, 170) | HEX #1A20AA
# rgb(86, 202, 184) | HEX #56CAB8
# rgb(0, 251, 250) | HEX #00FBFA
# rgb(31, 83, 77) | HEX #1F534D
# rgb(0, 51, 52) | HEX #003334
# rgb(31, 247, 252) | HEX #1FF7FC
# rgb(3, 248, 252) | HEX #03F8FC
# rgb(0, 102, 96) | HEX #006660
# rgb(0, 16, 15) | HEX #00100F