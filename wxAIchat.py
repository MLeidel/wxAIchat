#
# wxAIchat.py
# wxPython GUI with OpenAI API in chat mode`
# ML Aug 2025
#
# Requires an OpenAI registration 'key'
# Uses 'mpv' for voice playback on Linux
#
import os
import sys
import iniproc
import markdown
import webbrowser
import wx
import platform
import subprocess
import openvoc
from time import localtime, strftime
from openai import OpenAI

opts = [] # loading options from the options.ini file into a list
opts = iniproc.read("options.ini", 'openai',    # 0
                                   'model',     # 1
                                   'fontsz1',   # 2
                                   'fontsz2',   # 3
                                   'role',      # 4
                                   'log',       # 5
                                   'editor',    # 6
                                   'qheight',   # 7
                                   'font1',     # 8
                                   'font2',     # 9
                                   'voice')     # 10
intro = f'''
Welcome to wxAIchat
    a GUI desktop AI client for conversing with
    OpenAI's Large Language Models

Model: {opts[1]}
role: {opts[4]}
OpenAI Key: {opts[0]}
log: {opts[5]}
qheight: {opts[7]}
editor: {opts[6]}
voice: {opts[10]}
font1: {opts[8]}
f1 size: {opts[2]}
font2: {opts[9]}
f2 size: {opts[3]}

A registered OpenAI API key is required
and set as a system environment variable

wxpython and openai modules also required

Use Ctrl-H for list of keyboard commands
'''

