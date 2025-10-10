from queue import Queue, Empty, Full
from pynput.keyboard import Controller
from pynput.keyboard import Listener
from pynput.keyboard import Key
from retico_core import AbstractProducingModule
from retico_core import UpdateMessage
from retico_core import UpdateType
from retico_core.text import TextIU

class KeyboardModule(AbstractProducingModule):
    """
    A module that incrementally produces TextIUs from keyboard input.
    """

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
        return TextIU

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.charbuf = Queue()
        self.word = ''
        self.kb = Controller()
        self.listener = Listener(
            on_press=self._on_press,
            on_release=None,
        )

    def prepare_run(self):
        self.listener.start()

    def process_update(self, update_message):
        if self.charbuf.empty(): return

        char = self.charbuf.get()
        if char == ' ':
            # clear current word from terminal
            for _ in range(len(self.word)):
                self.kb.press(Key.backspace)
                self.kb.release(Key.backspace)

            iu = self.create_iu()
            iu.payload = self.word
            #self.current_output.append(iu)  # maybe add a way to revoke ius
            self.word = ''

            um = UpdateMessage.from_iu(iu, UpdateType.ADD)
            self.append(um)
        else:
            self.word += char

    def _on_press(self, key):
        try:
            self.charbuf.put_nowait(key.char)
        except AttributeError:
            if key == Key.space:
                try:
                    self.charbuf.put_nowait(' ')
                except Full:
                    pass
            if key == Key.backspace:
                try:
                    self.charbuf.get_nowait()
                except Empty:
                    pass

    def shutdown(self):
        self.listener.stop()
        self.kb.press(Key.enter)
        self.kb.release(Key.enter)
