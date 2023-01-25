# TODO: Transition gridview to be within a scrollview and set meaningful sizes for column headers
# TODO: Possible zoom functionality on KivyFigureCanvasAgg via touch gestures or scrollview.
import kivy.graphics
import numpy as np
from kivy.app import App
from kivy.lang import Builder
from kivy.properties import NumericProperty
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.uix.spinner import Spinner, SpinnerOption
from kivy.uix.textinput import TextInput
import pandas as pd
import re

from kivy.utils import get_color_from_hex


class ColoredButton(Button):
    def __init__(self, bcolor, **kwargs):
        super().__init__(**kwargs)
        self.background_color=(0,0,0,0)
        self.background_normal=''
        self.bgcolor=bcolor
        with self.canvas.before:
            if 'color' in kwargs:
                self.fgcolor = kwargs['color']
                Color(*kwargs['color'])
                self._line=RoundedRectangle(pos=self.pos, size=self.size)
            Color(*bcolor)
            self._rect=RoundedRectangle(pos=self.pos, size=(self.size[0]-1, self.size[1]-1))
        self.bind(pos=self.update_rect, size=self.update_rect)

    def set_bgcolor(self, color):
        print(f"Entered bgcolor: {color}")
        self.bgcolor=color
        self.canvas.before.clear()
        with self.canvas.before:
            if hasattr(self, 'fgcolor'):
                Color(*self.fgcolor)
                self._line=RoundedRectangle(pos=self.pos, size=self.size)
            Color(*color)
            self._rect=RoundedRectangle(pos=self.pos, size=(self.size[0]-1, self.size[1]-1))

    def set_fgcolor(self, color):
        print(f"Entered fgcolor: {color}")
        self.canvas.before.clear()
        self.fgcolor=color
        with self.canvas.before:
            Color(*self.fgcolor)
            self._line=RoundedRectangle(pos=self.pos, size=self.size)
            Color(*self.bgcolor)
            self._rect=RoundedRectangle(pos=self.pos, size=(self.size[0]-1, self.size[1]-1))

    def update_rect(self, *args):
        if hasattr(self,'_line'):
            self._line.pos=self.pos
            self._line.size=self.size
        self._rect.pos=self.pos
        self._rect.size=(self.size[0]-1, self.size[1]-1)


class ColoredLabel(Label):
    def __init__(self, bcolor, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*bcolor)
            self._rect=Rectangle(pos=self.center, size=(self.width/2., self.height/2.))
        self.bind(pos=self.update_rect, size=self.update_rect)


    def set_bgcolor(self, bcolor):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*bcolor)
            self._rect=Rectangle(pos=self.pos, size=self.size)
        # Note that the callback for pos and size remains set and updates self._rect
        self.bind(pos=self.update_rect, size=self.update_rect)


    def update_rect(self, *args):
            self._rect.pos=self.pos
            self._rect.size=self.size

class StyledSpinnerOption(SpinnerOption):
    def update_background(self, key):
        currapp = App.get_running_app()
        self.background_color = get_color_from_hex(currapp._vc[key])

    def update_textcolor(self, key):
        currapp = App.get_running_app()
        self.color = get_color_from_hex(currapp._vc[key])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        currapp=App.get_running_app()
        self.background_normal=''
        self.background_color=get_color_from_hex(currapp._vc['spinner.background'])
        self.color=get_color_from_hex(currapp._vc['spinner.textcolor'])
        currapp.styles.register_callback(self, 'spinner.textcolor', self.update_textcolor)
        currapp.styles.register_callback(self, 'spinner.background', self.update_background)

