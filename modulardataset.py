import datetime
from dataclasses import dataclass, field
import math, re
import os.path
import xml.sax
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.splitter import Splitter
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelHeader
from kivy.uix.textinput import TextInput
from kivy.utils import get_color_from_hex
from dataframegridview import ColoredButton, ColoredLabel
from kivy.app import App

@dataclass
class MDField:
    """Class for describing the fields of the datasets that VAERity manages"""
    name: str
    type: type
    iskey: bool
    allowna: bool
    description: str
    groups: list[str] = field(default_factory=list)
    dateformat: str = ''
    maxlength: int = -1

@dataclass
class MDDataTable:
    name: str
    multiplefiles: bool = False
    fields: list[MDField] = field(default_factory=list)
    groups: dict = field(default_factory=dict)

    def get_group(self, group: str) -> list[MDField]:
        if group in self.groups:
            return self.groups[group]
        else:
            return None

    def add_to_group(self, group, field):
        if group not in self.groups:
            self.groups[group]=list()

        if field not in self.groups[group]:
            self.groups[group].append(field)

    def add_field(self, field: MDField):
        self.fields.append(field)
        print(f"Adding {field} to groups")
        for group in field.groups:
            self.add_to_group(group, field)

class ModularDataset:
    rf = []
    orig_cls = None
    currapp = None
    ids: dict = None
    resolvers: dict = None
    ref_resolvers: dict = None
    ref_funcs: dict = None
    field_order: dict = None
    dsid: str = None
    module: str = None

    def __init__(self, origin, record_format, dsid):
        self.currapp=App.get_running_app()
        self.stylekeys = dict()
        self.ids = dict()
        self.labels = dict()
        self.formulas = dict()
        self.resolvers = dict()
        self.field_order=dict()
        self.ref_resolvers= dict()
        self.ref_funcs=dict()
        self.orig_cls = origin
        self.dsid = dsid
        self.datatables = dict()
        if record_format is None:
            raise ValueError("Please supply the record format")

        if isinstance(record_format, list):
            self.rf = record_format
            self.content=self.generate_content()

        datasets=os.path.join(os.path.dirname(__file__), 'datasets')
        self.xmlfile=os.path.join(datasets, f"{self.dsid}.xml")
        if os.path.exists(self.xmlfile):
            self.mdparser=DatasetParser(self)
            xml.sax.parse(self.xmlfile, self.mdparser)

    def find_field_by_description(self, description):
        for table in self.datatables.values():
            results = [f for f in table.fields if f.description == description]
            if len(results) > 0:
                return (table.name, results[0])

        return None

    def find_field(self, name):
        for table in self.datatables.values():
            results=[f for f in table.fields if f.name == name]
            if len(results) > 0:
                return (table.name, results[0])

        return None

    def set_stylekey(self, element, key):
        if key is None:
            return
        if key == '':
            return

        if key not in self.stylekeys:
            self.stylekeys[key]=[]
            self.currapp.styles.register_callback(self, key, self.style_callback)

        self.stylekeys[key].append(element)

    def style_callback(self, key):
        if key == 'textbox.background':
            for id in self.ids.keys():
                if isinstance(self.ids[id],TextInput):
                    self.ids[id].background_color = get_color_from_hex(self.currapp._vc[key])
            return
        elif key == 'textbox.textcolor':
            for id in self.ids.keys():
                if isinstance(self.ids[id],TextInput):
                    self.ids[id].foreground_color = get_color_from_hex(self.currapp._vc[key])
            return

        if key in self.stylekeys:
            for element in self.stylekeys[key]:
                if re.fullmatch(r'^\w+\.textcolor$',key):
                    element.color = get_color_from_hex(self.currapp._vc[key])
                elif re.fullmatch(r'^\w+\.background$',key):
                    if isinstance(element, ColoredLabel):
                        element.set_bgcolor(get_color_from_hex(self.currapp._vc[key]))
                else:
                    print(f"Unable to match unknown key {key}")

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
            if 'splitter' in item:
                if item['splitter'] is not None:
                    splitr=Splitter()
                    splitr.sizable_from=item['splitter']
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
                #print(f"Hit no type, rf is {rf}")
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
                        self.set_stylekey(cell1, fgcolor)
                        self.set_stylekey(cell1, bgcolor)

                    if sk is not None:
                        bgcolor, = stylekeys[0:1] or [None]
                        fgcolor, = stylekeys[1:2] or [None]
                    else:
                        bgcolor, = stylekeys[0:1] or [None]
                        fgcolor, = stylekeys[1:2] or [None]

                    kwa = item.get('kwargs', {}).copy()
                    if fgcolor is not None:
                        kwa['color'] = get_color_from_hex(self.currapp._vc[fgcolor])
                    if bgcolor is not None:
                        cell2 = ColoredLabel(get_color_from_hex(self.currapp._vc[bgcolor]), text=item['label'], **kwa)
                    else:
                        cell2 = Label(text=item['label'], **kwa)

                    rc.append(cell2)
                    self.set_stylekey(cell2, fgcolor)
                    self.set_stylekey(cell2, bgcolor)

                    if 'id' in item:
                        self.ids[item['id']]=cell2
                        if not 'labelonly' in item:
                            self.labels[item['id']]=cell1
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
                    self.set_stylekey(cell1, 'textbox.background')
                    self.set_stylekey(cell1, 'textbox.textcolor')
                    rc.append(cell1)

                    if 'id' in item:
                        self.ids[item['id']]=cell1
                        self.field_order[item['id']]=len(self.ids)-1
                        self.formulas[item['id']]=item.get('formula','')
                        self.resolvers[item['id']]=item.get('resolver','')
                        self.ref_resolvers[item['id']] = item.get('ref_resolver', '')
        return rc

