import re

class RtfDocument:
    border_types={'single': 's', 'dotted' : 'dot', 'double': 'db', 'dash': 'dash'}

# Note that throughout this code there will be found new lines after certain tokens.
# The reason for this is that it is unknown what action will be taken after that
# token.  Therefore, to preserve the legality of the syntax of the generated document,
# the new line is added to make what comes next separate from the token, regardless of
# its starting chars, alphanumeric or otherwise.

    def __init__(self, font_table: list, color_table: list, **kwargs):
        self.in_code = False
        self.default_font: int = 0
        self.docheader: list = []
        self.docdata = []
        self.style_sheet = []
        if color_table is None:
            color_table = []

        if font_table is None:
            font_table = []

        self.font_table = font_table
        self.color_table = color_table
        self.page_size=[int(8.5*1440),11*1440]

        if 'page_size' in kwargs:
            if isinstance(kwargs['page_size'],list):
                self.page_size=kwargs['page_size']

        if 'default_font' in kwargs:
            self.default_font=int(kwargs['default_font'])

        self.set_document_header()
        if self.page_size[0]>self.page_size[1]:
            self.add_raw(['\\landscape'])

        self.add_raw([f'\\paperw{int(self.page_size[0])}', f'\\paperh{int(self.page_size[1])}\n'])

    def add_raw(self,elements: list):
        self.docdata.extend(elements)
        return self

    def add_text(self, text):
        self.docdata.extend([re.sub('([{\\\\])','\\\1',text)])
        return self

    def end_column(self):
        self.docdata.append('\\cell\n')
        return self

    def add_table_paragraph(self,text):
        self.add_text(text)
        self.docdata.extend(['\\intbl\n'])
        return self

    def extend_style(self, styleidx):
        s = self.style_sheet[styleidx]
        # Include the style definition \sN and the corresponding formatting
        # commands but not the style name.  This allows parsers that do not
        # stylesheets to interpret the document correctly.
        self.docdata.extend(s[0:len(s) - 1])

    def single_paragraph_column(self, text, bg=None, fg=None, style=None):
        if style is not None:
            self.extend_style(style)

        if bg is not None:
            self.set_background(bg)

        if fg is not None:
            self.set_color(fg)

        self.add_table_paragraph(text)
        self.end_column()

    def end_row(self):
        self.docdata.append('\\row\n')

    def add_style(self,styleidx,fontnum,fontsize,fg,bg,raw,stylename):
        if styleidx is None:
            styleidx = len(self.style_sheet)

        style=[]
        style.append(f'\\s{styleidx}')

        if fg is not None:
            if isinstance(fg, str):
                try:
                    m = self.color_table.index(fg)
                    style.append(f'\\cf{m}')
                except:
                    raise ValueError(f"Color {fg} not present in color table!")
            else:
                style.append(f'\\cf{fg}')
        if bg is not None:
            if isinstance(bg, str):
                try:
                    m = self.color_table.index(bg)
                    style.append(f'\\cb{m}')
                except:
                    raise ValueError(f"Color {bg} not present in color table!")
            else:
                style.append(f'\\cb{bg}')

        if raw is not None:
            style.extend(raw)

        if fontnum is not None:
            style.append(f'\\f{fontnum}')

        if fontsize is not None:
            style.append(f'\\fs{fontsize}')

        self.style_sheet.append(style)

        if stylename is None:
            stylename=f"style{styleidx}"

        self.style_sheet.append(stylename)

    def set_color(self,n):
        eol=self.eol()
        if isinstance(n, str):
            try:
                m=self.color_table.index(n)
                self.docdata.append(f'\\cf{m}{eol}')
            except:
                raise ValueError(f"Color {n} not present in color table!")
        else:
            self.docdata.append(f'\\cf{n}{eol}')
        return self

    def begin_code_words(self):
        self.in_code=True

    def end_code_words(self):
        self.in_code=False

    def eol(self):
        if self.in_code:
            return ''
        else:
            return '\n'

    def set_background(self,n):
        eol=self.eol()
        if isinstance(n, str):
            try:
                m=self.color_table.index(n)
                self.docdata.append(f'\\cb{m}{eol}')
            except:
                raise ValueError(f"Color {n} not present in color table!")
        else:
            self.docdata.append(f'\\cb{n}{eol}')
        return self

    def italic(self,on: bool):
        eol=self.eol()
        if on:
            self.docdata.append(f'\\i{eol}')
        else:
            self.docdata.append(f'\\i0{eol}')
        return self

    def bold(self,on: bool):
        eol=self.eol()
        if on:
            self.docdata.append(f'\\b{eol}')
        else:
            self.docdata.append(f'\\b0{eol}')
        return self
    def br(self):
        self.docdata.append('\\line\n')
        return self

    def add_row_definition(self, rowdef: dict):
        self.docdata.append('\\trowd\n')
        if 'spacing' in rowdef:
            spacing=rowdef['spacing']//2
        else:
            spacing=144

        self.docdata.append(f'\\trgaph{spacing}\n')

        if 'widths' in rowdef:
            j=0
            for col in rowdef['widths']:
                self.docdata.append(f'\\cellx{col}\n')
                tlbr=rowdef['borders'][j]
                i=0
                for b in ['t','l','b','r']:
                    if tlbr[i] in self.border_types:
                        self.docdata.extend([f'\\clbrdr{b} ', f'\\brdr{self.border_types[tlbr[i]]}\n'])
                    i += 1
                j += 1
        else:
            raise ValueError("widths parameter must be an array of length 4 specifying twips")

    def document(self):
        xtnd=[]
        el=self.docheader.pop()
        if el != '{font_table}':
            raise ValueError('Unexpected data in document header')
        else:
            if len(self.font_table) > 0:
                xtnd.append('{\\fonttbl')
                i=0
                for font in self.font_table:
                    xtnd.append(f"{{\\f{i}")
                    xtnd.append(f"\\f{font['family']} ")
                    xtnd.append(f"{font['name']};}}")
                    i += 1
                xtnd.append('}\n')

        el=self.docheader.pop()
        xtnd2=[]
        if el == '{color_table}':
            if len(self.color_table) > 0:
                xtnd2.append('{\\colortbl;')
                for color in self.color_table:
                    if re.match('^#[A-Fa-f0-9]+$',color):
                        h=str(color).lstrip('#')
                        t=tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
                        xtnd2.extend([f'\\red{t[0]}',f'\\green{t[1]}', f'\\blue{t[2]};'])
                xtnd2.append('}\n')
            else:
                raise ValueError('Unexpected data in document header')

        xtnd2.extend(xtnd)

        if len(self.style_sheet) > 0:
            xtnd2.append('{\\stylesheet')
            for style in self.style_sheet:
                xtnd2.append('{')
                xtnd2.extend(style)
                xtnd2.append(';}')
            xtnd2.append('}')

        final=self.docheader.copy()
        final.extend(xtnd2)
        final.extend(self.docdata)
        final.append('}\n')
        self.docheader.extend(['{color_table}','{font_table}'])
        return ''.join(final)


    def set_document_header(self):
        self.docheader = ['{\\rtf1','\\ansi']

        self.docheader.extend([f'\\deff{self.default_font}','{color_table}','{font_table}'])
