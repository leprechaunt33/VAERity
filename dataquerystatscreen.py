import os

import kivy.garden.matplotlib
from kivy.app import App
from kivy.core.window import Window
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.utils import get_color_from_hex

from dataframegridview import ColoredButton
from kivy.garden.matplotlib import FigureCanvasKivyAgg

_builderstring = """
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

<dataquerystatscreen.SaveDialog>:
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

class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)

class SaveDialog(FloatLayout):
    save = ObjectProperty(None)
    text_input = ObjectProperty(None)
    cancel = ObjectProperty(None)

class DataQueryStatScreen(Screen):
    currapp = None

    def goback(self, *args):
        self.currapp.manager.current = 'resultscreen'

    def set_figure(self,fig):
        for widget in self._sv.walk():
            if isinstance(widget,kivy.garden.matplotlib.FigureCanvasKivyAgg):
                widget.parent.remove_widget(widget)

        ka=FigureCanvasKivyAgg(fig)
        ka.size_hint=(None,None)
        ka.width=2500
        ka.height=2500
        #ka.pos_hint=(1,None)
        self._sv.add_widget(ka)

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

    def save_figure(self,*args):
        print("save_figure:")
        content=SaveDialog(save=self.save_figure_png, cancel=self.dismiss_popup)
        self._popup = Popup(title="Save figure", content=content,
                            size_hint=(0.7, 0.7))
        self._popup.open()

    def on_resize(self, *args):
        self._sv.height=self._vbox2.height-55
        print(self.width,Window.width,self.height,Window.height)
        print(self._vbox2.width,self._vbox2.height, self._vbox.width, self._vbox.height, self._sv.width, self._sv.height)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.currapp=App.get_running_app()

        Builder.load_string(_builderstring)
        btnbg=get_color_from_hex(self.currapp._vc['button.background'])
        btnfg = get_color_from_hex(self.currapp._vc['button.textcolor'])

        # Outer BoxLayout vertical
        vbox2 = FloatLayout(size_hint=(1, 1))

        # Horizontal boxlayout as row 1 of outer vbox2, with two sized buttons as content
        hbox1=BoxLayout(orientation = 'horizontal', size_hint=(1,None), height=50)
        btn1=ColoredButton(btnbg,text="Go Back", size_hint=(None, None), width=60, height=50, color=btnfg)
        btn1.bind(on_press=self.goback)
        btn1.pos_hint={'x': 0, 'top': 1}

        btn2=ColoredButton(btnbg,text="Save figure", size_hint=(None, None), width=100, height=50, color=btnfg)
        btn2.bind(on_press=self.save_figure)
        btn2.pos_hint = {'x': 0.2, 'top': 1}
        vbox2.add_widget(btn1)
        vbox2.add_widget(btn2)

        vbox=BoxLayout(orientation = 'vertical', size_hint=(None,None), height=2500, width=2500)
        vbox.bind(minimum_height=self.setter('height'))

        sv=ScrollView(size_hint=(1, 0.9))
        sv.pos_hint={'x': 0, 'top': 0.9}

        self._vbox=vbox
        self._sv=sv
        self._vbox2=vbox2

        # ScrollViewer within outer vertical box
        vbox2.add_widget(sv)
        # Outer vertical box as child of Screen
        self.add_widget(vbox2)