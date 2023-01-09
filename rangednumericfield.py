import math
from kivy.app import App
from kivy.graphics import Color, Rectangle
from kivy.properties import ObjectProperty, BooleanProperty, NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.core.text import Label as CoreLabel
import re

from kivy.utils import get_color_from_hex


class NumericTextInput(TextInput):
    pat = re.compile('[^0-9]')
    def insert_text(self, substring, from_undo=False):
        pat = self.pat
        if '.' in self.text:
            s = re.sub(pat, '', substring)
        else:
            s = '.'.join(
                re.sub(pat, '', s)
                for s in substring.split('.', 1)
            )


        return super().insert_text(s, from_undo=from_undo)

class RangedNumericField(BoxLayout):
    df = ObjectProperty(None)
    colname = StringProperty(None)
    lowerbound=NumericProperty(math.nan)
    upperbound=NumericProperty(math.nan)
    lbound=ObjectProperty(None)
    ubound = ObjectProperty(None)
    _min: float = math.nan
    _max: float = math.nan
    currapp: App = None

    def reset_form(self):
        self.ubound.text=''
        self.lbound.text=''

    def filter_expression(self):
        ubexists=self.ubound.text.isnumeric()
        lbexists=self.lbound.text.isnumeric()
        self.ubound.text=re.sub('^0([0-9])','\\1',self.ubound.text)
        self.lbound.text=re.sub('^0([0-9])','\\1',self.lbound.text)
        if ubexists or lbexists:
            conds=[]
            if ubexists:
                conds.append(f"({self.colname} <= {self.ubound.text})")

            if lbexists:
                conds.append(f"({self.colname} >= {self.lbound.text})")

            return ' & '.join(conds)
        else:
            return None
    def update_lrect(self, *args):
        if hasattr(self,'_minrect'):
            self._minrect.pos=(self.lbound.pos[0]+3,self.lbound.pos[1]+self.lbound.size[1]-self._mintext.size[1])

        if hasattr(self,'_resrect'):
            self._resrect.pos=(self.lbound.pos[0]+3,self.lbound.pos[1]-self._restext.size[1])
            self._resrect.size=self._restext.size

        self.lbound.padding=(3,(self.lbound.height-self.lbound.line_height)//2,
                             3, (self.lbound.height - self.lbound.line_height) // 2)

    def update_urect(self, *args):
        if hasattr(self,'_minrect'):
            self._maxrect.pos=(self.ubound.pos[0]+3,self.ubound.pos[1]+self.ubound.size[1]-self._maxtext.size[1])
        self.ubound.padding = (3,(self.ubound.height - self.ubound.line_height) // 2,
                               3, (self.ubound.height - self.ubound.line_height) // 2)

    def update_resultset(self, value: str,*args):
        ubexists=self.ubound.text.isnumeric()
        lbexists=self.lbound.text.isnumeric()
        self.ubound.text=re.sub('^0([0-9])','\\1',self.ubound.text)
        self.lbound.text=re.sub('^0([0-9])','\\1',self.lbound.text)
        ressize: int = 0
        if ubexists or lbexists:
            conds=[]
            if ubexists:
                conds.append(f"({self.colname} <= {self.ubound.text})")

            if lbexists:
                conds.append(f"({self.colname} >= {self.lbound.text})")

            if len(conds) > 0:
                ressize=len(self.df.filter(' & '.join(conds)))
                self._restext.label=f"{ressize} records"
                self._restext.refresh()
                self._resrect.texture=self._restext.texture
                self._resrect.size=self._restext.texture.size
                print(self._restext.text)

    def on_df(self, instance, value):
        if value is not None:
            try:
                (_min, _max)=self.df.minmax(self.colname)
                self.ubound.bind(text=self.update_resultset)
                self.lbound.bind(text=self.update_resultset)
                if not math.isnan(_min):
                    with self.lbound.canvas.after:
                        Color(*self.tboxfg)
                        self._mintext=CoreLabel(str(_min), font_size=10)
                        self._mintext.refresh()
                        txt=self._mintext.texture
                        self._minrect=Rectangle(size=txt.size,pos=(self.lbound.pos[0],self.lbound.pos[1]+self.lbound.size[1]),texture=txt)
                        self.lbound.bind(size=self.update_lrect, pos=self.update_lrect)

                if not math.isnan(_min):
                    with self.ubound.canvas.after:
                        Color(*self.tboxfg)
                        self._maxtext = CoreLabel(str(_max), font_size=10)
                        self._maxtext.refresh()
                        txt = self._maxtext.texture
                        self._maxrect = Rectangle(size=txt.size, pos=(self.lbound.pos[0]+3,self.lbound.pos[1]+self.lbound.size[1]),texture=txt)
                        self.ubound.bind(size=self.update_urect, pos=self.update_urect)
            except:
                pass

    def __init__(self, dfcolumn: str, **kwargs):
        super().__init__(**kwargs)
        self.currapp=App.get_running_app()
        self.tboxbg=get_color_from_hex(self.currapp._vc['textbox.background'])
        self.tboxfg = get_color_from_hex(self.currapp._vc['textbox.textcolor'])
        self.colname=dfcolumn
        self.lbound=NumericTextInput(multiline=False, size_hint_x=None, width='70dp',
                                     foreground_color = self.tboxfg, background_color=self.tboxbg)
        self.ubound=NumericTextInput(multiline=False, size_hint_x=None, width='70dp',
                                     foreground_color = self.tboxfg, background_color=self.tboxbg)

        with self.ubound.canvas.after:
            Color(*self.tboxfg)
            self._restext = CoreLabel(str(' '), font_size=10)
            self._restext.refresh()
            txt = self._restext.texture
            self._resrect = Rectangle(size=txt.size, pos=(self.lbound.pos[0], self.lbound.pos[1]),
                                  texture=txt)

        self.add_widget(self.lbound)
        self.add_widget(self.ubound)