class BorderBoxLayout(BoxLayout):
    def __init__(self, bcolor, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(bcolor)
            self._rect=Rectangle(pos=self.center, size=(self.width/2., self.height/2.))
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self._rect.pos=self.pos
        self._rect.size=self.size

class DataFrameGridViewRow(BoxLayout):
    def __init__(self, rowdata: list, keys: dict, **kwargs):
        super().__init__(**kwargs)
        self.currapp=App.get_running_app()
        bgcolor=get_color_from_hex(self.currapp._vc['label.background'])
        fgcolor = get_color_from_hex(self.currapp._vc['label.textcolor'])
        self.orientation='horizontal'
        self.size_hint_x=None
        self.bind(minimum_width=self.setter('width'))

        i=0
        if keys is None:
            keys=dict()

        cols=list(keys.keys())

        for item in rowdata:
            boxcolumns=ColoredLabel(bgcolor, color=fgcolor, text=str(item), size_hint_x=None, width=150)
            boxcolumns.halign='left'
            boxcolumns.valign='top'
            self.add_widget(boxcolumns)
            if keys[cols[i]] > 10:
                boxcolumns.width=300
                boxcolumns.text_size=(300,None)
                boxcolumns.height=boxcolumns.texture_size[1]

            i+=1

class DataFrameGridView(BoxLayout):
    start_index = NumericProperty(0)
    screen_size = NumericProperty(10)

    def update_rows(self):
        self._center_layout.clear_widgets()
        lastindex=self.start_index + self.screen_size
        if lastindex >= len(self._df):
            lastindex=len(self._df)

        for rowid in range(self.start_index,lastindex):
            datarow= self._df.iloc[rowid].to_list()
            boxrow=DataFrameGridViewRow(datarow,self.lengths)
            self._center_layout.add_widget(boxrow)

    def navRight(self,*args):
        if (self.start_index+self.screen_size) >= len(self._df):
            if len(self._df) < self.screen_size:
                self.start_index=0
            else:
                self.start_index=len(self._df)-self.screen_size
        else:
            self.start_index += self.screen_size

        self._navIndex.text=str(self.start_index)
        self.update_rows()

    def navLeft(self,*args):
        if self.start_index>=self.screen_size:
            self.start_index -= self.screen_size
        else:
            self.start_index=0
        self.update_rows()
        self._navIndex.text=str(self.start_index)

    def attempt_navigate(self, *args):
        if re.fullmatch("^[0-9]+$",self._navIndex.text) is not None:
            newindex=int(self._navIndex.text)
            if newindex >= len(self._df):
                newindex=max(0,len(self._df)-self.screen_size)
            self._navIndex.text=str(newindex)
            self.update_rows()

    def build_navigation(self) -> BoxLayout:
        navlayout=BoxLayout(orientation='horizontal')
        navlayout.size_hint_y=None
        navlayout.height=50

        rgba=get_color_from_hex(self.currapp._vc['navbutton.background'])
        fgcolor = get_color_from_hex(self.currapp._vc['navbutton.textcolor'])

        butNavLeft = ColoredButton(rgba,text=' < ', color=fgcolor, bold=True, size_hint=(None, None), width=30, height=30)
        butNavLeft.bind(on_press=self.navLeft)

        navlayout.add_widget(butNavLeft)
        navIndex=TextInput(multiline=False, size_hint=(None, None), width=60, height=30, text=str(self.start_index))
        navIndex.halign='center'
        navlayout.add_widget(navIndex)
        self._navIndex=navIndex
        self._navIndex.bind(on_text_validate=self.attempt_navigate)

        butNavRight=ColoredButton(rgba,text=' > ', color=fgcolor, bold=True, size_hint=(None, None), width=30, height=30)
        butNavRight.bind(on_press=self.navRight)
        navlayout.add_widget(butNavRight)
        return navlayout

    def build_column_headers(self):
        boxheaders=BoxLayout(orientation='horizontal', size_hint_x=None)
        boxheaders.bind(minimum_width=boxheaders.setter('width'))
        column_names=self._df.columns.to_list()
        rgba=get_color_from_hex(self.currapp._vc['label.background'])
        fgcolor = get_color_from_hex(self.currapp._vc['label.textcolor'])

        col_len=[]
        for col in column_names:
            col_len.append(len(max(self._df[col].values.astype('str'), key=len)))
            print(col)

        self.lengths = dict(zip(column_names, col_len))

        self.colnames=column_names
        for col in column_names:
            colheader=ColoredLabel(rgba, text=col, color=fgcolor, size_hint=(None,None),
                                   height=50, width=150
                                   )
            if self.lengths[col] > 10:
                colheader.width=300
                colheader.text_size=(300,None)

            boxheaders.add_widget(colheader)
        return boxheaders

    def __init__(self, source: pd.DataFrame, **kwargs):
        super().__init__(**kwargs)
        self.currapp=App.get_running_app()
        self._df=source
        self.orientation='vertical'
        self.size_hint_x=None
        self.size_hint_y=1
        self.bind(minimum_width=self.setter('width'))
        self._center_layout=BoxLayout(orientation='vertical', size_hint_x=None)

        self.add_widget(self.build_column_headers())
        self.add_widget(self._center_layout)
        self._navheader=self.build_navigation()
        self.add_widget(self._navheader)
        self.update_rows()
