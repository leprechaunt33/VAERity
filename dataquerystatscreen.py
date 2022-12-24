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
        for widget in self._vbox.walk():
            if isinstance(widget,kivy.garden.matplotlib.FigureCanvasKivyAgg):
                self._vbox.remove_widget(widget)

        ka=FigureCanvasKivyAgg(fig)
        ka.size_hint=(None,None)
        ka.width=1600
        ka.height=1200
        self._vbox.add_widget(ka)

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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.currapp=App.get_running_app()

        #Factory.register('LoadDialog', cls=LoadDialog)
        #Factory.register('SaveDialog', cls=SaveDialog)
        Builder.load_string(_builderstring)

        vbox=BoxLayout(orientation = 'vertical', size_hint=(None,None), height=1300, width=1600)
        vbox.bind(minimum_height=self.setter('height'))
        hbox1=BoxLayout(orientation = 'horizontal')
        btn1=ColoredButton([0.15,0.15,0.15,1],text="Go Back", size_hint=(None, None), width=60, height=50)
        btn1.bind(on_press=self.goback)
        hbox1.add_widget(btn1)

        btn2=ColoredButton([0.15,0.15,0.15,1],text="Save figure", size_hint=(None, None), width=100, height=50)
        btn2.bind(on_press=self.save_figure)
        hbox1.add_widget(btn2)

        vbox.add_widget(hbox1)

        sv=ScrollView(size_hint=(1, None), size=(Window.width, Window.height))
        sv.add_widget(vbox)

        self._vbox=vbox
        self.add_widget(sv)