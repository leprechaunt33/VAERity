import os.path

from kivy.app import App
import json
from kivy.uix.settings import SettingsWithSidebar

# TODO: Add ThemeSetting and FontSetting classes extending SettingItem

class VaeritySettings:
    settings_keys = [('Styles',[
        {'type': 'title',
        'title': 'Styles'},
        {'key': 'window.clearcolor',
         'title': 'Window background color',
         'desc': 'The background color of the window',
         'type': 'color',
         'section': 'style'
        },
        {'key': 'textbox.textcolor',
         'title': 'Default textbox/textinput text color',
         'desc': 'Designates the primary color of text for any textbox not styled elsewhere',
         'type': 'color',
         'section': 'style'
         },
        {'key': 'textbox.background',
         'title': 'Default textbox/textinput background color',
         'desc': 'Designates the primary textbox background color for any textbox not styled elsewhere',
         'type': 'color',
         'section': 'style'
         },
        {'key': 'button.textcolor',
         'title': 'Default button text color',
         'desc': 'Designates the primary color of text for buttons not styled separately',
         'type': 'color',
         'section': 'style'
         },
        {'key': 'button.background',
         'title': 'Default button background color',
         'desc': 'Designates the primary button background color for any button not covered below',
         'type': 'color',
         'section': 'style'
         },
        {'key': 'label.background',
         'title': 'Default label background color',
         'desc': 'Designates the background color of labels not otherwise styled separately',
         'type': 'color',
         'section': 'style'
        },
        {'key': 'label.textcolor',
         'title': 'Default label text color',
         'desc': 'Designates the text color of labels not otherwise styled separately',
         'type': 'color',
         'section': 'style'
         },
        {'key': 'togglebutton.background',
         'title': 'Toggle button color',
         'desc': 'Color of an unchecked checkbox',
         'type': 'color',
         'section': 'style'
         },
        {'key': 'navbutton.background',
         'title': 'Navigation button background color',
         'desc': 'Background color of the left and right arrow buttons in the record viewer screens',
         'type': 'color',
         'section': 'style'
         },
        {'key': 'navbutton.textcolor',
         'title': 'Navigation button background color',
         'desc': 'Text color of the left and right arrow buttons in the record viewer screens',
         'type': 'color',
         'section': 'style'
         },
        {'key': 'recordheader.background',
         'title': 'Record header background color',
         'desc': 'Background color of the record header on the record viewer screens',
         'type': 'color',
         'section': 'style'
         },
        {'key': 'recordheader.textcolor',
         'title': 'Record header text color',
         'desc': 'Text color of the record header on the record viewer screens',
         'type': 'color',
         'section': 'style'
         },
        {'key': 'backbutton.background',
         'title': 'Back button background color',
         'desc': 'Background color of the back button enabling transition between screens',
         'type': 'color',
         'section': 'style'
         },
        {'key': 'recordheader.textcolor',
         'title': 'Back button text color',
         'desc': 'Text color of the various back buttons',
         'type': 'color',
         'section': 'style'
         },
        {'key': 'eventheader.background',
         'title': 'Event header background',
         'desc': 'Background color of the labels in the event table',
         'type': 'color',
         'section': 'style'
         },
        {'key': 'eventheader.textcolor',
         'title': 'Event header text color',
         'desc': 'Text color of the various back buttons',
         'type': 'color',
         'section': 'style'
         },
        {'key': 'patientdata.background',
         'title': 'Patient descriptor background color',
         'desc': 'Background color of the patient record descriptor in the record viewer',
         'type': 'color',
         'section': 'style'
         },
        {'key': 'patientdata.textcolor',
         'title': 'Patient data text color',
         'desc': 'Text color of the patient record descriptor in the record viewer',
         'type': 'color',
         'section': 'style'
         },
        {'key': 'vaccinedata.background',
         'title': 'Vaccine descriptor background color',
         'desc': 'Background color of the vaccine table header in the record viewer',
         'type': 'color',
         'section': 'style'
         },
        {'key': 'vaccinedata.textcolor',
         'title': 'Vaccine descriptor text color',
         'desc': 'Text color of the vaccine table header in the record viewer',
         'type': 'color',
         'section': 'style'
         },
        {'key': 'vaccineheader.background',
         'title': 'Vaccine header text color',
         'desc': 'Background color of the labels in the vaccine table in the record viewer',
         'type': 'color',
         'section': 'style'
         },
        {'key': 'vaccineheader.textcolor',
         'title': 'Vaccine header text color',
         'desc': 'Text color of the labels in the vaccine table in the record viewer',
         'type': 'color',
         'section': 'style'
         }

    ])
    ]

    settings_defaults=[('style', {''
                                  'button.textcolor': '#FFFFFF', 'button.background': '#092E5B',
                                  'textbox.textcolor': '#FFFFFF', 'textbox.background': '#092E5B',
                                  'window.clearcolor': '#000000', 'label.textcolor': '#FFFFFF',
                                  'label.background': '#262626', 'togglebutton.background': '#144272',
                                  'navbutton.background': '#092E5B', 'navbutton.textcolor': '#FFFFFF',
                                  'recordheader.background': '#0A2647', 'recordheader.textcolor': '#FFFFFF',
                                  'backbutton.background': '#111133', 'backbutton.textcolor': '#FFFFFF',
                                  'eventheader.background': '#111133', 'eventheader.textcolor': '#FFFFFF',
                                  'patientdata.background': '#111133', 'patientdata.textcolor': '#FFFFFF',
                                  'vaccinedata.background': '#111133', 'vaccinedata.textcolor': '#FFFFFF',
                                  'vaccineheader.background': '#111133', 'vaccineheader.textcolor': '#FFFFFF',
                                  })]

    def __init__(self):
        self.filepath=os.path.join(os.path.dirname(__file__),'vaerity.ini')