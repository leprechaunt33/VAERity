import math
import traceback

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.app import App
from kivy.graphics import Color, Rectangle, PushMatrix, Translate, Rotate, PopMatrix, Line
from kivy.properties import ObjectProperty, BooleanProperty, NumericProperty, StringProperty
from kivy.core.text import Label as CoreLabel
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.togglebutton import ToggleButton
from kivy.utils import get_color_from_hex

from dataframegridview import ColoredLabel, ColoredButton


class FluxCapacitor(RelativeLayout):
    backInTime: ObjectProperty = ObjectProperty(None, allownone=True)
    backToTheFuture: ObjectProperty = ObjectProperty(None, allownone=True)
    plutonium: ColoredLabel = None
    maddog: Label = None
    density: Label = None
    calvinklein: Label = None
    currapp: App = None
    df: ObjectProperty = ObjectProperty(None)
    radius: float = 100
    wirewidth: float = 1
    upper_wire_angle = 50
    font_size = 11
    chkindex = None
    boolop = StringProperty()

    def set_calvin(self, fgcolors, bgcolors):
        self.calvinklein = Label(text=self.fieldlabels[2], color=fgcolors[2], font_size=10,
                                 size_hint=(None,None))

        self.calvinklein.texture_update()
        # Calvin is located at 20% of the radius from the bottom,
        # minus half its height.  Similarly, half its texture size
        # from the center
        self.calvinklein.width = self.calvinklein.texture_size[0]
        self.calvinklein.height = self.calvinklein.texture_size[1]

        posx2 = self.radius-self.calvinklein.texture_size[0]/2
        posy2 = self.radius*0.2

        self.calvinklein.pos=(posx2, posy2)

        # Checkbox
        t = ToggleButton(background_color=get_color_from_hex("#808080"), group=self.fieldgroup,
                          size_hint=(None, None), width=15, height=15)

        self.checks.append(t)

        n = len(self.checks)
        # Calvin's check is centered with its bottom left edge 8px left of center
        # and its bottom y 15 above the bottom right of calvin's text
        self.checks[n - 1].pos = (self.radius - 8, posy2 + 15)

        # Position for wire 1
        posn1 = self.to_window(posx2, posy2)

        origin = self.to_window(self.radius, self.radius)

        with self.calvinklein.canvas.before:
            Color(*fgcolors[2])
            self.wires.append(Line(width=self.wirewidth, points=[
                origin[0], origin[1], posn1[0],posn1[1]
            ]))
            PushMatrix()
            self.yourmymom = Rotate()
            self.yourmymom.angle = 0
            self.yourmymom.axis = (0, 0, 1)
            self.yourmymom.origin = (self.center_x, self.center_y)
            self.rotates.append(self.yourmymom)
            Color(*bgcolors[2])
            self.rectcalvin=Rectangle(pos=self.calvinklein.pos, size=self.calvinklein.size)

        with self.calvinklein.canvas.after:
            PopMatrix()

    def set_maddog(self,fgcolors, bgcolors):
        self.maddog = Label(text=self.fieldlabels[0], color=fgcolors[0], font_size=self.font_size,
                            size_hint=(None,None), bold=True)
        self.maddog.texture_update()
        self.maddog.width = self.maddog.texture_size[0]
        self.maddog.height = self.maddog.texture_size[1]

        # Mad dog's bottom left is located half of its size before the 0.8 of the radius
        # center from center to center
        uwa=self.upper_wire_angle
        posx = self.radius*(1+math.cos(math.radians(uwa))*0.9)-self.maddog.texture_size[0]/2
        posy = self.radius*(1+math.sin(math.radians(uwa))*0.9)-self.maddog.texture_size[1]/2

        self.maddog.pos = (posx, posy)

        t = ToggleButton(background_color=get_color_from_hex("#808080"), group=self.fieldgroup,
                          size_hint=(None, None), width=15, height=15)

        self.checks.append(t)
        n = len(self.checks)
        self.checks[n - 1].pos = (posx - 15, posy - 25)

        origin=self.to_window(self.radius, self.radius)
        madpos=self.to_window(posx, posy)

        with self.maddog.canvas.before:
            Color(0,1,0,1)
            Line(width=self.wirewidth,
                 points=[origin[0], origin[1], origin[0], origin[1]+ self.radius])

            Color(1,0,0,1)
            Line(width=self.wirewidth,
                points=[origin[0], origin[1], origin[0],origin[1]-self.radius])

            Line(width=self.wirewidth,
                points=[origin[0], origin[1], madpos[0],madpos[1]])

            Color(1,1,0,1)
            Line(width=self.wirewidth,
                 points=[0, 0,
                         2*self.radius, 0,
                         2*self.radius, 2*self.radius,
                         0, 2*self.radius,
                         0,0], dash_offset=2, dash_length=2)
            PushMatrix()
            self.tannen=Rotate()
            self.tannen.angle=self.upper_wire_angle-90
            self.tannen.axis=(0,0,1)
            self.tannen.origin = (posx,posy)
            self.rotates.append(self.tannen)
            Color(*bgcolors[0])
            self.rectdog=Rectangle(pos=self.maddog.pos, size=self.maddog.size)

        with self.maddog.canvas.after:
            PopMatrix()

    def set_density(self, fgcolors, bgcolors):
        self.density = Label(text=self.fieldlabels[1], color=fgcolors[1], font_size=self.font_size,
                             size_hint=(None,None), bold=True)

        self.density.texture_update()
        self.density.width = self.density.texture_size[0]
        self.density.height = self.density.texture_size[1]

        uwa=180-self.upper_wire_angle
        posx1 = self.radius*(1+math.cos(math.radians(uwa))*0.9)-self.density.texture_size[0]/2
        posy1 = self.radius*(1+math.sin(math.radians(uwa))*0.9)-self.density.texture_size[0]/2

        self.density.pos=(posx1,posy1)
        origin=self.to_window(self.radius, self.radius)
        densitypos=self.to_window(posx1, posy1)

        t = ToggleButton(background_color=get_color_from_hex("#808080"), group=self.fieldgroup,
                          size_hint=(None, None), width=15, height=15)

        self.checks.append(t)
        n = len(self.checks)
        self.checks[n - 1].pos = (posx1 + 15, posy1 - 25)

        with self.density.canvas.before:
            Color(*fgcolors[1])
            self.wires.append(Line(width=self.wirewidth, points=[
                origin[0], origin[1], posx1,posy1]))
            Line(width=self.wirewidth,
                points=[origin[0], origin[1], densitypos[0],densitypos[1]])
            PushMatrix()
            self.destiny = Rotate()
            self.destiny.angle = self.upper_wire_angle
            self.destiny.axis = (0, 0, 1)
            self.rotates.append(self.destiny)
            self.destiny.origin = (posx1, posy1)
            Color(*bgcolors[1])
            self.rectdestiny=Rectangle(pos=self.density.pos, size=self.density.size)

        with self.density.canvas.after:
            PopMatrix()

    def toggleop(self, *args):
        self.df.drop_filter(inplace=True)
        print(f'At the toggle point boolop is {self.boolop}')
        if self.boolop == 'and':
            self.boolop='or'
        else:
            self.boolop='and'

        print(f"boolop now {self.boolop}")
        if self.boolop == 'and':
            markup = "([color=#5BC0F8][u][ref=boolopchange]A[/ref][/u][/color)"
        else:
            markup = "([color=#5BC0F8][u][ref=boolopchange]O[/ref][/u][/color]"

        self.fluxheader.text=f"{self.fluxtext}   {markup}"
        self.fluxheader.markup=True
        self.fluxheader.texture_update()
        Clock.schedule_once(self.on_state)

    def on_boolop(self, instance, value):
        self.on_state(instance, value)
        return True

    def set_flux_header(self, fgcolors, bgcolors):
        if self.boolop == 'and':
            markup="([color=#5BC0F8][u][ref=boolopchange]A[/ref][/u][/color])"
        else:
            markup = "([color=#5BC0F8][u][ref=boolopchange]O[/ref][/u][/color])"

        self.fluxheader = Label(text=f"{self.fluxtext}   {markup}", color=fgcolors[0], font_size=self.font_size,
                                size_hint=(None,None), bold=True, markup=True)
        self.fluxheader.texture_update()
        self.fluxheader.pos=(0,self.radius*2-(self.fluxheader.texture_size[1]+5))
        self.fluxheader.height=self.fluxheader.texture_size[1]+5
        self.fluxheader.width=2*self.radius
        self.fluxheader.bind(on_ref_press = self.toggleop)

        with self.fluxheader.canvas.before:
            Color(*bgcolors[0])
            self.fluxheadrect=Rectangle(pos=self.fluxheader.pos, size=self.fluxheader.size)

    def position_checks(self):
        self.checks[0].pos = (self.maddog.pos[0] - 15, self.maddog.pos[1] - 25)
        self.checks[1].pos = (self.density.pos[0] + 15, self.density.pos[1] - 25)
        self.checks[2].pos = (self.radius - 8, self.calvinklein.pos[1] + 15)

    def set_buttons(self):
        btn1=ColoredButton(get_color_from_hex(self.currapp._vc['button.background']), text=" < ",
                           color=get_color_from_hex(self.currapp._vc['button.textcolor']),
                           size_hint=(None,None), bold=True
                           )
        btn1.texture_update()
        btn1.height=btn1.texture_size[1]+5
        btn1.width=btn1.texture_size[0]
        btn1.pos=(5, self.radius-btn1.height/2)
        self.navLeft=btn1
        btn2=ColoredButton(get_color_from_hex(self.currapp._vc['button.background']), text=" > ",
                           color=get_color_from_hex(self.currapp._vc['button.textcolor']),
                           size_hint=(None,None), bold=True
                           )
        btn2.texture_update()
        btn2.height=btn2.texture_size[1]+5
        btn2.width=btn2.texture_size[0]
        btn2.pos=(2*self.radius-btn2.width, self.radius-btn2.height/2)
        self.navright=btn2

        self.navLeft.bind(on_release=self.moveFluxLeft)
        self.navright.bind(on_release=self.moveFluxRight)

    def fluxOrder(self):
        if self.backInTime is not None:
            return self.backInTime.fluxOrder()+1
        else:
            return 0

    def fluxFirst(self):
        first=self
        while first.backInTime is not None:
            first=first.backInTime

        return first

    def fluxPrev(self):
        return self.backInTime

    def fluxNext(self):
        return self.backToTheFuture

    def fluxLast(self):
        last=self

        while last.backToTheFuture is not None:
            last=last.backToTheFuture

        return last

    def moveFluxLeft(self, *args):
        parent=self.parent
        fluxord=self.fluxOrder()
        if fluxord == 0:
            newDownstream=self.fluxLast()
            # Kill the link to the second flux capacitor in the chain
            newHead=self.backToTheFuture
            if newHead is None:
                # Flux order zero with null afterwards means we are the only
                # flux in the list.  There is nothing to do.
                return

            # Disconnect from 2nd flux
            newHead.backInTime = None
            self.backToTheFuture = None
            self.backInTime = None
            # Notify will set btff and BIT on self
            self.notify_downstream(newDownstream)
        else:
            prev=self.backInTime
            if prev.backInTime is None:
                oldnext=self.backToTheFuture
                # If backInTime is not set for the prior Flux, we are moving
                # to the head of the list.  Disconnect from oldnext if any
                self.backToTheFuture=None
                self.backInTime=None
                # If oldnext is not None, this fixes the tree.  If it is, this
                # correctly sets prev as last of new list
                prev.backToTheFuture=oldnext
                prev.notify_downstream(self)
            else:
                # We are neither first nor second.  Save our pointwrs
                oldnext=self.backToTheFuture
                oldprev=self.backInTime
                newprev=oldprev.backInTime
                # Disconnect self from prev and prev from new left link
                self.backToTheFuture=None
                oldprev.backInTime = None
                # Connect old next record with oldprev as new head of right
                # If oldnext is null ie end of list, no notification is done
                # Otherwise forward propagation of the BIT pointer happens.
                oldprev.backToTheFuture=oldnext
                # This links pointers on the left end of the list
                self.notify_downstream(newprev)
                oldprev.notify_downstream(self)

        parent.clear_widgets()
        child=self.fluxFirst()
        while child is not None:
            parent.add_widget(child)
            child=child.fluxNext()

    def moveFluxRight(self, *args):
        parent=self.parent
        last=self.fluxLast()

        if self is last:
            newTail=self.backInTime

            if newTail is None:
                return

            newTail.backToTheFuture=None
            self.backInTime=None
            newTail.fluxFirst().notify_downstream(self)
        else:
            nextitem=self.backToTheFuture
            if nextitem.backToTheFuture is None:
                # Moving to tail
                self.backToTheFuture=None
                nextitem.backInTime=self.backInTime
                self.backInTime=None
                nextitem.notify_downstream(nextitem.backInTime)
                self.notify_downstream(nextitem)
            else:
                oldnext=self.backToTheFuture
                oldprev=self.backInTime
                newnext=oldnext.backToTheFuture
                oldnext.backToTheFuture=None
                self.backInTime=None
                if oldprev is None:      # self is head of list
                    oldnext.backInTime=None
                else:
                    oldprev.backToTheFuture=oldnext
                newnext.notify_downstream(self)
                self.notify_downstream(oldnext)


        parent.clear_widgets()
        child=self.fluxFirst()
        while child is not None:
            parent.add_widget(child)
            child=child.fluxNext()

    def build_fusion_reactor(self):
        self.size_hint=(None,None)
        self.width=self.radius*2
        self.height=self.radius*2
        self.defaults = [get_color_from_hex(self.currapp._vc['fluxlabel.background']),
                         get_color_from_hex(self.currapp._vc['fluxlabel.textcolor'])
                         ]

        if ('fluxbg' in self.kwargs) and isinstance(self.kwargs['fluxbg'], list):
            if len(self.kwargs['fluxbg']) != 3:
                raise ValueError(
                    "If you supply fluxbg, it must be a list of exactly three color arrays or color strings")
            else:
                bgcolors = []
                for c in self.kwargs['fluxbg']:
                    if isinstance(c, list):
                        bgcolors.append(c)
                    else:
                        bgcolors.append(get_color_from_hex(c))
        else:
            bgcolors = [self.defaults[0], self.defaults[0], self.defaults[0]]

        if ('fluxfg' in self.kwargs) and isinstance(self.kwargs['fluxfg'], list):
            if len(self.kwargs['fluxfg']) != 3:
                raise ValueError(
                    "If you supply fluxfg, it must be a list of exactly three color arrays or color strings")
            else:
                fgcolors = []
                for c in self.kwargs['fluxfg']:
                    if isinstance(c, list):
                        fgcolors.append(c)
                    else:
                        fgcolors.append(get_color_from_hex(c))
        else:
            fgcolors = [self.defaults[1], self.defaults[1], self.defaults[1]]

        # Colors have been loaded.  Now we focus on the 4 labels and 3 checkboxes.

        self.plutonium = Label(text='plutonium', color=fgcolors[0], font_size=self.font_size,
                               size_hint=(None,None), bold=True)

        self.plutonium.texture_update()
        # Plutonium is centered within the relative layout
        self.plutonium.pos = (self.radius-self.plutonium.texture_size[0]/2,
                              self.radius-self.plutonium.texture_size[1]/2)

        self.plutonium.width=self.plutonium.texture_size[0]+2
        self.plutonium.height=self.plutonium.texture_size[1]+2

        self.translates = []
        self.rotates = []
        self.wires = []
        self.checks = []
        self.checktr = []

        self.set_maddog(fgcolors, bgcolors)
        self.set_density(fgcolors, bgcolors)
        self.set_calvin(fgcolors, bgcolors)
        self.set_flux_header(fgcolors, bgcolors)
        self.set_buttons()

        self.add_widget(self.plutonium)
        self.add_widget(self.maddog)
        self.add_widget(self.density)
        self.add_widget(self.calvinklein)
        self.add_widget(self.fluxheader)
        self.add_widget(self.navLeft)
        self.add_widget(self.navright)
        for check in self.checks:
            self.add_widget(check)

        self.bind(pos=self.update_flux, size=self.update_flux)

    def update_flux(self, *args):
        print(f"In update_flux: {self.plutonium.texture_size} is the texture size")

        self.plutonium.pos = (self.radius-self.plutonium.texture_size[0]/2,
                              self.radius-self.plutonium.texture_size[1]/2)


        self.position_checks()

        self.rectdog.pos=self.maddog.pos
        self.rectdestiny.pos=self.density.pos
        self.rectcalvin.pos=self.calvinklein.pos
        self.rectdog.size=self.maddog.size
        self.rectdestiny.size=self.density.size
        self.rectcalvin.size=self.calvinklein.size

        print(f"plutonium @ {self.plutonium.pos}")
        for check in self.checks:
            print(f"check @ {check.pos}")

        print(f"maddog @ {self.maddog.pos}")
        print(f"density @ {self.density.pos}")
        print(f"calvinklein @ {self.calvinklein.pos}")

        #self.wires[2].points[0:4]=(self.center_x, self.center_y, self.center_x,
        #                           self.center_y - self.radius * 0.8)

        uwa=180-self.upper_wire_angle
        self.wires[1].points[0:4]=(self.center_x, self.center_y,
                                   self.center_x + self.radius * math.cos(math.radians(uwa)) * 0.8,
                                   self.center_y + self.radius * math.sin(math.radians(uwa)) * 0.8)
        uwa=self.upper_wire_angle
        self.wires[0].points[0:4]=(self.center_x, self.center_y,
                                   self.center_x + self.radius * math.cos(math.radians(uwa)) * 0.8,
                                   self.center_y + self.radius * math.sin(math.radians(uwa)) * 0.8)

    def filter_expression(self):
        if self.chkindex is None:
            return None

        querystring: str = self.fieldexprs[self.chkindex]

        if querystring is None:
            return None

        name=self.fieldname
        qs0=querystring.format(**locals())

        return qs0

    def filter_result(self):
        if self.backInTime is not None:
            filterset=self.backInTime.filter_result()
        else:
            filterset=self.df

        fe=self.filter_expression()
        print(f"Upstream returned a filterset of {len(filterset)} records.")
        if fe is None:
            print("Returning entire filterset unchanged")
            return filterset
        else:
            print(f"returning op {self.boolop} fe {fe} ")
            return filterset.filter(fe, mode=self.boolop)

    def __init__(self, fieldname: str, fieldgroup: str, fieldlabels: list[str],
                 fieldexpressions: list[str], fluxcolors: list, fluxtext, **kwargs):
        super().__init__()
        self.currapp=App.get_running_app()
        # Multiple fieldnames can be chained together into a hexagonal packing
        # to make arrows easier to draw.
        self.fieldname = fieldname
        # Groups: what to name the Toggle groups for each field
        self.fieldgroup = fieldgroup
        # The text labels for each toggle option
        self.fieldlabels = fieldlabels
        # The database expressions corresponding in vaex
        self.fieldexprs = fieldexpressions
        # The arrays of colors to animate through if an option
        # is selected or if an upstream/downstream is connected
        self.fluxcolors = fluxcolors
        # The flux text colors for result sets
        self.fluxtext = fluxtext

        self.cboxcol = get_color_from_hex(self.currapp._vc['togglebutton.background'])

        # Save arguments before building our fusion reactor.  We'll need those
        # for later.
        self.kwargs={**kwargs}
        self.boolop='and'
        self.build_fusion_reactor()

    def check_recordset(self):
        if self.df is None:
            print("Strange someone giving me a null dataset...")
            return

        try:
            fr=self.filter_result()
            if fr is not None:
                result2=len(fr)
                print(f"result2 is {result2}")
                self.plutonium.text=str(result2)
            else:
                self.plutonium.text = str(len(self.df))
        except Exception as ex:
            self.plutonium.text='No data'
            tb = traceback.format_exc()
            print(tb)

    def on_df(self, instance, value):
        print("df update triggered")
        self.check_recordset()
        self.checks[0].bind(state=self.on_state)
        self.checks[1].bind(state=self.on_state)
        self.checks[2].bind(state=self.on_state)
        if self.backToTheFuture is not None:
            self.backToTheFuture.notify_upstream(self.df.drop_filter(), self.filter_expression(), self)

    def notify_downstream(self, upstreamflux):
        print("Setting forward branch")
        upstreamflux.backToTheFuture = self

    def notify_upstream(self, dataframe, filter_expr, caller):
        self.backInTime=caller
        if dataframe is not None:
            if self.df is None:
                # Make sure the objects are independent.
                self.df = dataframe.copy()
            # We don't update df if its changed in the upstream
            # as the select() needs to operate independently of
            # other copies of the DataFrame
            self.check_recordset()
            if self.backToTheFuture is not None:
                self.backToTheFuture.notify_upstream(self.df, self.filter_expression(), self)

        elif filter_expr is not None:
            print(f"Received downstream notification filter {filter_expr}")
            # For now we do nothing with the expression as it can be
            # returned through

    def on_backToTheFuture(self, instance, value):
        if self.backToTheFuture is None:
            # Disconnected
            return

        self.backToTheFuture.notify_upstream(self.df,self.filter_expression(),self)

    def on_state(self, *args):
        print(f"on_state() entered")
        if self.df is not None:
            print(f"name is {self.fluxtext}, len df is {len(self.df)}")
        else:
            print("No dataframe yet")
            return
        if self.checks[0].state == 'down':
            self.chkindex=0
        elif self.checks[1].state == 'down':
            self.chkindex=1
        elif self.checks[2].state == 'down':
            self.chkindex=2
        else:
            return

        print(f"chkindex is {self.chkindex}")
        fr=self.filter_result()
        if fr is None:
            try:
                self.resultsize = len(self.df)
                self.plutonium.text = str(self.resultsize)
            except Exception as ex:
                self.plutonium.text="Data error"
                tb=traceback.format_exc()
                print(tb)
        else:
            try:
                dfsize=len(self.df)

                result2=len(fr)
                self.plutonium.text = str(result2)

                print(f"plutonium should have just updated to {result2}.\nThe original df len is {dfsize}")
                print(f"get_active_range returns {self.df.get_active_range()}")
                print(f"result2 is {result2}")
            except Exception as ex:
                self.plutonium.text="Data error"
                tb=traceback.format_exc()
                print(tb)

        if self.backToTheFuture is not None:
            print("Notifying upstream...")
            self.backToTheFuture.notify_upstream(self.df.drop_filter(), self.filter_expression(), self)
        else:
            print("No upstream to notify")

