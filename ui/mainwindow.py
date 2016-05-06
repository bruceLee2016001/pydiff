import os, mimetypes, filecmp
from difflibparser.difflibparser import *
from ui.mainwindow_ui import MainWindowUI
from tkinter import *
from tkinter.filedialog import askopenfilename, askdirectory

class MainWindow:
    def start(self, leftFile = None, rightFile = None):
        self.main_window = Tk()
        self.main_window.title('Difftools')
        self.main_window_ui = MainWindowUI(self.main_window)

        self.leftFile = StringVar()
        self.rightFile = StringVar()
        self.leftFile.trace('w', lambda *x:self.__filesChanged())
        self.rightFile.trace('w', lambda *x:self.__filesChanged())

        self.main_window_ui.center_window()
        self.main_window_ui.create_file_path_labels()
        self.main_window_ui.create_text_areas()
        self.main_window_ui.create_line_numbers()
        self.main_window_ui.create_scroll_bars()
        self.main_window_ui.create_file_treeview()
        path_to_my_project = os.getcwd()
        self.main_window_ui.add_menu('File', [
            {'name': 'Compare Files', 'command': self.browse_files},
            {'name': 'Compare Directories', 'command': self.browse_directories},
            {'separator'},
            {'name': 'Exit', 'command': self.exit}
            ])
        self.main_window_ui.add_menu('Edit', [
            {'name': 'Cut', 'command': self.__cut},
            {'name': 'Copy', 'command': self.__copy},
            {'name': 'Paste', 'command': self.__paste}
            ])
        self.main_window_ui.fileTreeView.bind('<<TreeviewSelect>>', lambda *x:self.__treeViewItemSelected())

        self.leftFile.set(leftFile if leftFile else '')
        self.rightFile.set(rightFile if rightFile else '')

        ######### for test only
        self.browse_process_directory('', 'tests/left_dir', 'tests/right_dir')

        self.main_window.mainloop()

    def browse_files(self):
        self.load_file('left')
        self.load_file('right')

    # Load directories into the treeview
    def browse_directories(self):
        leftDir = self.load_directory('left')
        rightDir = self.load_directory('right')
        if leftDir and rightDir:
            self.main_window_ui.fileTreeView.delete(*self.main_window_ui.fileTreeView.get_children())
            self.browse_process_directory('', leftDir, rightDir)

    # Recursive method to fill the treevie with given directory hierarchy
    def browse_process_directory(self, parent, leftPath, rightPath):
        if parent == '':
            leftDirName = os.path.basename(leftPath)
            rightDirName = os.path.basename(rightPath)
            self.main_window_ui.fileTreeView.heading('#0', text=leftDirName + ' / ' + rightDirName, anchor=W)
        leftListing = os.listdir(leftPath)
        rightListing = os.listdir(rightPath)
        mergedListing = list(set(leftListing) | set(rightListing))
        for l in mergedListing:
            newLeftPath = leftPath + '/' + l
            newRightPath = rightPath + '/' + l
            bindValue = (newLeftPath, newRightPath)
            # Item in left dir only
            if l in leftListing and l not in rightListing:
                self.main_window_ui.fileTreeView.insert(parent, 'end', text=l, value=bindValue, open=False, tags=('red','simple'))
            # Item in right dir only
            elif l in rightListing and l not in leftListing:
                self.main_window_ui.fileTreeView.insert(parent, 'end', text=l, value=bindValue, open=False, tags=('green','simple'))
            # Item in both dirs
            else:
                # If one of the diffed items is a file and the other is a directory, show in yellow indicating a difference
                if (not os.path.isdir(newLeftPath) and os.path.isdir(newRightPath)) or (os.path.isdir(newLeftPath) and not os.path.isdir(newRightPath)):
                    self.main_window_ui.fileTreeView.insert(parent, 'end', text=l, value=bindValue, open=False, tags=('yellow','simple'))
                else:
                    # If both are directories, show in white and recurse on contents
                    if os.path.isdir(newLeftPath) and os.path.isdir(newRightPath):
                        oid = self.main_window_ui.fileTreeView.insert(parent, 'end', text=l, open=False)
                        self.browse_process_directory(oid, newLeftPath, newRightPath)
                    else:
                        # Both are files. diff the two files to either show them in white or yellow
                        if (filecmp.cmp(newLeftPath, newRightPath)):
                            oid = self.main_window_ui.fileTreeView.insert(parent, 'end', text=l, value=bindValue, open=False, tags=('simple'))
                        else:
                            oid = self.main_window_ui.fileTreeView.insert(parent, 'end', text=l, value=bindValue, open=False, tags=('yellow','simple'))

    def load_file(self, pos):
        fname = askopenfilename()
        if fname:
            if pos == 'left':
                self.leftFile.set(fname)
            else:
                self.rightFile.set(fname)
            return fname
        else:
            return None

    def load_directory(self, pos):
        dirName = askdirectory()
        if dirName:
            if pos == 'left':
                self.main_window_ui.leftFileLabel.config(text=dirName)
            else:
                self.main_window_ui.rightFileLabel.config(text=dirName)
            return dirName
        else:
            return None

    # Highlight characters in a line in the given text area
    def tag_line_chars(self, lineno, textArea, tag, charIdx=None):
        try:
            line_start = ''
            line_end = ''
            if charIdx:
                line_start = str(lineno + 1) + '.' + str(charIdx)
                line_end = str(lineno + 1) + '.' + str(charIdx + 1)
                textArea.tag_remove('red', line_start, line_end)
            else:
                line_start = str(lineno + 1) + '.0'
                line_end = textArea.index('%s lineend' % line_start)
            textArea.tag_add(tag, line_start, line_end)
        except TclError as e:
            showerror('problem', str(e))

    # Callback for changing a file path
    def __filesChanged(self):
        self.main_window_ui.leftLinenumbers.grid_remove()
        self.main_window_ui.rightLinenumbers.grid_remove()
        if self.leftFile.get() == None or self.rightFile.get() == None:
            self.main_window_ui.leftFileTextArea.config(background=self.main_window_ui.grayColor)
            self.main_window_ui.rightFileTextArea.config(background=self.main_window_ui.grayColor)
            return

        if not os.path.exists(self.leftFile.get()) or not os.path.exists(self.rightFile.get()):
            return

        self.main_window_ui.leftFileLabel.config(text=self.leftFile.get())
        self.main_window_ui.rightFileLabel.config(text=self.rightFile.get())
        self.main_window_ui.leftFileTextArea.config(background=self.main_window_ui.whiteColor)
        self.main_window_ui.rightFileTextArea.config(background=self.main_window_ui.whiteColor)
        self.main_window_ui.leftLinenumbers.grid()
        self.main_window_ui.rightLinenumbers.grid()
        self.diff_files_into_text_areas()

    def __treeViewItemSelected(self):
        item_id = self.main_window_ui.fileTreeView.focus()
        paths = self.main_window_ui.fileTreeView.item(item_id)['values']
        if paths == None or len(paths) == 0:
            return
        self.leftFile.set(paths[0])
        self.rightFile.set(paths[1])

    # Insert file contents into text areas and highlight differences
    def diff_files_into_text_areas(self):
        leftFileContents = open(self.leftFile.get()).read()
        rightFileContents = open(self.rightFile.get()).read()

        # enable text area edits so we can clear and insert into them
        self.main_window_ui.leftFileTextArea.config(state=NORMAL)
        self.main_window_ui.rightFileTextArea.config(state=NORMAL)

        diff = DifflibParser(leftFileContents.splitlines(), rightFileContents.splitlines())

        self.main_window_ui.leftFileTextArea.delete(1.0, END)
        self.main_window_ui.rightFileTextArea.delete(1.0, END)

        lineno = 0
        for line in diff:
            if line['code'] == DiffCode.SIMILAR:
                self.main_window_ui.leftFileTextArea.insert('end', line['line'] + '\n')
                self.main_window_ui.rightFileTextArea.insert('end', line['line'] + '\n')
            elif line['code'] == DiffCode.RIGHTONLY:
                self.main_window_ui.leftFileTextArea.insert('end', '\n', 'gray')
                self.main_window_ui.rightFileTextArea.insert('end', line['line'] + '\n', 'green')
            elif line['code'] == DiffCode.LEFTONLY:
                self.main_window_ui.leftFileTextArea.insert('end', line['line'] + '\n', 'red')
                self.main_window_ui.rightFileTextArea.insert('end', '\n', 'gray')
            elif line['code'] == DiffCode.CHANGED:
                for (i,c) in enumerate(line['line']):
                    self.main_window_ui.leftFileTextArea.insert('end', c, 'darkred' if i in line['leftchanges'] else 'red')
                for (i,c) in enumerate(line['newline']):
                    self.main_window_ui.rightFileTextArea.insert('end', c, 'darkgreen' if i in line['rightchanges'] else 'green')
                self.main_window_ui.leftFileTextArea.insert('end', '\n')
                self.main_window_ui.rightFileTextArea.insert('end', '\n')

        self.main_window_ui.leftFileTextArea.config(state=DISABLED)
        self.main_window_ui.rightFileTextArea.config(state=DISABLED)

    def __cut(self):
        area = self.__getActiveTextArea()
        if area:
            area.event_generate("<<Cut>>")

    def __copy(self):
        area = self.__getActiveTextArea()
        if area:
            area.event_generate("<<Copy>>")

    def __paste(self):
        area = self.__getActiveTextArea()
        if area:
            area.event_generate("<<Paste>>")

    def __getActiveTextArea(self):
        if self.main_window.focus_get() == self.main_window_ui.leftFileTextArea:
            return self.main_window_ui.leftFileTextArea
        elif self.main_window.focus_get() == self.main_window_ui.rightFileTextArea:
            return self.main_window_ui.rightFileTextArea
        else:
            return None

    def exit(self):
        self.main_window.destroy()


