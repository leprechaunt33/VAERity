import kivy.graphics
from kivy.lang import Builder
from kivy.properties import NumericProperty
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
import pandas as pd
import re

class ColoredButton(Button):
    def __init__(self, bcolor, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(bcolor)
            self._rect=Rectangle(pos=self.center, size=(self.width/2., self.height/2.))
        self.bind(pos=self.update_rect, size=self.update_rect)


    def update_rect(self, *args):
        self._rect.pos=self.pos
        self._rect.size=self.size

class ColoredLabel(Button):
    def __init__(self, bcolor, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(bcolor)
            self._rect=Rectangle(pos=self.center, size=(self.width/2., self.height/2.))
        self.bind(pos=self.update_rect, size=self.update_rect)


    def update_rect(self, *args):
        self._rect.pos=self.pos
        self._rect.size=self.size

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
    def __init__(self, rowdata: list, **kwargs):
        super().__init__(**kwargs)
        self.orientation='horizontal'
        for item in rowdata:
            boxcolumns=Label()
            boxcolumns.halign='left'
            boxcolumns.valign='top'
            boxcolumns.text=str(item)
            self.add_widget(boxcolumns)

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
            boxrow=DataFrameGridViewRow(datarow)
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

        rgba=[x/255.0 for x in [9,46,91,255]]
        butNavLeft = ColoredButton(rgba,text=' < ')
        butNavLeft.background_color=rgba
        butNavLeft.color=[1,1,1,1]
        butNavLeft.bold=True
        butNavLeft.bind(on_press=self.navLeft)
        butNavLeft.size_hint=(None, None)
        butNavLeft.width=30
        butNavLeft.height = 30

        navlayout.add_widget(butNavLeft)
        navIndex=TextInput(multiline=False)
        navIndex.size_hint_x=None
        navIndex.size_hint_y=None
        navIndex.width=60
        navIndex.height=30
        navIndex.halign='center'
        navIndex.text=str(self.start_index)
        navlayout.add_widget(navIndex)
        self._navIndex=navIndex
        self._navIndex.bind(on_text_validate=self.attempt_navigate)
        butNavRight=ColoredButton(rgba,text=' > ')
        butNavRight.background_color=rgba
        butNavRight.color=[1,1,1,1]
        butNavRight.bold=True
        butNavRight.size_hint=(None, None)
        butNavRight.width=30
        butNavRight.height = 30
        butNavRight.bind(on_press=self.navRight)
        navlayout.add_widget(butNavRight)
        return navlayout

    def build_column_headers(self):
        boxheaders=BoxLayout(orientation='horizontal')
        column_names=self._df.columns.to_list()
        rgba=[x/255.0 for x in [151, 166, 191, 255]]
        for col in column_names:
            colheader=ColoredLabel(rgba)
            colheader.text=col
            colheader.color=[0,0,0,1]
            if len(column_names) <=5:
                colheader.size_hint_x=1/len(column_names)
            colheader.size_hint_y=None
            colheader.height=50
            boxheaders.add_widget(colheader)
        return boxheaders

    def __init__(self, source: pd.DataFrame, **kwargs):
        super().__init__(**kwargs)
        self._df=source
        self.orientation='vertical'
        self._center_layout=BoxLayout(orientation='vertical')
        self.add_widget(self.build_column_headers())
        self.add_widget(self._center_layout)
        self._navheader=self.build_navigation()
        self.add_widget(self._navheader)
        self.update_rows()