class MyFrame(wx.Frame):
    def __init__(self, parent, title="wxAI V1.1 OpenAI " + opts[1]):
        super(MyFrame, self).__init__(parent, title=title, size=(600, 550))

        panel = wx.Panel(self)
        sizer = wx.GridBagSizer(5, 5)
        self.playback = False

        # ----------------------------
        # First Text Widget (text1) the Prompt area
        # ----------------------------
        # This TextCtrl will expand horizontally but not vertically
        self.text1 = wx.TextCtrl(panel, style=wx.TE_MULTILINE)
        sizer.Add(
            self.text1,
            pos=(0, 0),              # Position at row 0, column 0
            span=(1, 5),             # Span of 1 row and 2 columns
            flag=wx.ALL | wx.EXPAND, # Allow horizontal expansion
            border=5
        )
        sizer.SetItemMinSize(self.text1, self.text1.GetSize().GetWidth(), int(opts[7]))  # Height
        self.text1.Bind(wx.EVT_KEY_DOWN, self.on_key_down_hotkeys)
        self.text1.SetToolTip("Enter Prompt in this field")
        self.text1.SetFocus()

        # ----------------------------
        # Second Text Widget (text2) the response area
        # ----------------------------
        # This TextCtrl will expand both horizontally and vertically
        self.text2 = wx.TextCtrl(panel, style=wx.TE_MULTILINE)  # wx.TE_DONTWRAP
        sizer.Add(
            self.text2,
            pos=(1, 0),              # Position at row 1, column 0
            span=(1, 5),             # Span of 1 row and 2 columns
            flag=wx.ALL | wx.EXPAND, # Allow horizontal expansion
            border=5
        )
        self.text2.Bind(wx.EVT_KEY_DOWN, self.on_key_down_hotkeys)
        self.text2.SetValue(intro)

        # ----------------------------
        # Clear Button
        # ----------------------------
        clear_btn = wx.Button(panel, label="Clear")
        sizer.Add(
            clear_btn,
            pos=(2, 0),          # Position at row 2, column 0
            span=(1, 1),         # Span of 1 row and 1 column
            flag=wx.EXPAND | wx.ALL, # Align to bottom-right
            border=5  # behaves like a "margin"
        )
        # Bind the close button event to the handler
        clear_btn.Bind(wx.EVT_BUTTON, self.on_clear)
        clear_btn.SetToolTip("Erase query and response text")

        # ----------------------------
        # Export Button
        # ----------------------------
        export_btn = wx.Button(panel, label="Export")
        sizer.Add(
            export_btn,
            pos=(2, 1),          # Position at row 2, column 0
            span=(1, 1),         # Span of 1 row and 1 column
            flag=wx.EXPAND | wx.ALL, # Align to bottom-right
            border=5  # behaves like a "margin"
        )
        # Bind the close button event to the handler
        export_btn.Bind(wx.EVT_BUTTON, self.on_export)
        export_btn.SetToolTip("Open response in web browser")

        # ----------------------------
        # View Button
        # ----------------------------
        view_btn = wx.Button(panel, label="View Log")
        sizer.Add(
            view_btn,
            pos=(2, 2),          # Position at row 2, column 0
            span=(1, 1),         # Span of 1 row and 1 column
            flag=wx.EXPAND | wx.ALL, # Align to bottom-right
            border=5  # behaves like a "margin"
        )
        # Bind the close button event to the handler
        view_btn.Bind(wx.EVT_BUTTON, self.on_view)

        # ----------------------------
        # Submit Button
        # ----------------------------
        submit_btn = wx.Button(panel, label="Submit")
        sizer.Add(
            submit_btn,
            pos=(2, 3),          # Position at row 2, column 0
            span=(1, 1),         # Span of 1 row and 1 column
            flag=wx.EXPAND | wx.ALL, # Align to bottom-right
            border=5  # behaves like a "margin"
        )
        submit_btn.SetToolTip(f"Submit prompt to {opts[1]} (Ctrl-G)")
        submit_btn.Bind(wx.EVT_BUTTON, self.on_submit)

        # ----------------------------
        # Close Button
        # ----------------------------
        close_btn = wx.Button(panel, label="Close")
        sizer.Add(
            close_btn,
            pos=(2, 4),          # Position at row 2, column 0
            span=(1, 1),         # Span of 1 row and 1 column
            flag=wx.EXPAND | wx.ALL, # Align to bottom-right
            border=5  # behaves like a "margin"
        )
        # Bind the close button event to the handler
        close_btn.Bind(wx.EVT_BUTTON, self.on_close)
        close_btn.SetToolTip("Ctrl-Q")


        # ----------------------------
        # Configure Growable Columns and Rows
        # ----------------------------
        sizer.AddGrowableCol(0, 1)    # Column 0 for Submit button & response area grows horizontally
        sizer.AddGrowableCol(1, 1)    # Clear button grows horizontally
        sizer.AddGrowableCol(2, 1)    # Export button grows horizontally
        sizer.AddGrowableCol(3, 1)    #
        sizer.AddGrowableCol(4, 1)    #
        sizer.AddGrowableRow(1, 1)    #

        panel.SetSizer(sizer)

        #----------------------------
        # set window metrics from winfo file
        # ----------------------------
        if os.path.isfile("winfo"):
            with open("winfo", "r", encoding='utf-8') as fin:
                winfo = fin.read()
            p = winfo.split("|")
            x, y, w, h = int(p[0]), int(p[1]), int(p[2]), int(p[3])
            position = wx.Point(x, y)
            self.SetPosition(position)
            self.SetSize(wx.Size(w, h))

        #----------------------------
        # SET CUSTOM FONTS
        # https://docs.wxpython.org/wx.FontInfo.html#wx-fontinfo
        # https://docs.wxpython.org/wx.FontFamily.enumeration.html#wx-fontfamily
        if platform.system() == "Windows":
            custom_font1 = wx.Font(
                        int(opts[2]),
                        wx.FONTFAMILY_DEFAULT,
                        wx.FONTSTYLE_NORMAL,
                        wx.FONTWEIGHT_NORMAL,
                        False,
                        opts[8]
            )
            self.text1.SetFont(custom_font1)

            custom_font2 = wx.Font(
                        int(opts[3]),           # Font size
                        wx.FONTFAMILY_DEFAULT,  # Font family: MODERN is typically monospaced
                        wx.FONTSTYLE_NORMAL,    # Font style
                        wx.FONTWEIGHT_NORMAL,   # Font weight
                        False,                  # Underlined
                        opts[9]                 # Face name
            )
            self.text2.SetFont(custom_font2)
        else:  # not Windows ...
            custom_font1 = wx.Font(
                        int(opts[2]),
                        wx.FONTFAMILY_DEFAULT,
                        wx.FONTSTYLE_NORMAL,
                        wx.FONTWEIGHT_NORMAL,
                        False,
                        opts[8]
            )
            self.text1.SetFont(custom_font1)

            custom_font2 = wx.Font(
                        int(opts[3]),           # Font size
                        wx.FONTFAMILY_DEFAULT,  # Font family: MODERN is typically monospaced
                        wx.FONTSTYLE_NORMAL,    # Font style
                        wx.FONTWEIGHT_NORMAL,   # Font weight
                        False,                  # Underlined
                        opts[9]                 # Face name
            )
            self.text2.SetFont(custom_font2)

        # DISABLE View Log if not set to 'on'
        if opts[5] == "off":
            view_btn.Enable(False)
            view_btn.SetToolTip("Log is 'off'")
        else:
            view_btn.SetToolTip("View past queries")

        # Variables to store search state
        self.search_text = ""
        self.search_pos = 0

        # initial conversation buffer
        self.conversation = [
            {"role": "system", "content": opts[4]}
        ]

        self.Show()


    # ----------------------------
    #   Event handlers follow
    # ----------------------------

    def on_close(self, event):
        ''' Event handler for the Close button.'''
        # save Window metrics
        pos = self.GetPosition()
        x, y = str(pos[0]), str(pos[1])
        size = self.GetSize()
        w, h = str(size[0]), str(size[1])
        with open("winfo", "w") as fout:
            fout.write(x + "|" + y + "|" + w + "|" + h)
        self.Close()


    def on_clear(self, event):
        ''' Event handler for the Clear button.'''
        dlg = wx.MessageDialog(
            self,
            "Do you want to clear PROMPT and RESPONSE areas?",  # content
            "Confirm Clear",  # title
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION
        )
        result = dlg.ShowModal()
        dlg.Destroy()

        if result == wx.ID_YES:
            self.text1.SetValue("")
            self.text2.SetValue(intro)


    def on_export(self, event):
        ''' convert MD file to HTML file and open in default browser '''
        mdtext = self.text2.GetValue()
        htmlText = markdown.markdown(mdtext, extensions=['tables', 'fenced_code'])
        htmlFile = "exported.html"
        # open in default browser
        with open(htmlFile, 'w', encoding='utf-8') as file:
            file.write(htmlText)
        webbrowser.open(htmlFile)

    def on_view(self, event):
        ''' view the current log
            if set to "on" in options '''
        with open("log.md", "r", encoding='utf-8') as fin:
            self.text2.SetValue(fin.read())
        self.text2.SetFocus()
        self.text2.SetInsertionPointEnd()

    def on_submit(self, event):
        ''' Event handler for Submit button (Ctrl-G). '''
        self.text2.SetValue("Thinking ...")
        wx.Yield()
        query = self.text1.GetValue()

        # 1) add the user message
        self.conversation.append(
            {"role": "user", "content": query}
        )

        # 2) call the chat completion
        ai_text = self.gptCode(opts[0], opts[1], self.conversation)

        if ai_text == "":
            self.text2.SetValue("")
            self.text1.SetValue("")
            return

        # 3) add the assistant reply to history
        self.conversation.append(
            {"role": "assistant", "content": ai_text}
        )

        # 4) show it
        self.text2.SetValue(ai_text)

        # append to log.md ?
        if opts[5].lower() == "on":
            today = strftime("%a %d %b %Y", localtime())
            tm    = strftime("%H:%M", localtime())
            with open("log.md", "a", encoding="utf-8") as fout:
                fout.write("\n\n=== Chat on %s %s ===\n\n" % (today, tm))
                for msg in self.conversation:
                    role = msg["role"]
                    fout.write(f"{role.upper()}:\n{msg['content']}\n\n")
                fout.write("="*40 + "\n\n")

        # clear the input query box
        self.text1.SetValue("")
        # Speak response, if speach is on ...
        if self.playback is True:
            self.speak_text(ai_text)


    def gptCode(self, key: str, model: str, messages: str) -> str:
        """Call the OpenAI ChatCompletion endpoint."""
        try:
            client = OpenAI(api_key=os.environ.get(key))
            resp = client.chat.completions.create(
            model    = model,
            messages = messages)
            return resp.choices[0].message.content.strip()
        except Exception as e:
            wx.MessageBox(str(e), "Error", wx.OK | wx.ICON_ERROR)
            return ""

    def speak_text(self, text: str):
        ''' Speak the query response text '''
        # text = self.getmdtext()  # get selected or all text
        x = openvoc.textospeech(opts[10], 'speek.mp3', text)
        if x != 0:
            messagebox.showerror("OpenVOC Error",
                                 "There is a problem with the voice playback")

    def toggle_speak_text(self, e=None):
        ''' toggle voice playback of each response
        Requires mpv for Linux. Nothing for Windows. '''
        if self.playback == True:
            self.playback = False
            # announce it
            x = openvoc.textospeech(
                                    opts[10],
                                    'speek.mp3',
                                    "Voice playback is now off.")
        else:
            self.playback = True
            # announce it
            x = openvoc.textospeech(
                                    opts[10],
                                    'speek.mp3',
                                    "Voice playback is now on.")
        if x != 0:
            messagebox.showerror("OpenVOC Error",
                                 "There is a problem with the voice")


    def on_key_down_hotkeys(self, event):
        ''' Set up HotKeys for the App '''
        keycode = event.GetKeyCode()
        modifiers = event.GetModifiers()

        if modifiers == (wx.MOD_CONTROL | wx.MOD_ALT) and keycode == ord('C'):  # Ctrl-Alt C on copy code
            self.on_copy_code()
        elif modifiers == (wx.MOD_CONTROL | wx.MOD_ALT) and keycode == ord('V'):  # toggle voice
            self.toggle_speak_text()
        elif modifiers == wx.MOD_CONTROL and keycode == ord('F'):  # Ctrl+F: open search dialog.
            self.doSearchDialog()
        elif modifiers == wx.MOD_CONTROL and keycode == ord('N'):  # Ctrl+N: find next occurrence.
            self.findNext()
        elif modifiers == wx.MOD_CONTROL and keycode == ord('G'):
            self.on_submit(event)
        elif modifiers == wx.MOD_CONTROL and keycode == ord('Q'):
            self.on_close(event)
        elif modifiers == wx.MOD_CONTROL and keycode == ord('H'):  # Ctrl+F: open search dialog.
            self.on_help_dialog()
        elif modifiers == wx.MOD_CONTROL and keycode == ord('O'):  # Ctrl+O: open editor with options
            self.openEditor()
        else:
            event.Skip()  # Ensure other key events are processed

    def openEditor(self):
        ''' Open text editor to alter options.ini '''
        global opts
        p = subprocess.Popen([opts[6], 'options.ini'])
        p.wait()  # wait until editor closes
        opts = []
        opts = iniproc.read("options.ini", 'openai',    # 0
                                           'model',     # 1
                                           'fontsz1',   # 2
                                           'fontsz2',   # 3
                                           'role',      # 4
                                           'log',       # 5
                                           'editor',    # 6
                                           'qheight',   # 7
                                           'font1',     # 8
                                           'font2',     # 9
                                           'voice')     # 10
        self.reLaunch()

    def doSearchDialog(self):
        # Open a dialog to accept search text.
        dlg = wx.TextEntryDialog(self, "Enter text to search:", "Find")
        if dlg.ShowModal() == wx.ID_OK:
            self.search_text = dlg.GetValue()
            # Start search from current insertion point.
            self.search_pos = self.text2.GetInsertionPoint()
            self.findNext()
        dlg.Destroy()

    def findNext(self):
        if not self.search_text:
            return  # Nothing to search.

        # Get the full text from the TextCtrl.
        full_text = self.text2.GetValue()
        # For a case–insensitive search, convert both full text and search string to lower case.
        lower_text = full_text.lower()
        lower_search = self.search_text.lower()

        # Search from the current position.
        idx = lower_text.find(lower_search, self.search_pos)
        if idx == -1:
            # Optionally, notify the user if the search text is not found:
            wx.MessageBox(f'"{self.search_text}" was not found.', "Find", wx.OK | wx.ICON_INFORMATION)
            # Reset search position for a new search.
            self.search_pos = 0
        else:
            # Set focus to the TextCtrl and highlight the found text.
            self.text2.SetFocus()
            self.text2.ShowPosition(idx)
            self.text2.SetSelection(idx, idx + len(self.search_text))
            # Update the search position for next search.
            self.search_pos = idx + len(self.search_text)

    def on_copy_code(self):
        text = self.text2.GetValue()
        lines = text.splitlines()
        result = []
        in_backticks = False

        for line in lines:
            if line.startswith('```'):
                if in_backticks:
                    break
                else:
                    in_backticks = True
                    continue
            else:
                if in_backticks:
                    result.append(line)  # Collect lines within the back-ticked region

        # Join selected text and put it to the clipboard
        if result:
            clipboard_text = '\n'.join(result)
            self.set_clipboard(clipboard_text)
            wx.MessageBox('Copied to clipboard', "Code")
        else:
            wx.MessageBox('No text found between triple back-ticks.')

    def set_clipboard(self, text):
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(text))
            wx.TheClipboard.Close()

    def reLaunch(self):
        ''' close and re-open this instance '''
        wx.MessageBox('App will now close and re-open...')
        python = sys.executable
        #self.Destroy()
        self.on_close(None)
        os.execl(python, python, *sys.argv)

    def on_help_dialog(self):
        msg = '''
        Ctrl-H     This help message\n
        Ctrl-F     Find text\n
        Ctrl-N     Find next\n
        Ctrl-Q     Quit App\n
        Ctrl-G     Execute AI request\n
        Ctrl-O     Open options in editor\n
        Alt-Ctrl-V Toggle voice
        Alt-Ctrl-C
                   Copy Code in Markup\n
        '''
        #wx.MessageBox(msg)
        wx.MessageBox(msg, 'Command Keys' , wx.OK)


class MyApp(wx.App):
    def OnInit(self):
        frame = MyFrame(None)
        self.SetTopWindow(frame)
        return True

if __name__ == '__main__':
    app = MyApp(False)
    app.MainLoop()
