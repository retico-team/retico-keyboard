import time
import tkinter as tk
from threading import Thread
from tkinter import ttk
from retico_core import AbstractProducingModule, UpdateMessage, UpdateType
from retico_core.text import TextIU


class KeyboardModule(AbstractProducingModule):
    """
    A module that incrementally produces TextIUs from keyboard input.
    """
    RESTRICTED_CURSOR_ACTIONS = [
        '<Left>',
        '<Right>',
        '<Up>',
        '<Down>',
        '<Button-1>',
        '<ButtonPress-1>',
        '<B1-Motion>',
        '<Home>',
        '<End>',
        '<Tab>',
        '<Prior>',
        '<Next>',
        '<Return>',
    ]
    RESTRICTED_STACK_ACTIONS = [
        '<Button-1>',
        '<ButtonPress-1>',
        '<B1-Motion>',
    ]
    FONT = "Segoe UI"

    @staticmethod
    def name():
        return "KeyboardModule"

    @staticmethod
    def description():
        return "A module that produces IUs from keyboard input."

    @staticmethod
    def input_ius():
        return None

    @staticmethod
    def output_iu():
        return TkTextIU

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._gui_thread = Thread(target=self._gui, daemon=True)
        self.current = None
        self.new_tag_start = None
        self.start_word = False
        self.text = None
        self.stack = None

    def prepare_run(self):
        self._gui_thread.start()

    def process_update(self, _):
        time.sleep(0.1)

    def _gui(self):
        root = tk.Tk()
        root.geometry('700x400')
        root.minsize(500, 300)

        style = ttk.Style()
        style.configure('TLabel', font=(self.FONT, 11))
        style.configure('TButton', font=(self.FONT, 10), padding=5)
        style.configure('Header.TLabel', font=(self.FONT, 12, 'bold'))

        container = ttk.Frame(root)
        container.place(relx=0.5, rely=0.5, relwidth=0.8, relheight=0.8, anchor='center')
        container.columnconfigure(0, weight=3)
        container.columnconfigure(1, weight=1)
        container.rowconfigure(0, weight=1)

        left_frame = ttk.Frame(root, padding=15)
        left_frame.grid(row=0, column=0, rowspan=2, sticky='nsew', in_=container)
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(1, weight=1)

        entry_label = ttk.Label(left_frame, text='Input', style='Header.TLabel')
        entry_label.grid(row=0, column=0, sticky='w', pady=(0, 10))

        def _update_stack(um):
            for iu, ut in um:
                if ut == UpdateType.ADD:
                    verb = 'ADD'
                elif ut == UpdateType.REVOKE:
                    verb = 'REVOKE'
                elif ut == UpdateType.COMMIT:
                    verb = 'COMMIT'
                else:
                    raise NotImplementedError
                stack.insert(0, f' {iu.payload} -- {verb}')

        def _on_key_press(event):
            self.current = text.index('insert')

            if event.keysym == 'space' and self.start_word: return
            if event.keysym == 'space' and text.compare(self.new_tag_start, '!=', f"{self.current}"):
                new_word = text.get(self.new_tag_start, self.current).strip()
                text.tag_add('add', self.new_tag_start, self.current)

                iu = self.create_iu()
                iu.payload = new_word
                iu.tag_range = (self.new_tag_start, self.current)
                self.current_output.append(iu)

                um = UpdateMessage.from_iu(iu, UpdateType.ADD)
                self.append(um)
                _update_stack(um)
                self.start_word = True
                return

            if event.keysym == 'BackSpace' and text.get(self.current, f'{self.current}+1c') != ' ':
                if len(self.current_output) == 0: return
                if text.compare(self.current, '<=', self.current_output[-1].tag_range[1]):
                    iu = self.current_output.pop()
                    text.delete(iu.tag_range[0], iu.tag_range[1])
                    um = UpdateMessage.from_iu(iu, UpdateType.REVOKE)
                    self.append(um)
                    _update_stack(um)
                    self.current = text.index('insert')
                    self.new_tag_start = self.current

            if (event.char != '' and self.start_word) or (len(self.current_output) == 0 and self.start_word):
                self.new_tag_start = self.current
                self.start_word = False
                return

        text = tk.Text(
            left_frame,
            font=(self.FONT, 11), wrap='word', relief='flat', bd=0,
            highlightthickness=1, highlightbackground='#cccccc',
            highlightcolor='#0078d4', padx=10, pady=10
        )
        text.grid(row=1, column=0, sticky='nsew', pady=(0, 10))
        for action in self.RESTRICTED_CURSOR_ACTIONS: text.bind(action, lambda e: 'break')
        text.bind('<KeyPress>', _on_key_press)
        text.tag_configure('add', background='green')
        self.new_tag_start = text.index('insert')
        text.focus_set()

        btn_frame = ttk.Frame(left_frame)
        btn_frame.grid(row=2, column=0, sticky='w')

        def _commit():
            stack.delete(0, tk.END)
            for iu in self.current_output:
                um = UpdateMessage.from_iu(iu, UpdateType.COMMIT)
                self.append(um)
                _update_stack(um)
            self.current_output = []
            text.delete('1.0', tk.END)
            self.current = text.index('insert')
            self.start_word = True
            text.after(1, text.focus_set)

        def _clear_text():
            stack.delete(0, tk.END)
            while len(self.current_output) > 0:
                iu = self.current_output.pop()
                um = UpdateMessage.from_iu(iu, UpdateType.REVOKE)
                self.append(um)
                _update_stack(um)
            self.current_output = []
            text.delete('1.0', tk.END)
            self.current = text.index('insert')
            self.start_word = True
            text.after(1, text.focus_set)

        commit_btn = ttk.Button(btn_frame, text='Commit', command=_commit)
        commit_btn.pack(side='right')
        clear_btn = ttk.Button(btn_frame, text='Clear', command=_clear_text)
        clear_btn.pack(side='right')

        right_frame = ttk.Frame(root, padding=15)
        right_frame.grid(row=0, column=1, rowspan=2, sticky='nsew', in_=container)
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)

        stack_label = ttk.Label(right_frame, text='IU Stack', style='Header.TLabel')
        stack_label.grid(row=0, column=0, sticky='w', pady=(0, 10))

        list_container = ttk.Frame(right_frame)
        list_container.grid(row=1, column=0, sticky='nsew', pady=(0, 10))
        list_container.columnconfigure(0, weight=1)
        list_container.rowconfigure(0, weight=1)

        stack = tk.Listbox(
            list_container,
            font=(self.FONT, 11),
            relief='flat',
            bd=0,
            highlightthickness=1,
            highlightbackground='#cccccc',
            highlightcolor='#0078d4',
            selectbackground='#0078d4',
            activestyle='none',
        )
        stack.grid(row=0, column=0, sticky='nsew')
        for action in self.RESTRICTED_STACK_ACTIONS: stack.bind(action, lambda e: 'break')

        scrollbar = ttk.Scrollbar(list_container, orient='vertical', command=stack.yview)
        scrollbar.grid(row=0, column=1, sticky='ns')
        stack.config(yscrollcommand=scrollbar.set)

        bottom_frame = ttk.Frame(root, padding=(15, 10))
        bottom_frame.grid(row=2, column=0, columnspan=2, sticky='ew')

        exit_btn = tk.Button(
            bottom_frame,
            text='Exit',
            bg='#dc3545',
            fg='white',
            font=(self.FONT, 10),
            relief='flat',
            padx=20,
            pady=5,
            cursor='hand2',
            command=root.destroy,
        )
        exit_btn.pack(side="right")
        exit_btn.bind('<Enter>', lambda e: exit_btn.config(bg='#c82333'))
        exit_btn.bind('<Leave>', lambda e: exit_btn.config(bg='#dc3545'))

        root.mainloop()

    def shutdown(self):
        self._gui_thread.join(timeout=5)


class TkTextIU(TextIU):
    """A TextIU wrapper for the Tkinter Text widget."""

    @staticmethod
    def type():
        return "TkTextIU"

    def __init__(self, creator, iuid=0, previous_iu=None, grounded_in=None, payload=None):
        super().__init__(
            creator,
            iuid=iuid,
            previous_iu=previous_iu,
            grounded_in=grounded_in,
            payload=payload
        )
        self.tag_range = None
