import math

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.splitter import Splitter
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelHeader
from kivy.uix.textinput import TextInput
from kivy.utils import get_color_from_hex
from dataframegridview import ColoredButton, ColoredLabel
from kivy.app import App
#from rootwindow import RootWindow

class ModularDataset:
    rf = []
    orig_cls = None
    currapp = None
    ids: dict = None
    resolvers: dict = None
    ref_resolvers: dict = None
    ref_funcs: dict = None
    field_order: dict = None

    def __init__(self, origin, record_format):
        self.currapp=App.get_running_app()
        self.ids = dict()
        self.formulas = dict()
        self.resolvers = dict()
        self.field_order=dict()
        self.ref_resolvers= dict()
        self.ref_funcs=dict()
        self.orig_cls = origin
        if record_format is None:
            raise ValueError("Please supply the record format")

        if isinstance(record_format, list):
            self.rf = record_format
            self.content=self.generate_content()

    def formatmissing(self,val):
        if val is None:
            return "Not Provided"

        if isinstance(val,float):
            if math.isnan(val):
                return "Not Provided"

            return str(int(val))

        if str(val) == '':
            return "Not Provided"

        return str(val)

    def boolformat(self, boolval, truthval = 'Yes', falseval='No', npval = 'Not Provided'):
        if boolval is None:
            return npval

        if isinstance(boolval,float):
            if math.isnan(boolval):
                return npval
        if str(boolval) == '':
            return falseval

        if str(boolval) == 'Y':
            return truthval


    def formula(self,f: str, r, caller, ref=False):
        if ref:
            formulaz=self.ref_funcs
            resolverz=self.ref_resolvers
        else:
            formulaz=self.formulas
            resolverz=self.resolvers

        if f in formulaz:
            res=resolverz.get(f, 'self')
            frm=formulaz[f]
            if frm[0:3] == 'fm:':
                wrapperfunc=self.formatmissing
                frm=frm[3:]
            elif frm[0:3] == 'bf:':
                wrapperfunc=self.boolformat
                frm=frm[3:]
            else:
                # First, try to resolve the formula as a custom function
                # in the caller module.  At the moment only the caller as
                # the resolver is supported,
                if (caller is not None) and (res == 'self'):
                    # Don't attempt to resolve ref funcs for binding in self,
                    # this is a special case.
                    if ref and isinstance(caller,type(self)):
                        caller = self.orig_cls
                    if hasattr(caller,frm):
                        wf=getattr(caller,frm)
                        if ref:
                            return wf
                        else:
                            return wf(r, f, self)
                elif (self.orig_cls is not None) and (res == 'origin'):
                    if hasattr(self.orig_cls,frm):
                        wf=getattr(self.orig_cls,frm)
                        if ref:
                            return wf
                        else:
                            return wf(r, f, self)
                    else:
                        raise ValueError(f"Could not resolve {frm} via {self.orig_cls}!")
                else:
                    if frm in r:
                        return r[frm]
                    else:
                        return frm

            if frm in r:
                return wrapperfunc(r[frm])
            else:
                return frm

        else:
            raise KeyError(f"No formula named '{f}'!")

    def generate_content(self, rf = None, stylekeys = None):
        if rf is None:
            rf = self.rf

        rc = []

        if isinstance(rf,dict):
            rf = [rf]

        for item in rf:
            if 'splitter' in rf:
                if rf['splitter'] is not None:
                    splitr=Splitter()
                    splitr.sizable_from=rf['splitter']
                else:
                    splitr=None
            else:
                splitr=None

            if 'type' in item:
                if item['type'] == 'table':
                    outerLayout=GridLayout(cols=2*item['cols'], rows=item['rows'])
                    hdrbg=item['stylekeys'][0]
                    hdrfg=item['stylekeys'][1]
                    labelbg=item['stylekeys'][2]
                    labelfg = item['stylekeys'][3]
                    if 'kwargs' in item:
                        kwa=item['kwargs']
                    else:
                        kwa={}

                    for entry in item['content']:
                        children=self.generate_content(entry, item['stylekeys'])
                        for child in children:
                            outerLayout.add_widget(child)

                    if splitr is not None:
                        splitr.add_widget(outerLayout)
                        rc.append(splitr)
                    else:
                        rc.append(outerLayout)
                elif item['type'] == 'tabgroup':
                    tpanel = TabbedPanel(do_default_tab=False)
                    for tph in item['content']:
                        content = self.generate_content(tph['content'], item.get('stylekeys', []))
                        tph1 = TabbedPanelHeader(text=tph['header'])
                        if len(content) == 1:
                            tph1.content = content[0]
                        else:
                            vbox1=BoxLayout(orientation = 'vertical')
                            for widget in content:
                                vbox1.add_widget(widget)
                            tph1.content=vbox1
                        tpanel.add_widget(tph1)
                    if splitr is not None:
                        splitr.add_widget(tpanel)
                        rc.append(splitr)
                    else:
                        rc.append(tpanel)
                elif item['type'] == 'hbox':
                    hbox1=BoxLayout(orientation='horizontal')
                    content = self.generate_content(item['content'], item.get('stylekeys', []))
                    for c in content:
                        hbox1.add_widget(c)

                    if splitr is not None:
                        splitr.add_widget(hbox1)
                        rc.append(splitr)
                    else:
                        rc.append(hbox1)
                else:
                    raise ValueError(f"Item of type '{item['type']}' is unsupported layout!")
            else:
                # No type.  Therefore it must be a label or textarea or other
                # supported content field
                print(f"Hit no type, rf is {rf}")
                if 'label' in item:
                    sk=item.get('stylekeys', None)
                    if sk is not None:
                        bgcolor, = stylekeys[0:1] or ['']
                        fgcolor, = stylekeys[1:2] or ['']
                    else:
                        bgcolor, = stylekeys[2:3] or ['']
                        fgcolor, = stylekeys[3:4] or ['']

                    kwa=item.get('kwargs', {}).copy()

                    if not item.get('labelonly', False):
                        if len(fgcolor) > 0:
                            kwa['color'] = get_color_from_hex(self.currapp._vc[fgcolor])
                        if len(bgcolor) > 0:
                            cell1=ColoredLabel(get_color_from_hex(self.currapp._vc[bgcolor]),text=item['label'], **kwa)
                        else:
                            cell1=Label(text=item['label'], **kwa)

                        rc.append(cell1)

                    if sk is not None:
                        bgcolor, = stylekeys[0:1] or [None]
                        fgcolor, = stylekeys[1:2] or [None]
                    else:
                        bgcolor, = stylekeys[4:5] or [None]
                        fgcolor, = stylekeys[5:6] or [None]

                    kwa = item.get('kwargs', {}).copy()
                    if fgcolor is not None:
                        kwa['color'] = get_color_from_hex(self.currapp._vc[fgcolor])
                    if bgcolor is not None:
                        cell2 = ColoredLabel(get_color_from_hex(self.currapp._vc[bgcolor]), text=item['label'], **kwa)
                    else:
                        cell2 = Label(text=item['label'], **kwa)

                    rc.append(cell2)
                    if 'id' in item:
                        self.ids[item['id']]=cell2
                        self.field_order[item['id']]=len(self.ids)-1
                        self.formulas[item['id']]=item.get('formula','')
                        self.resolvers[item['id']]=item.get('resolver','')
                        self.ref_resolvers[item['id']] = item.get('ref_resolver', '')
                        self.ref_funcs[item['id']]=item.get('ref_func', '')
                        if 'ref_func' in item:
                            rfunc=self.formula(item['id'], {}, self, ref=True)
                            print(f"ref_func is {rfunc}")
                            cell2.bind(on_ref_press=rfunc)
                            self.ids[item['id']].markup = True
                    else:
                        print(f"Could not find id in {item}")
                elif 'textinput' in item:
                    bgcolor= get_color_from_hex(self.currapp._vc['textbox.background'])
                    fgcolor = get_color_from_hex(self.currapp._vc['textbox.textcolor'])
                    kwa=item.get('kwargs', {}).copy()
                    if fgcolor is not None:
                        kwa['foreground_color'] = fgcolor
                    if bgcolor is not None:
                        kwa['background_color'] = bgcolor

                    cell1=TextInput(**kwa)
                    rc.append(cell1)

                    if 'id' in item:
                        self.ids[item['id']]=cell1
                        self.field_order[item['id']]=len(self.ids)-1
                        self.formulas[item['id']]=item.get('formula','')
                        self.resolvers[item['id']]=item.get('resolver','')
                        self.ref_resolvers[item['id']] = item.get('ref_resolver', '')
        return rc