# retico-keyboard
A Retico module for producing IUs from keyboard inputs.

---

### Installation
The module can be installed by running:  
```pip install git+https://github.com/retico-team/retico-keyboard.git```

---

### Instructions
The module provides a simple GUI including a text input field and an IU stack component.
Text can be entered into the input field and will be parsed into IUs delimited by whitespace.
As text is entered and parsed, it is added incrementally to the associated network of modules.
Deleting text similarly revokes the previously added IUs. Added and revoked IUs are queued 
and logged via the IU stack, providing an easy-to-read history of IU events. All queued IUs
can be either committed or cleared (revoked) using the appropriate buttons.

### Example
```python
from retico_core.debug import DebugModule
from retico_keyboard import KeyboardModule


keeb = KeyboardModule()
debug = DebugModule(print_payload_only=True)

keeb.subscribe(debug)

keeb.run()
debug.run()

input()

keeb.stop()
debug.stop()
```

---
