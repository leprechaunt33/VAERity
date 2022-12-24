import asyncio
import random

import kivy.uix.image
from kivy.config import Config
from kivy.uix.image import Image
from kivy.core.window import Window
import pyautogui
import sys
from dataquerystatscreen import DataQueryStatScreen

Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
#Config.set('kivy', 'log_level', 'error')
import os
import threading
import matplotlib.pyplot as plt
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy.properties import ObjectProperty
from kivy.clock import Clock, mainthread
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

import helperfunc
from dataqueryresultscreen import DataQueryResultScreen
from helperfunc import vaershandle
from virtualcolumns import *
from kivy.garden.matplotlib import FigureCanvasKivyAgg
from dataframegridview import DataFrameGridView, ColoredButton
from dataqueryscreen import DataQueryViewScreen

_builderstring="""
<HeatMapScreen>:
    BoxLayout:
        orientation: 'vertical'
        BoxLayout:
            orientation: 'horizontal'
            size_hint: None, 0.1
            Button:
                text: 'Go Back'
                width: 100
                size_hint: None, None
                on_press:
                    root.manager.transition.direction = 'right'
                    root.manager.current = 'mainscreen'
                
            Button:
                text: 'Save Plot'
                width: 100
                size_hint: None, None
                on_press: root.save_figure()
            Button:
                text: 'View Raw Data'
                width: 150
                size_hint: None, None
                on_press: root.popup_grid()
        BoxLayout:
            name: 'imglayout'
            
<LoadDialog>:
    BoxLayout:
        size: root.size
        pos: root.pos
        orientation: "vertical"
        FileChooserListView:
            id: filechooser

        BoxLayout:
            size_hint_y: None
            height: 30
            Button:
                text: "Cancel"
                on_release: root.cancel()

            Button:
                text: "Load"
                on_release: root.load(filechooser.path, filechooser.selection)

<SaveDialog>:
    text_input: text_input
    BoxLayout:
        size: root.size
        pos: root.pos
        orientation: "vertical"
        FileChooserListView:
            id: filechooser
            on_selection: text_input.text = self.selection and self.selection[0] or ''

        TextInput:
            id: text_input
            size_hint_y: None
            height: 30
            multiline: False

        BoxLayout:
            size_hint_y: None
            height: 30
            Button:
                text: "Cancel"
                on_release: root.cancel()

            Button:
                text: "Save"
                on_release: root.save(filechooser.path, text_input.text)
"""

