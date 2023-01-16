import os
import datetime
from datetime import timedelta, datetime
import time
import kivy.garden.matplotlib
from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import ObjectProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.utils import get_color_from_hex
from matplotlib import pyplot as plt
from matplotlib.axis import YAxis, XAxis
from matplotlib.collections import PolyCollection
from matplotlib.patches import Rectangle

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
    current_figure = NumericProperty(0)
    current_axis = NumericProperty(0)
    argument: str = ''

    def scroll_to_current_graph(self):
        currfig: plt.Figure = self.figs[self.current_figure]
        ax: plt.Axes = currfig.axes[self.current_axis]
        (l, b, w, h) = ax.get_position().bounds
        (figsizex, figsizey) = currfig.get_size_inches()
        dpi = currfig.get_dpi()
        uppery = figsizey * dpi * (1-(b - h))
        leftx = figsizex * dpi * l
        print(f"figsize {figsizex}, {figsizey} dpi {dpi} ax is {l},{b}, {w} x {h}")
        print(f"Calculated coordinates are {leftx},{uppery}")
        #self._sv.scroll_x = 0
        #self._sv.scroll_y = 0
        dScrollX, dScrollY=self._sv.convert_distance_to_scroll(leftx,uppery)
        self._sv.scroll_x = float(l)
        self._sv.scroll_y = float(b)

    def handle_keyboard(self, window, key, scancode, codepoint, modifier, keyname):
        statscreen=self
        currfig: plt.Figure = statscreen.figs[statscreen.current_figure]
        ax: plt.Axes = currfig.axes[statscreen.current_axis]
        (xmin, xmax) = ax.get_xlim()
        if (keyname == ']') and ('ctrl' in modifier):
            xdata = statscreen.xdata[statscreen.current_figure][statscreen.current_axis]
            if isinstance(xdata[0], datetime):
                epoch = time.mktime(time.localtime(0))
                dt1 = datetime.fromtimestamp(epoch)
                dt2 = dt1 + timedelta(days=xmin)
                xmin = dt2
            else:
                print(f'Type of data is {type(xdata[0])}\nValue is xdata[0]')
            print(f"Searching for  x > {xmin}")

            if isinstance(xdata[0], str):
                barposn = xmax + 1
                for child in ax.patches:
                    if isinstance(child, Rectangle):
                        w = child.get_width()
                        x = child.get_x() + w / 2
                        # We iterate
                        if x > xmin:
                            barposn = min(x, barposn)
                if barposn != xmax + 1:
                    newxmin = barposn
            else:
                newxmin = min([x for x in xdata if x > xmin])
            print(f"Found {newxmin}")
            if isinstance(xdata[0], datetime):
                tdelta: timedelta = newxmin - dt1
                newxmin = tdelta.days + (tdelta.seconds / 86400) + (datetime.now() - datetime.utcnow()).seconds / 86400
            print(f"] setting xmin,xmax to {newxmin},{xmax}, previous is {xmin}")
            ax.set_xlim(newxmin, xmax)
            sv: ScrollView = statscreen._sv
            sv.children[0].draw()
            statscreen.update_graphinfo()
        elif (keyname == '[') and ('ctrl' in modifier):
            xdata = statscreen.xdata[statscreen.current_figure][statscreen.current_axis]
            if isinstance(xdata[0], datetime):
                epoch = time.mktime(time.localtime(0))
                dt1 = datetime.fromtimestamp(epoch)
                dt2 = dt1 + timedelta(days=xmax)
                xmax = dt2
                tdeltasecs = (datetime.now() - datetime.utcnow()).seconds
                xmax = xmax - timedelta(seconds=tdeltasecs)

            if isinstance(xdata[0], str):
                barposn = 0
                for child in ax.patches:
                    if isinstance(child, Rectangle):
                        w = child.get_width()
                        x = child.get_x() + w / 2
                        if x < xmax:
                            if x > barposn:
                                barposn = x
                if barposn != 0:
                    newxmax = barposn
            else:
                newxmax = max([x for x in xdata if x < xmax])

            if isinstance(xdata[0], datetime):
                tdelta: timedelta = newxmax - dt1
                newxmax = tdelta.days + (tdelta.seconds / 86400) + (datetime.now() - datetime.utcnow()).seconds / 86400
            print(f"[ setting xmin,xmax is {xmin},{newxmax}, previous is {xmax}")
            ax.set_xlim(xmin, newxmax)
            sv: ScrollView = statscreen._sv
            sv.children[0].draw()
            statscreen.update_graphinfo()
        elif (keyname in '0123456789') and ('ctrl' in modifier):
            graphnum = int(keyname)
            statscreen.current_axis = graphnum
            statscreen.update_graphinfo()
        elif (keyname in '0123456789.-') and (len(modifier) == 0):
            self.argument += keyname
            self.update_graphinfo()
        elif (keyname == 'c') and ('ctrl' in modifier):
            self.argument=''
            self.update_graphinfo()
        elif (keyname == 'l') and ('ctrl' in modifier):
            ax.set_xlim(xmin=float(self.argument))
            self._sv.children[0].draw()
            self.argument = ''
            self.update_graphinfo()
        elif (keyname == 'r') and ('ctrl' in modifier):
            ax.set_xlim(xmax=float(self.argument))
            self._sv.children[0].draw()
            self.argument = ''
            self.update_graphinfo()
        elif (keyname == 'u') and ('ctrl' in modifier):
            ax.set_ylim(ymax=float(self.argument))
            self._sv.children[0].draw()
            self.argument = ''
            self.update_graphinfo()
        elif (keyname == 'd') and ('ctrl' in modifier):
            ax.set_ylim(ymin=float(self.argument))
            self._sv.children[0].draw()
            self.argument = ''
            self.update_graphinfo()
        elif (keyname == 'f') and ('ctrl' in modifier):
            self.scroll_to_current_graph()
        elif (keyname == 'e') and ('ctrl' in modifier):
            (l, b, w, h) = ax.get_position().bounds
            print(f"Scroll position {self._sv.scroll_x},{self._sv.scroll_y}, left bottom is {l} {b}")
            print(f"Difference {self._sv.scroll_x-l},{self._sv.scroll_y-b}")
        elif all(m in modifier for m in ['ctrl', 'alt']) and codepoint == 'n':
            statscreen.current_figure=(statscreen.current_figure+1) % len(statscreen.figs)
        elif keyname == 'right':
            if modifier == ['ctrl']:
                statscreen._sv.scroll_x = min(statscreen._sv.scroll_x + 1 / 25, 1)
            else:
                statscreen._sv.scroll_x = min(statscreen._sv.scroll_x + 1 / 250, 1)
        elif keyname == 'left':
            if modifier == ['ctrl']:
                statscreen._sv.scroll_x = max(statscreen._sv.scroll_x - 1 / 25, 0)
            else:
                statscreen._sv.scroll_x = max(statscreen._sv.scroll_x - 1 / 250, 0)
        elif keyname == 'up':
            statscreen._sv.scroll_y = min(statscreen._sv.scroll_y + 1 / 250, 1)
        elif keyname == 'down':
            statscreen._sv.scroll_y = max(statscreen._sv.scroll_y - 1 / 250, 0)
        elif keyname == 'pageup':
            statscreen._sv.scroll_y = min(statscreen._sv.scroll_y + 1 / 25, 1)
        elif keyname == 'pagedown':
            statscreen._sv.scroll_y = max(statscreen._sv.scroll_y - 1 / 25, 0)

    def goback(self, *args):
        self.currapp.manager.current = 'resultscreen'

    def clear_scrollview(self):
        for widget in self._sv.walk():
            if isinstance(widget,kivy.garden.matplotlib.FigureCanvasKivyAgg):
                widget.parent.remove_widget(widget)

    def select_graph(self, instance, text):
        graphnum=int(text[0])
        fig=self.figs[self.current_figure]
        if graphnum > len(fig.axes):
            return

        self.current_axis = graphnum
        self.update_graphinfo()

    def set_figure(self,fig, xdata):
        self.clear_scrollview()

        if isinstance(fig,list):
            ka = FigureCanvasKivyAgg(fig[0])
            ka.size_hint = (None, None)
            ka.width = int(fig[self.current_figure].get_dpi() * fig[self.current_figure].get_figwidth())
            ka.height = int(fig[self.current_figure].get_dpi() * fig[self.current_figure].get_figwidth())
            self._sv.add_widget(ka)
            self.figs=fig
            self.xdata=xdata
        else:
            ka=FigureCanvasKivyAgg(fig)
            ka.size_hint=(None,None)
            ka.width=int(fig.get_dpi()* fig.get_figwidth())
            ka.height=int(fig.get_dpi()* fig.get_figwidth())
            self._sv.add_widget(ka)
            self.figs=[fig]

        self.spinner_options=[]

        for figure in self.figs:
            spinnervals=[]
            for i, ax in enumerate(figure.axes):
                xlab=ax.get_xlabel()
                ylab=ax.get_ylabel()
                title=ax.get_title()
                (ymin, ymax) = ax.get_ylim()
                if title == '':
                    if (xlab == '') or (ylab == ''):
                        title=f"Untitled graph with y bounds {ymin}, {ymax} "
                    else:
                        title=f"{xlab} vs {ylab}"

                spinnervals.append(f"{i}: {title}")
            self.spinner_options.append(spinnervals)
        # Because setting the figure implies our list of figures may have changed,
        # call on_current_figure to make sure the available graphs are updated.
        self.on_current_figure(None, self.current_figure)

    def update_graphinfo(self):
        currfig: plt.Figure = self.figs[self.current_figure]
        ax: plt.Axes = currfig.axes[self.current_axis]
        (xmin, xmax) = ax.get_xlim()
        (ymin, ymax) = ax.get_ylim()

        self.ids['graphinfo'].text = f"""
Figure {self.current_figure+1} selected    Graph {self.current_axis} selected
X bounds: {xmin:.3f}, {xmax:.3f} ([ref=xreset]Reset[/ref])     Y Bounds: {ymin:.3f}, {ymax:.3f} ([ref=yreset]Reset[/ref])   Arg {self.argument}
X label: {ax.get_xlabel()}        Y label: {ax.get_ylabel()}
"""

    def on_current_figure(self, instance, value):
        self.clear_scrollview()
        ka = FigureCanvasKivyAgg(self.figs[value])
        ka.size_hint = (None, None)
        ka.width = int(self.figs[value].get_dpi() * self.figs[value].get_figwidth())
        ka.height = int(self.figs[value].get_dpi() * self.figs[value].get_figwidth())
        self._sv.add_widget(ka)

        # Reset the current axis to ensure sanity of graph operations
        self.current_axis = 0
        if self.spinner_options is not None:
            self.ids['graphspinner'].values = self.spinner_options[self.current_figure]
            self.ids['graphspinner'].text=self.spinner_options[self.current_figure][self.current_axis]
        self.update_graphinfo()

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

    def process_ref(self, instance, value):
        print(f"process_ref {value}")
        if value == 'xreset':
            ax=self.figs[self.current_figure].axes[self.current_axis]
            xd=self.xdata[self.current_figure][self.current_axis]
            if isinstance(xd[0], str):
                xvals=[]
                wvals=[]
                for patch in ax.patches:
                    if isinstance(patch, Rectangle):
                        xvals.append(patch.get_x())
                        wvals.append(patch.get_width())
                xmin=min(xvals)
                xmax=max([x+wvals[w] for w, x in enumerate(xvals)])
            else:
                xmin=min(self.xdata[self.current_figure][self.current_axis])
                xmax=max(self.xdata[self.current_figure][self.current_axis])
            ax.set_xlim(xmin,xmax)
            self._sv.children[0].draw()
            self.update_graphinfo()
        elif value == 'yreset':
            xmin=min(self.xdata[self.current_figure][self.current_axis])
            xmax=max(self.xdata[self.current_figure][self.current_axis])
            ax=self.figs[self.current_figure].axes[self.current_axis]
            (xliml, xlimr) = ax.get_xlim()
            figgypudding: plt.Axes =  ax
            yax: YAxis=figgypudding.yaxis
            xax: XAxis=figgypudding.xaxis

            ymax=0

            for j, coll in enumerate(figgypudding.collections):
                print(f"{j} {type(coll)} {len(coll.get_children())}")
                if isinstance(coll, PolyCollection):
                    for k, obj in enumerate(coll.get_paths()):
                        print(f"\t{k}, {type(obj)}")
                        if hasattr(obj, 'vertices'):
                            print(f"\t\tvertices {len(obj.vertices)} on Path")
                            for vertex in obj.vertices:
                                if (vertex[0] >= xliml) and (vertex[0] <= xlimr):
                                    if ymax < vertex[1]:
                                        ymax=vertex[1]
                #elif isinstance(coll, )

            print(f"yaxis has {len(yax.get_children())} children")
            print(f"xaxis has {len(xax.get_children())} children")
            for child in yax.get_children():
                print(f"{type(child)}", end=' ')
            for child in xax.get_children():
                print(f"{type(child)}", end=' ')

            print(f"There are {figgypudding.patches} patches on the axes")
            for child in figgypudding.patches:
                if isinstance(child, Rectangle):
                    h=child.get_height()
                    x=child.get_x()
                    if (x>=xliml) and (x<=xlimr):
                        if h>ymax:
                            ymax=h

            print(f"Determined calculated ymax should be {ymax*1.05}")
            if ymax > 0:
                ax.set_ylim(0,ymax*1.05)
                self._sv.children[0].draw()
                self.update_graphinfo()

    def on_resize(self, *args):
        self._sv.height=self._vbox2.height-55
        print(self.width, Window.width, self.height, Window.height)
        print(self._vbox2.width, self._vbox2.height, self._vbox.width, self._vbox.height, self._sv.width, self._sv.height)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.figs = None
        self.currapp = App.get_running_app()

        Builder.load_string(_builderstring)
        btnbg = get_color_from_hex(self.currapp._vc['button.background'])
        btnfg = get_color_from_hex(self.currapp._vc['button.textcolor'])
        lblfg = get_color_from_hex(self.currapp._vc['label.textcolor'])

        # Outer BoxLayout vertical
        vbox2 = FloatLayout(size_hint=(1, 1))

        # Horizontal boxlayout as row 1 of outer vbox2, with two sized buttons as content
        hbox1=BoxLayout(orientation = 'horizontal', size_hint=(1,None), height=50)
        btn1=ColoredButton(btnbg,text="Go Back", size_hint=(None, None), width=60, height=50, color=btnfg)
        btn1.bind(on_press=self.goback)
        btn1.pos_hint={'x': 0, 'top': 1}

        btn2=ColoredButton(btnbg,text="Save figure", size_hint=(None, None), width=100, height=50, color=btnfg)
        btn2.bind(on_press=self.save_figure)
        btn2.pos_hint = {'x': 0.1, 'top': 1}

        lbl3=Label(size_hint=(0.4,None), height=50, color = lblfg, markup = True)
        lbl3.bind(on_ref_press = self.process_ref)
        self.ids['graphinfo']=lbl3
        lbl3.pos_hint={'x': 0.2, 'top': 1}

        spinner4=Spinner(size_hint=(0.2,None), height=50)
        spinner4.bind(text = self.select_graph)
        spinner4.pos_hint = {'x': 0.7, 'top': 1}
        self.ids['graphspinner']=spinner4

        vbox2.add_widget(btn1)
        vbox2.add_widget(btn2)
        vbox2.add_widget(lbl3)
        vbox2.add_widget(spinner4)

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