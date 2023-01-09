# TODO: Change startup screen to move to a carousal or random image transition after the logo screen.  Update logo.

import asyncio
import importlib.util
import json
import random

import kivy.uix.image
from kivy.config import Config
from kivy.uix.image import Image
from kivy.uix.settings import SettingsWithSidebar
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex
import pyautogui
import sys

from configsettings import VaeritySettings
from dataquerystatscreen import DataQueryStatScreen

Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
import os
import threading
import matplotlib.pyplot as plt
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Keyboard
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
        boxPop.size_hint_x=None
        boxPop.size_hint_y=0.8
        boxPop.bind(minimum_width=self.setter('width'))

        self.currapp=App.get_running_app()
        bgcolor=get_color_from_hex(self.currapp._vc['gridview.background'])
        textcolor = get_color_from_hex(self.currapp._vc['gridview.textcolor'])
        butSaveCsv=ColoredButton(bgcolor,text='Save CSV', color=textcolor, bold=True, size_hint_x=None, width = 100)
        butSaveCsv.bind(on_press=self.save_csv_dialog)
        butSaveCsv.size_hint_y=0.1
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
    _keyboard: Keyboard = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.navkeys = ('up', 'down', 'left', 'right','pageup','pagedown')
        self.loaded = False
        self.windowstatus = None
        self.progress = None
        self.df=dict()
        self.ids=dict()
        self.rangedfields=dict()
        self.regexfields=dict()
        self._vc = None

        Builder.load_string(_builderstring)

        if 'pyautogui' in sys.modules:
            pass
        elif (spec := importlib.util.find_spec('pyautogui')) is not None:
            module = importlib.util.module_from_spec(spec)
            sys.modules['pyautogui'] = module
            spec.loader.exec_module(module)
        else:
            print(f"can't find the pyautogui module!")
            return

        self.screensize=pyautogui.size()
        self._cse=VaeritySettings()
        self._keyboard=Window.request_keyboard(self.keyboard_closed(), self.root)
        Window.bind(on_keyboard=self.keyboard_event_loop)

    def keyboard_closed(self, *args):
        self._keyboard=None

    def keyboard_event_loop(self, window, key, scancode, codepoint, modifier):
        if self._keyboard is not None:
            keyname=self._keyboard.keycode_to_string(key)
        else:
            keyname=''

        if all(m in modifier for m in ['ctrl', 'alt']) and codepoint == 'm':
            modlist=open('modules.txt','w')
            print(json.dumps(list(sys.modules.keys())),file=modlist)
            modlist.close()
            print(json.dumps(list(sys.modules.keys())))
        elif all(m in modifier for m in ['ctrl', 'alt']) and codepoint == 'n':
            print("Matched modifiers and codepoint")
            if self.manager.current == 'statscreen':
                statscreen: DataQueryStatScreen=self.manager.get_screen('statscreen')
                statscreen.current_figure=(statscreen.current_figure+1) % len(statscreen.figs)
            else:
                print(f"{self.manager.current}")
        elif (len(modifier) == 0) and ( keyname in self.navkeys):
            if self.manager.current == 'statscreen':
                statscreen: DataQueryStatScreen = self.manager.get_screen('statscreen')
                if keyname == 'right':
                    statscreen._sv.scroll_x=min(statscreen._sv.scroll_x + 1/250,1)
                elif keyname == 'left':
                    statscreen._sv.scroll_x = max(statscreen._sv.scroll_x - 1 / 250, 0)
                elif keyname == 'up':
                    statscreen._sv.scroll_y = min(statscreen._sv.scroll_y + 1 / 250, 1)
                elif keyname == 'down':
                    statscreen._sv.scroll_y = max(statscreen._sv.scroll_y - 1 / 250, 0)
                elif keyname == 'pageup':
                    statscreen._sv.scroll_y = min(statscreen._sv.scroll_y + 1 / 25, 1)
                elif keyname == 'pagedown':
                    statscreen._sv.scroll_y = max(statscreen._sv.scroll_y - 1 / 25, 0)
            elif self.manager.current == 'resultscreen':
                resultscreen: DataQueryResultScreen=self.manager.get_screen(self.manager.current)
                focus=self.current_focus()
                if (focus is None) or (not isinstance(focus, TextInput)):
                    if keyname == 'left':
                        resultscreen.navLeft()
                    elif keyname == 'right':
                        resultscreen.navRight()
            elif self.manager.current == 'dataqueryscreen':
                dq: DataQueryViewScreen = self.manager.get_screen(self.manager.current)
                focus=self.current_focus()
                if (focus is None) or (not isinstance(focus, Widget)):
                    if keyname == 'down':
                        dq._sv.scroll_y = max(dq._sv.scroll_y - 1/100,0.)
                    elif keyname == 'up':
                        dq._sv.scroll_y = min(dq._sv.scroll_y + 1 / 100, 1.)
                    elif keyname == 'pageup':
                        dq._sv.scroll_y = min(dq._sv.scroll_y + 1 / 10, 1.)
                    elif keyname == 'pagedown':
                        dq._sv.scroll_y = max(dq._sv.scroll_y - 1/10,0.)

                else:
                    print(focus)
        #else:
            #print(f"{modifier}, {keyname}, {scancode}")

    def load_splash_screen(self,*args):
        resourcesdir=os.path.join(os.path.dirname(__file__),'resources')
        splashdir=os.path.join(resourcesdir,'splash')
        self.splashlist=[os.path.join(resourcesdir,"vaerity_logo.png")]
        randos=[file.path for file in os.scandir(splashdir) if (file.name.endswith('.gif') | file.name.endswith('.jpg'))]
        random.shuffle(randos)
        self.splashlist.extend(randos)

        self.splashindex=0
        imgfile=self.splashlist[self.splashindex]
        self.splashheader=Image(source=imgfile, size_hint_x=None, width=480)
        self.splashtexture=self.splashheader.texture
        self.splashheader.anim_delay=1/10.0
        self.splashheader.anim_loop=0
        self.splashheader.size_hint_y=None
        self.splashheader.height=self.splashheader.texture_size[1]
        self.splashheader.pos_hint={'center_x': 0.5, 'center_y': 0.5}

    def splashcarousel(self, *args):
        if len(self.splashlist) == 0:
            return None

        self.splashindex += 1
        if self.splashindex >= len(self.splashlist):
            self.splashindex=0

        if os.path.exists(self.splashlist[self.splashindex]):
            self.splashheader.source=self.splashlist[self.splashindex]
            self.splashtexture=self.splashheader.texture
            self.splashheader.anim_delay=1/10.0
            self.splashheader.anim_loop=0
            self.splashheader.size_hint_y=None
            self.splashheader.height=self.splashheader.texture_size[1]

        if not self.loaded:
            Clock.schedule_interval(self.splashcarousel,5)

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
                child.parent.remove_widget(child)
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
        if hasattr(self,'rangedfields'):
            for fld in self.rangedfields.values():
                fld.df=self.df['data']

        if hasattr(self,'regexfields'):
            for fld in self.regexfields.values():
                fld.df=self.df['data']

        dq=self.manager.get_screen('dataqueryscreen')
        dq.marty.df=self.df['data']


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
        self.loaded=True

    def startdbimport(self,*args):
        threading.Thread(target=self.setupdataframes).start()


    def build(self):
        sm = ScreenManager()
        self.settings_cls=SettingsWithSidebar
        self._vc=dict(self.config.items('style'))
        self._vr = dict(self.config.items('main'))

        # All Window manipulation is done before loading images/layouts
        # so that sizing works properly
        Window.clearcolor=self._vc['window.clearcolor']
        Window.size = (600,600)
        Window.borderless=1
        Window.top=0
        Window.left=(self.screensize[0]-600)//2

        mainscreen=Screen(name='mainscreen')
        layout = GridLayout(rows=7, cols=1)
        self.progress = ProgressBar(max=1000)
        self.progress.size_hint=(1, None)
        self.progress.height=32
        self.windowstatus = Label(text='Ready.', font_size='10sp', size_hint=(1, None), height=120)
        box1= BoxLayout(orientation='vertical')
        self.load_splash_screen()
        box1.add_widget(self.splashheader)
        box1.add_widget(self.progress)
        box1.add_widget(self.windowstatus)
        layout.add_widget(box1)

        self.button_layout=BoxLayout(orientation='vertical', size_hint_y=None, height=250)
        if 'button.textcolor' in self._vc:
            textcolor=self._vc['button.textcolor']
        else:
            textcolor=self._cse.settings_defaults[0][1]['button.textcolor']

        textcolor=get_color_from_hex(textcolor)

        if 'button.background' in self._vc:
            bgcolor=self._vc['button.background']
        else:
            bgcolor=self._cse.settings_defaults[0,1]['button.background']

        menubuttons=[ColoredButton(bgcolor,text='1. Vaccinations by month and sex, stack plot.', color=textcolor),
                    ColoredButton(bgcolor,text=f"2. Hospitalisations and deaths\nby age group, filtered by year.", color=textcolor),
                    ColoredButton(bgcolor,text='3. List most common words in symptom text', color=textcolor),
                    ColoredButton(bgcolor,text='4. Filter symptom text by common word', color=textcolor),
                    ColoredButton(bgcolor,text='5. 2D histogram [age/days since vaccination]', color=textcolor),
                    ColoredButton(bgcolor,text='6. Data Query Screen', color=textcolor)
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

        self.title="VAERity"

        mainscreen.add_widget(layout)
        sm.add_widget(mainscreen)
        sm.add_widget(HeatMapScreen(name='heatmapscreen'))
        sm.add_widget(DataQueryViewScreen(name='dataqueryscreen'))
        sm.add_widget(DataQueryResultScreen(name='resultscreen'))
        sm.add_widget(DataQueryStatScreen(name='statscreen'))
        self.manager=sm
        self.mainscreen=mainscreen
        self.mslayout=layout
        if os.path.exists(self._vr['vaersfolder']):
            Clock.schedule_once(self.startdbimport, 2)
            Clock.schedule_interval(self.splashcarousel, 5)
        else:
            Clock.schedule_once(self.open_settings, 2)
        return sm

    def build_config(self, config):
        for tupac in self._cse.settings_defaults:
            config.setdefaults(tupac[0],tupac[1])

    def build_settings(self, settings):
        for tupac in self._cse.settings_keys:
            settings.add_json_panel(tupac[0], self.config, data=json.dumps(tupac[1]))

    def on_config_change(self, config, section, key, value):
        if key == 'window.clearcolor':
            Window.clearcolor=value

        # TODO: on change of VAERS folder, check that it exists, and if so
        #  call the database initialization code

    async def base(self):
        await self.async_run()
        print("App completed successfully")

    def current_focus(self):
        s: Screen=self.manager.get_screen(self.manager.current)
        if s is None:
            return None

        for widget in s.walk():
            if not hasattr(widget, 'focus'):
                continue
            if widget.focus:
                return widget

        return None