class HeatMapScreen(Screen):
    def dismiss_popup(self):
        if self._popup is not None:
            self._popup.dismiss()

    def save_figure_png(self, path, file):
        self.dismiss_popup()
        curscreen=self.manager.get_screen(self.manager.current)
        for child in curscreen.walk():
            if isinstance(child,FigureCanvasKivyAgg):
                boximg=child

        if boximg is not None:
            try:
                boximg.print_png(os.path.join(path, file))
            except:
                print(f"Unable to save file {file} in {path}")

    def save_figure(self):
        content=SaveDialog(save=self.save_figure_png, cancel=self.dismiss_popup)
        self._popup = Popup(title="Save Plot", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def save_csv(self, path, file):
        self._pgrid.dismiss()
        self._popup.dismiss()
        App.get_running_app().ids['graphdata'].to_csv(os.path.join(path, file))

    def save_csv_dialog(self, *args):
        content=SaveDialog(save=self.save_csv, cancel=self.dismiss_popup)
        self._popup = Popup(title="Save CSV", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def popup_grid(self):
        scrollable=ScrollView()
        boxPop=BoxLayout(orientation='vertical')
        butSaveCsv=ColoredButton([0.1,0.1,1,1])
        butSaveCsv.text='Save CSV'
        butSaveCsv.color=[1,1,1,1]
        butSaveCsv.bold=True
        butSaveCsv.bind(on_press=self.save_csv_dialog)
        butSaveCsv.size_hint_y=0.1
        butSaveCsv.size_hint_x=None
        butSaveCsv.width=100
        boxPop.add_widget(butSaveCsv)
        boxPop.add_widget(DataFrameGridView(App.get_running_app().ids['graphdata']))
        scrollable.add_widget(boxPop)
        self._pgrid=Popup(title="DataFrame View",content=scrollable, size_hint=(0.9,0.9))
        self._pgrid.open()

class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)

class SaveDialog(FloatLayout):
    save = ObjectProperty(None)
    text_input = ObjectProperty(None)
    cancel = ObjectProperty(None)

class RootWindow(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.windowstatus = None
        self.progress = None
        self.df=dict()
        self.ids=dict()
        Builder.load_string(_builderstring)

        if 'pyautogui' in sys.modules:
            pass
        elif (spec := importlib.util.find_spec('pyautogui')) is not None:
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
        else:
            print(f"can't find the pyautogui module!")
            return None

        self.screensize=pyautogui.size()

    def load_splash_screen(self,*args):
        resourcesdir=os.path.join(os.path.dirname(__file__),'resources')
        splashdir=os.path.join(resourcesdir,'splash')
        imagelist=os.scandir(splashdir)
        gifs=[file for file in imagelist if (file.name.endswith('.gif') | file.name.endswith('.jpg'))]
        giffile=gifs[int(len(gifs)*random.random())]
        self.splashanim=Image(source=giffile.path, size_hint_x=None, width=480)
        self.splashtexture=self.splashanim.texture
        self.splashheader=Image(source=os.path.join(resourcesdir,"vaers logo.png"), size_hint_x=None, width=480)
        self.splashanim.anim_delay=1/10.0
        self.splashanim.anim_loop=0
        self.splashanim.size_hint_y=None
        self.splashheader.size_hint_y = None
        self.splashheader.height=self.splashanim.texture_size[1]
        self.splashanim.height=self.splashanim.texture_size[1]

    @mainthread
    def update_status(self,text):
        if self.windowstatus is not None:
            curtxt=self.windowstatus.text
            if curtxt.count("\n")>4:
                curtxt=curtxt[curtxt.find("\n") + 1:]
            self.windowstatus.text=f"{curtxt}\n{text}"

    @mainthread
    def showplot(self,fig,screen):
        hmscreen=self.manager.get_screen(screen)

        try:
            boximg=hmscreen.children[0].children[0]
        except:
            boximg=None

        if boximg is not None:
            if len(boximg.children) == 0:
                boximg.add_widget(FigureCanvasKivyAgg(fig))
            else:
                boximg.remove_widget(boximg.children[0])
                boximg.add_widget(FigureCanvasKivyAgg(fig))

        self.manager.current = screen

    def call_report_1(self):
        plt.clf()
        plt.cla()
        helperfunc.bymonthandsex(self.df['data'],self)
        self.showplot(plt.gcf(),'heatmapscreen')

    def start_report_1(self, *args):
        threading.Thread(target=self.call_report_1).start()

    def call_report_2(self):
        helperfunc.piecharts1(self.df['data'], self)
        self.showplot(plt.gcf(),'heatmapscreen')

    def start_report_2(self, *args):
        plt.clf()
        plt.cla()
        threading.Thread(target=self.call_report_2).start()

    def call_report_3(self):
        helperfunc.symptoms(self.df['symptoms'], self)
        self.showplot(plt.gcf(),'heatmapscreen')

    def start_report_3(self, *args):
        plt.clf()
        plt.cla()
        threading.Thread(target=self.call_report_3).start()

    def call_report_4(self, searchTerm):
        helperfunc.filtersymptoms(self.df['symptoms'],searchTerm, self)
        self.showplot(plt.gcf(),'heatmapscreen')

    def startsymptomsearch(self, *args):
        self._psearch.dismiss()
        threading.Thread(target=self.call_report_4, args=[self.ids['txtinput'].text]).start()

    def start_report_4(self, *args):
        wrapbox = BoxLayout(orientation='vertical')
        content=BoxLayout(orientation='horizontal')
        lSearchTerm=Label(
            text='Enter a search term'
        )
        txtinput=TextInput()
        txtinput.size_hint=(0.4, None)
        txtinput.height=30
        self.ids['txtinput']=txtinput
        content.add_widget(lSearchTerm)
        content.add_widget(txtinput)
        wrapbox.add_widget(content)
        btnSubmit=ColoredButton([0.1,0.1,1,1])
        btnSubmit.text="Search"
        btnSubmit.bind(on_press=self.startsymptomsearch)
        wrapbox.add_widget(btnSubmit)
        self._psearch=Popup(title="Search for symptoms",content=wrapbox, size_hint=(0.8,0.5))
        self._psearch.open()

    def heatmap(self, *args):
        plt.clf()
        plt.cla()
        self.df['data'].viz.heatmap(self.df['data'].AGE_YRS, self.df['data'].NUMDAYS, f="log")
        self.showplot(plt.gcf(),'heatmapscreen')

    def start_report_5(self,*args):
        threading.Thread(target=self.heatmap).start()


    def dataqueryscreen(self,*args):
        self.manager.current='dataqueryscreen'

    @mainthread
    def update_progress(self,val):
        if self.progress is not None:
            self.progress.value=int(val)

    @mainthread
    def assign_buttons(self):
        Window.borderless=0
        Window.resizable=1
        for child in self.mslayout.walk():
            if isinstance(child,kivy.uix.image.Image):
                child.parent.parent.remove_widget(child.parent)
                # So as not to child.parent.parent.remove_widget twice on the same parent
                break

        self.mslayout.add_widget(self.button_layout)
        Window.size= (800,self.progress.height+self.windowstatus.height+self.button_layout.height+50)
        Window.top=25

        self.ids['bymonthandsex'].bind(on_press=self.start_report_1)
        self.ids['hospreport'].bind(on_press=self.start_report_2)
        self.ids['tokenize_symptoms'].bind(on_press=self.start_report_3)
        self.ids['filterbyword'].bind(on_press=self.start_report_4)
        self.ids['histogram'].bind(on_press=self.start_report_5)
        self.ids['dataqueryscreen'].bind(on_press=self.dataqueryscreen)

    def setupdataframes(self,*args):
        self.update_status("Loading VAERSDATA dataframe")
        self.df['data'] = vaershandle('DATA')
        self.update_progress(100)
        self.update_status("Loading VAERSVAX dataframe")
        self.df['vax'] = vaershandle('VAX')
        self.update_progress(200)
        self.update_status("Loading VAERSSYMPTOMS dataframe")
        self.df['symptoms'] = vaershandle('SYMPTOMS')
        self.update_progress(300)
        self.update_status(f"Frame lengths {len(self.df['data'])},{len(self.df['vax'])},{len(self.df['symptoms'])}")
        seenv = dict()

        def seenid(x):
            if x in seenv:
                return False
            else:
                seenv[x] = 1
                return True

        self.update_status("Getting unique ids from VAERSVAX table")
        vaxdf2 = self.df['vax'][self.df['vax'].apply(seenid, arguments=[self.df['vax'].VAERS_ID])]
        self.update_progress(400)
        self.update_status("Joining with DATA frame...")
        dfdata = self.df['data'].join(vaxdf2, on='VAERS_ID', how='left', allow_duplication=True)
        self.update_status(f"Dataframe length after join with vax table: {len(dfdata)}. Now getting stats:")
        self.update_progress(500)
        self.df['data']=dfdata
        hosp=len(dfdata[dfdata.HOSPITAL == 'Y'])
        hospcovid=len(dfdata[(dfdata.HOSPITAL == 'Y') & ((dfdata.VAX_TYPE == 'COVID19') | (dfdata.VAX_TYPE.str.len() < 1)) ])
        deaths=len(dfdata[dfdata.DIED == 'Y'])
        deathscovid=len(dfdata[(dfdata.DIED == 'Y') & ((dfdata.VAX_TYPE == 'COVID19') | (dfdata.VAX_TYPE.str.len() < 1)) ])

        self.update_progress(600)
        self.update_status(f"Hospitalized {hosp} ({hospcovid} COVID), Deaths {deaths} ({deathscovid} COVID")
        self.update_status("Adding virtual columns to group dates and ages")
        self.df['data']['pdate'] = self.df['data'].RECVDATE.apply(parse_datetime)
        self.df['data']['ydate'] = self.df['data'].RECVDATE.apply(year_datetime)
        self.df['data']['age_bin'] = self.df['data'].AGE_YRS.apply(age_bin)
        self.update_progress(1000)
        self.update_status("Ready to run reports!")
        self.assign_buttons()

    def startdbimport(self,*args):
        threading.Thread(target=self.setupdataframes).start()


    def build(self):
        sm = ScreenManager()
        mainscreen=Screen(name='mainscreen')
        layout = GridLayout(rows=7, cols=1)
        self.progress = ProgressBar(max=1000)
        self.progress.size_hint=(1, None)
        self.progress.height=32
        self.windowstatus = Label(text='Ready.', font_size='10sp', size_hint=(1, None), height=120)
        box1= BoxLayout(orientation='vertical')
        self.load_splash_screen()
        box2=BoxLayout(orientation='horizontal', size_hint_y=None, height=self.splashanim.texture_size[1]+10)
        box2.add_widget(self.splashheader)
        box2.add_widget(self.splashanim)
        box1.add_widget(box2)
        box1.add_widget(self.progress)
        box1.add_widget(self.windowstatus)
        layout.add_widget(box1)
        print(box2.height, box1.height, box1.minimum_height)

        Window.size = (960,600)
        Window.borderless=1
        Window.top=0
        Window.left=(self.screensize[0]-960)//2

        self.button_layout=BoxLayout(orientation='vertical', size_hint_y=None, height=250)
        menubuttons=[Button(text='1. Vaccinations by month and sex, stack plot.'),
                    Button(text=f"2. Hospitalisations and deaths\nby age group, filtered by year."),
                    Button(text='3. List most common words in symptom text'),
                    Button(text='4. Filter symptom text by common word'),
                    Button(text='5. 2D histogram [age/days since vaccination]'),
                    Button(text='6. Data Query Screen')
                    ]

        self.button_ids=['bymonthandsex','hospreport','tokenize_symptoms','filterbyword','histogram','dataqueryscreen']
        butnum=1
        boxn=None
        for butn in menubuttons:
            self.ids[self.button_ids[butnum-1]]=butn
            if butnum % 2 == 1:
                boxn=BoxLayout(orientation='horizontal', size_hint=(1,None), height=80)
                boxn.add_widget(butn)
            if butnum % 2 == 0:
                boxn.add_widget(butn)
                self.button_layout.add_widget(boxn)
            butnum += 1

        self.title="VAERS Local Interface"

        mainscreen.add_widget(layout)
        sm.add_widget(mainscreen)
        sm.add_widget(HeatMapScreen(name='heatmapscreen'))
        sm.add_widget(DataQueryViewScreen(name='dataqueryscreen'))
        sm.add_widget(DataQueryResultScreen(name='resultscreen'))
        sm.add_widget(DataQueryStatScreen(name='statscreen'))
        self.manager=sm
        self.mainscreen=mainscreen
        self.mslayout=layout
        Clock.schedule_once(self.startdbimport, 2)
        return sm


    async def base(self):
        await self.async_run()
        print("App completed successfully")
