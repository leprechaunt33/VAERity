import asyncio
import datetime
from datetime import timedelta
import importlib.util
import json
import random
import time
import pytz
import os
import vaex.viz
from kivy.config import Config
import kivy.uix.image
from kivy.graphics import Color, Ellipse
from kivy.uix.colorpicker import ColorPicker
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.image import Image
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.settings import SettingsWithSidebar
from kivy.core.window import Window
from kivy.uix.spinner import Spinner, SpinnerOption
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex
import pyautogui
import sys

from matplotlib.patches import Rectangle

from configsettings import VaeritySettings
from dataquerystatscreen import DataQueryStatScreen
from kivystyles import KivyStyles

Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
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
from dataframegridview import DataFrameGridView, ColoredButton, ColoredLabel
from dataqueryscreen import DataQueryViewScreen

_builderstring="""
<LoadDialog>:
    BoxLayout:
        size: root.size
        pos: root.pos
        orientation: "vertical"
        FileChooserListView:
            id: filechooser
            filters: [lambda folder, filename: not (filename.endswith('.sys') or filename.endswith('.tmp'))]

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
            filters: [lambda folder, filename: not (filename.endswith('.sys') or filename.endswith('.tmp'))]
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
    def dismiss_popup(self, *args):
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

    def save_figure(self, *args):
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

    def popup_grid(self, *args):
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

    def transition_main(self, *args):
        self.currapp.manager.transition.direction = 'right'
        self.currapp.manager.current = 'mainscreen'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        vbox=BoxLayout(orientation='vertical')
        hbox1=BoxLayout(orientation='horizontal', size_hint=(None, 0.1))
        self.currapp=App.get_running_app()
        bbg=get_color_from_hex(self.currapp._vc['button.background'])
        bfg=get_color_from_hex(self.currapp._vc['button.textcolor'])
        btn1 = ColoredButton(bbg, color=bfg, text='Go Back', size_hint=(None, None), width=100, height=50)
        btn1.bind(on_release=self.transition_main)
        btn2 = ColoredButton(bbg, color=bfg, text='Save Plot', size_hint=(None, None), width=100, height=50)
        btn2.bind(on_release=self.save_figure)
        btn3 = ColoredButton(bbg, color=bfg, text='View Raw Data', size_hint=(None, None), width=150, height=50)
        btn3.bind(on_release=self.popup_grid)
        hbox1.add_widget(btn1)
        hbox1.add_widget(btn2)
        hbox1.add_widget(btn3)
        vbox.add_widget(hbox1)
        hbox2=BoxLayout()
        vbox.add_widget(hbox2)
        self.add_widget(vbox)

class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)

class SaveDialog(FloatLayout):
    save = ObjectProperty(None)
    text_input = ObjectProperty(None)
    cancel = ObjectProperty(None)

class StyleOption(SpinnerOption):
    def update_ellipse(self, *args):
        self.swatch.pos=(self.pos[0]+5, self.pos[1]+2)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            i=int(self.text.split(':')[0])
        except Exception as ex:
            print(ex)
            return

        currapp=App.get_running_app()
        settings_list = [t[1] for t in currapp._cse.settings_keys if t[0] == 'Styles'][0]
        stylekey=settings_list[i]['key']
        col=get_color_from_hex(currapp._vc[stylekey])

        with self.canvas.after:
            Color(*col)
            self.swatch=Ellipse(segments=18, size=(40,40), pos=(self.pos[0]+5,self.pos[1] +2))
        self.bind(pos=self.update_ellipse)

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
        self.styles = KivyStyles()

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
        self.styles.register_callback(self, 'button.textcolor', self.style_callback)
        self.styles.register_callback(self, 'button.background', self.style_callback)
        self.styles.register_callback(self, 'window.clearcolor', self.style_callback)

    def keyboard_closed(self, *args):
        self._keyboard=None

    def get_application_config(self):
        if 'APPDATA' in os.environ:
            folder=os.environ['APPDATA']
        else:
            folder = os.path.expanduser('~')

        return super().get_application_config(str(os.path.join(folder, 'vaerity.ini')))

    def start_thread_once(self, name, target, args = None):
        for thread in threading.enumerate():
            if thread.name == name:
                print(f"Not starting new thread as one with the name {name} already exists")
                return False

        if args is None:
            args = ()

        threading.Thread(name=name, target=target, args=args).start()
        return True

    def load_style(self, *args):
        self.dismiss_style()
        fname = os.path.join(self.fcstyles.path, self.tbstyles.text or self.fcstyles.selection[0])

        with open(fname, "r") as stylefile:
            newstyles=json.load(stylefile)

        for style in newstyles.keys():
            self._vc[style]=newstyles[style]
            self.styles.notify_style_change(style)

    def save_style(self, *args):
        self.stylespopup.dismiss()
        print(f"You decided to save the style {self.tbstyles.text} in {self.fcstyles.path}")
        fname=os.path.join(self.fcstyles.path, self.tbstyles.text)
        try:
            stylefile=open(fname, "w")
            print(json.dumps(self._vc), file=stylefile)
            stylefile.close()
        except Exception as ex:
            print(f"Unable to save file: {ex}")

    def dismiss_style(self, *args):
        self.stylespopup.dismiss()

    def update_tbstyles(self, *args):
        if self.fcstyles.selection is not None:
            self.tbstyles.text=self.fcstyles.selection[0]
        else:
            print("I'm here... but there's no selection?")

    def pop_styles(self, *args):
        popcontent = RelativeLayout(size_hint=(1, 1))
        lbl1 = ColoredLabel(get_color_from_hex(self._vc['label.background']),
                            color=get_color_from_hex(self._vc['label.textcolor']),
                            text="Select [b]Load[/b] to load a style or [b]Save[/b] to save the curreht style.",
                            markup=True)
        lbl1.pos_hint={'top': 1, 'left': 0}
        lbl1.size_hint=(1,None)
        lbl1.height=50
        popcontent.add_widget(lbl1)
        dirname=os.path.join(os.path.dirname(__file__), 'styles')
        if not os.path.exists(dirname):
            try:
                os.mkdir(dirname)
            except Exception as ex:
                dirname=os.path.dirname(__file__)

        fc=FileChooserListView(path=dirname, filters=['*.style'], size_hint=(1,0.7))
        fc.pos_hint = {'top': 0.9, 'x': 0}

        popcontent.add_widget(fc)

        bbg=get_color_from_hex(self._vc['button.background'])
        bfg = get_color_from_hex(self._vc['button.textcolor'])
        tbg = get_color_from_hex(self._vc['textbox.background'])
        tfg = get_color_from_hex(self._vc['textbox.textcolor'])
        self.tbstyles=TextInput(multiline=False, size_hint=(1, None),
                                height=40, background_color = tbg, foreground_color = tfg)
        self.tbstyles.pos_hint={'x': 0, 'y': 55/(0.8*Window.height)}
        popcontent.add_widget(self.tbstyles)
        fc.bind(selection=self.update_tbstyles)

        btn1=ColoredButton(bbg, color=bfg, text='Load', size_hint=(None,None), width=75, height=50)
        btn1.bind(on_release=self.load_style)
        btn1.pos_hint={'y': 0, 'x': 0}
        btn2=ColoredButton(bbg, color=bfg, text='Save', size_hint=(None,None), width=75, height=50)
        btn2.bind(on_release=self.save_style)
        btn2.pos_hint={'y': 0, 'x': 0.2}
        self.fcstyles = fc

        btn3=ColoredButton(bbg, color=bfg, text='Cancel', size_hint=(None,None), width=75, height=50)
        btn3.bind(on_release=self.dismiss_style)
        btn3.pos_hint={'y': 0, 'x': 0.4}
        popcontent.add_widget(btn1)
        popcontent.add_widget(btn2)
        popcontent.add_widget(btn3)
        self.stylespopup=Popup(title="Styles", size_hint=(0.8, 0.8), content=popcontent)
        self.stylespopup.open()

    def update_picker(self, *args):
        if self.stylespinner.text == '':
            return

        try:
            i=int(self.stylespinner.text.split(':')[0])
        except Exception as ex:
            print(ex)
            return

        settings_list = [t[1] for t in self._cse.settings_keys if t[0] == 'Styles'][0]
        stylekey=settings_list[i]['key']
        col=get_color_from_hex(self._vc[stylekey])
        self.stylecp.color = col

    def update_stylekey(self, *args):
        if self.stylespinner.text == '':
            return

        try:
            i=int(self.stylespinner.text.split(':')[0])
        except Exception as ex:
            print(ex)
            return
        settings_list = [t[1] for t in self._cse.settings_keys if t[0] == 'Styles'][0]
        stylekey=settings_list[i]['key']
        self._vc[stylekey]=self.stylecp.hex_color
        self.styles.notify_style_change(stylekey)


    def pop_edit_styles(self, *args):
        popcontent=RelativeLayout(size_hint=(1,1))
        spinner1 = Spinner(size_hint = (1, 0.1), option_cls=StyleOption)
        settings_list = [t[1] for t in self._cse.settings_keys if t[0] == 'Styles'][0]
        styleopt=[f"{i}: {s['title'] }" for i, s in enumerate(settings_list) if s['type'] != 'title']
        spinner1.values=styleopt
        spinner1.pos_hint={'top': 1, 'x': 0}
        colorpicker=ColorPicker(size_hint=(1,0.8))
        colorpicker.pos_hint={'top': 0.9, 'x': 0}
        bbg=get_color_from_hex(self._vc['button.background'])
        bfg = get_color_from_hex(self._vc['button.textcolor'])
        btn1=ColoredButton(bbg, color=bfg, text="Update")
        btn1.size_hint=(1,None)
        btn1.height=50
        btn1.pos_hint={'y': 0, 'x': 0}
        spinner1.bind(text=self.update_picker)
        btn1.bind(on_release=self.update_stylekey)

        self.stylecp = colorpicker
        self.stylespinner = spinner1

        popcontent.add_widget(spinner1)
        popcontent.add_widget(colorpicker)
        popcontent.add_widget(btn1)
        self.editstylepop=Popup(size_hint=(0.6, 0.6), title='Edit existing style', content=popcontent)
        self.editstylepop.background_color=(0,0,0,0.05)
        self.editstylepop.open()

    def keyboard_event_loop(self, window, key, scancode, codepoint, modifier):
        if self._keyboard is not None:
            keyname=self._keyboard.keycode_to_string(key)
        else:
            keyname=''

        # Keys that should operate on all screens first, then dispatch to
        # specific classes
        if all(m in modifier for m in ['ctrl', 'alt']) and (keyname == 's'):
                self.pop_styles()
        elif all(m in modifier for m in ['ctrl', 'alt']) and (keyname == 'c'):
            self.pop_edit_styles()
        elif all(m in modifier for m in ['ctrl', 'alt']) and codepoint == 'm':
            modlist = open('modules.txt', 'w')
            print(json.dumps(sorted(list(sys.modules.keys())), indent=4), file=modlist)
            modlist.close()
            print(json.dumps(list(sys.modules.keys())))
        elif self.manager.current == 'statscreen':
            statscreen: DataQueryStatScreen = self.manager.get_screen('statscreen')
            statscreen.handle_keyboard(window, key, scancode, codepoint, modifier, keyname)
        elif self.manager.current == 'resultscreen':
            resultscreen: DataQueryResultScreen = self.manager.get_screen('resultscreen')
            resultscreen.handle_keyboard(window, key, scancode, codepoint, modifier, keyname)
        elif (len(modifier) == 0) and (keyname in self.navkeys):
            # Nav keys goes last until it is folded into the specific classes
            if self.manager.current == 'dataqueryscreen':
                dq: DataQueryViewScreen = self.manager.get_screen(self.manager.current)
                focus = self.current_focus()
                if (focus is None) or (not isinstance(focus, Widget)):
                    if keyname == 'down':
                        dq._sv.scroll_y = max(dq._sv.scroll_y - 1 / 100, 0.)
                    elif keyname == 'up':
                        dq._sv.scroll_y = min(dq._sv.scroll_y + 1 / 100, 1.)
                    elif keyname == 'pageup':
                        dq._sv.scroll_y = min(dq._sv.scroll_y + 1 / 10, 1.)
                    elif keyname == 'pagedown':
                        dq._sv.scroll_y = max(dq._sv.scroll_y - 1 / 10, 0.)

                else:
                    print(focus)

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
        self.start_thread_once(name='report 1',target=self.call_report_1)

    def call_report_2(self):
        helperfunc.piecharts1(self.df['data'], self)
        self.showplot(plt.gcf(),'heatmapscreen')

    def start_report_2(self, *args):
        plt.clf()
        plt.cla()
        self.start_thread_once(name='report 2', target=self.call_report_2)

    def call_report_3(self):
        helperfunc.symptoms(self.df['symptoms'], self)
        self.showplot(plt.gcf(),'heatmapscreen')

    def start_report_3(self, *args):
        plt.clf()
        plt.cla()
        self.start_thread_once(name='report 3',target=self.call_report_3)

    def call_report_4(self, searchTerm):
        helperfunc.filtersymptoms(self.df['symptoms'],searchTerm, self)
        self.showplot(plt.gcf(),'heatmapscreen')

    def startsymptomsearch(self, *args):
        self._psearch.dismiss()
        self.start_thread_once(name='symptom search',target=self.call_report_4, args=[self.ids['txtinput'].text])

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
        self.start_thread_once(name='heatmap',target=self.heatmap)


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

    def style_callback(self, key):
        if key == 'button.textcolor':
            for button in self.button_ids:
                fgcolor=get_color_from_hex(self._vc[key])
                self.ids[button].set_fgcolor(fgcolor)

        if key == 'button.background':
            bgcolor=get_color_from_hex(self._vc[key])
            for button in self.button_ids:
                self.ids[button].set_bgcolor(bgcolor)

        if key == 'window.clearcolor':
            Window.clearcolor = self._vc[key]

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
        self.start_thread_once(name='dbimport', target=self.setupdataframes)


    def build(self):
        sm = ScreenManager()
        self.settings_cls=SettingsWithSidebar
        self._vc=dict(self.config.items('style'))
        self._vr = dict(self.config.items('main'))
        resourcesdir=os.path.join(os.path.dirname(__file__),'resources')
        self.icon=os.path.join(resourcesdir,'vaerity256x256.ico')

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
            bgcolor=get_color_from_hex(self._vc['button.background'])
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

        self.title="VAERity 1.0RC1"

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
            # So FileChooserListView doesnt crash viewing the non existent folder
            self._vr['vaersfolder'] = str(os.path.dirname(__file__))
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
        elif  key == 'vaersfolder':
            if os.path.exists(value):
                self._vr = dict(self.config.items('main'))
                Clock.schedule_once(self.startdbimport, 2)
                Clock.schedule_interval(self.splashcarousel, 5)
        elif section == 'style':
            self._vc=dict(self.config.items('style'))
            self.styles.notify_style_change(key)

    async def base(self):
        await self.async_run()
        print("App completed successfully")

    def current_focus(self):
        s: Screen=self.manager.get_screen(self.manager.current)
        if s is None:
            return None

        child=self.root_window.children[0]
        if isinstance(child, Popup):
            for widget in child.walk():
                if not hasattr(widget, 'focus'):
                    continue
                if widget.focus:
                    return widget

        for widget in s.walk():
            if not hasattr(widget, 'focus'):
                continue
            if widget.focus:
                return widget

        return None