class DatasetParser(xml.sax.ContentHandler):
    currenttag: str = None
    def __init__(self, md: ModularDataset):
        self.md = md
        self.currenttag = ''
        self.seenmodular = False

    def handle_field(self, tag, attributes):
        if 'name' in attributes:
            name=attributes['name']
        else:
            raise ValueError("A field must have a name!")

        dateformat=''

        if 'type' not in attributes:
            raise ValueError(f"A field ({name}) must have a type!")
        else:
            t=attributes['type']
            if t == 'char':
                ourtype=str
            elif t == 'int':
                ourtype=int
            elif t == 'float':
                ourtype=float
            elif t == 'string':
                ourtype = str
            elif t == 'date':
                ourtype=datetime.date
                if 'dateformat' in attributes:
                    dateformat=attributes['dateformat']
                else:
                    raise ValueError(f"If a field ({name}) is a date, it must have a dateformat attribute!")
            else:
                raise ValueError(f"Type for {name} must be one of ['char', 'int', 'float', 'string', 'date']")

        if 'description' in attributes:
            description = attributes['description']
        else:
            description = name

        if 'allowna' in attributes:
            try:
                allowna=bool(attributes['allowna'])
            except Exception:
                print(f"WARNING: Could not parse allowna for field {name}, defaulting to True")
                allowna=True
        else:
            allowna=True

        if 'maxlength' in attributes:
            try:
                maxlength = int(attributes['maxlength'])
            except Exception:
                print(f"WARNING: Could not parse maxlength for field {name}, defaulting to -1")
                maxlength=-1
        else:
            maxlength=-1

        if 'key' in attributes:
            try:
                iskey=bool(attributes['key'])
            except Exception:
                print(f"WARNING: Could not parse 'key' for field {name}, defaulting to False")
                iskey=False
        else:
            iskey=False

        if 'groups' in attributes:
            try:
                groupnames=str(attributes['groups']).split()
            except Exception:
                print(f"WARNING: Could not parse 'groups' for field {name}, groups will not be set!")
                groupnames=[]
        else:
            groupnames=[]

        element=MDField(name=name, description=description, allowna=allowna,
                        maxlength=maxlength, iskey=iskey, type=ourtype, dateformat=dateformat)
        for group in groupnames:
            element.groups.append(group)

        if isinstance(self.currentElement, MDDataTable):
            self.currentElement.add_field(element)
        else:
            print(f"CurrentElement is {type(self.currentElement)}")

    def handle_datatable(self, tag, attributes):
        if 'name' not in attributes:
            raise ValueError("A DataTable MUST have a name!")
        else:
            name = str(attributes['name'])

        if 'multiplefiles' in attributes:
            try:
                multiplefiles = bool(attributes['multiplefiles'])
            except Exception:
                print("WARNING: multiplefiles must be True or False.  Defaulting to True")
                multiplefiles=False

        self.currentElement=MDDataTable(name=name, multiplefiles=multiplefiles)
    def startElement(self, tag, attributes: xml.sax.xmlreader.AttributesImpl):
        print(tag,[f"{k}:{v} " for k, v in attributes.items()])
        if tag == 'ModularDataset':
            if (self.currenttag == '') and not self.seenmodular:
                self.seenmodular=True
                if 'module' in attributes:
                    self.md.module=attributes['module']
                if 'identifier' in attributes:
                    self.md.dsdescription=attributes['identifier']
                self.currenttag=tag
            else:
                print(f"WARNING: Ignoring out of place ModularDataset tag in {self.md.xmlfile}")
                self.currenttag=tag
        elif tag == 'DataTable':
            self.handle_datatable(tag, attributes)
        elif tag == 'Field':
            if self.currenttag=='Fields':
                self.handle_field(tag, attributes)
            else:
                print(f"Current tag is {self.currenttag}")
        elif tag == 'Fields':
            self.currenttag=tag

    def endElement(self, tag):
        if tag == 'DataTable':
            dtable: MDDataTable = self.currentElement
            if len(dtable.fields) == 0:
                raise ValueError("A data table must have at least one field!")
            else:
                self.md.datatables[dtable.name] = dtable
            self.currentElement = None

        if tag != 'Field':
            self.currenttag=''

    def characters(self, content):
        pass

