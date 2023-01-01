import math

from kivy.app import App
from kivy.clock import mainthread
from kivy.graphics import Color, Rectangle
from kivy.properties import ObjectProperty, BooleanProperty, NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.core.text import Label as CoreLabel
import re

from kivy.uix.togglebutton import ToggleButton
from kivy.utils import get_color_from_hex


class RegexTextInput(TextInput):
    pass

class RegexTextField(BoxLayout):
    df = ObjectProperty(None)
    colname = StringProperty(None)
    isregex=BooleanProperty(False)
    rebox = ObjectProperty(None)
    tbox=ObjectProperty(None)
    currapp: App = None

    def reset_form(self):
        if self.tbox is not None:
            self.tbox.text=''

        if self.rebox is not None:
            self.rebox.state = 'normal'

    @mainthread
    def set_text(self,text: str):
        self.tbox.text=text

    @mainthread
    def set_isregex(self,isregex):
        if isregex:
            self.rebox.state='down'
        else:
            self.rebox.state='normal'

    def filter_expression(self):
        if self.rebox is None:
            return None

        if self.tbox is None:
            return None

        regex=self.tbox.text
        if regex != '':
            conds=[]
            if self.rebox.state == 'down':
                self.isregex=True
                conds.append(f"str_contains(str_lower({self.colname}),'{str.lower(regex)}')")
            else:
                self.isregex=False
                conds.append(f"str_lower({self.colname})=='{str.lower(regex)}'")
            return ' & '.join(conds)
        else:
            return None

    def update_lrect(self, *args):
        if hasattr(self,'_minrect'):
            self._minrect.pos=(self.tbox.pos[0]+3,self.tbox.pos[1]+self.tbox.size[1]-self._mintext.size[1])

        if hasattr(self,'_resrect'):
            self._resrect.pos=(self.tbox.pos[0]+3,self.tbox.pos[1]-self._restext.size[1])
            self._resrect.size=self._restext.size

        self.tbox.padding=(3,(self.tbox.height-self.tbox.line_height)//2,
                             3, (self.tbox.height - self.tbox.line_height) // 2)


    def update_resultset(self, value: str,*args):
        ressize: int = 0
        fe=self.filter_expression()
        if fe is not None:
            try:
                ressize=len(self.df.filter(fe))
                self._restext.label=f"{ressize} records"
            except Exception as e:
                self._restext.label=f"Query problem"
            self._restext.refresh()
            self._resrect.texture=self._restext.texture
            self._resrect.size=self._restext.texture.size
            print(self._restext.text)

    def on_df(self, instance, value):
        if value is not None:
            try:
                self.tbox.bind(text=self.update_resultset)
                self.rebox.bind(on_press=self.update_resultset,on_release=self.update_resultset)
                with self.tbox.canvas.after:
                    Color(*self.tboxfg)
                    self._mintext=CoreLabel(str('exact match if unchecked, else regex'), font_size=10)
                    self._mintext.refresh()
                    txt=self._mintext.texture
                    self._minrect=Rectangle(size=txt.size,pos=(self.tbox.pos[0],self.tbox.pos[1]+self.tbox.size[1]),texture=txt)
                    self.tbox.bind(size=self.update_lrect, pos=self.update_lrect)

            except:
                pass

    def text(self):
        return self.tbox.text

    def __init__(self, dfcolumn: str, **kwargs):
        super().__init__(**kwargs)
        self.currapp=App.get_running_app()
        self.tboxbg=get_color_from_hex(self.currapp._vc['textbox.background'])
        self.tboxfg = get_color_from_hex(self.currapp._vc['textbox.textcolor'])
        cboxcol = get_color_from_hex(self.currapp._vc['togglebutton.background'])
        self.size_hint_x = 1
        self.colname=dfcolumn
        cbox = ToggleButton(size_hint_y=None, height=25, size_hint_x=None, width=40,
                            allow_no_selection=True, background_color=cboxcol)
        self.rebox=cbox
        self.tbox=RegexTextInput(multiline=False, size_hint_x=1,foreground_color = self.tboxfg,
                                 background_color=self.tboxbg)

        with self.tbox.canvas.after:
            Color(*self.tboxfg)
            self._restext = CoreLabel(str(' '), font_size=10)
            self._restext.refresh()
            txt = self._restext.texture
            self._resrect = Rectangle(size=txt.size, pos=(self.tbox.pos[0], self.tbox.pos[1]),
                                  texture=txt)

        self.add_widget(self.rebox)
        self.add_widget(self.tbox)
