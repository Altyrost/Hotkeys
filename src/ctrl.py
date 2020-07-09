
import uuid
import keyboard
from keyboard._canonical_names import canonical_names
from collections import Counter

from PySide2.QtCore import QObject, Signal
from PySide2.QtWidgets import QApplication

from model import HotkeyModel
import app
from log import log

# handle Num keys and weird formatting like Ctrl+Shift++
# replace the given key by the one used by the keyboard lib
def convert_qtkeys(qtkey):
    try:
        # https://stackoverflow.com/questions/8023306/get-key-by-value-in-dictionary
        key = list(canonical_names.keys())[list(canonical_names.values()).index(qtkey)]
    except ValueError:
        key = qtkey
    return key

def convert_qtsource(qtsource):
    mods = qtsource[0]
    key = convert_qtkeys(qtsource[1])

    if "Num+" in mods:
        mods = mods.replace("Num+", "")
        #key = "num " + key

    return "".join([mods, key])

def find_duplicates(elems, prop):
    sorted_datas = {}
    for elem in elems:
        value = "".join(getattr(elem, prop))
        if value == "":
            continue
        try:
            sorted_datas[value].append(elem)
        except KeyError:
            sorted_datas[value] = [elem]
            
    duplicates = []
    for k,v in sorted_datas.items():
        if len(v) > 1:
            duplicates.extend(v)
    
    return duplicates 

def register_hk(hotkey):
    source = convert_qtsource(hotkey.source)
    log(f"-- register {hotkey.source} -> {hotkey.target} as {source}")    

    try:
        return keyboard.add_hotkey(source, keyboard.press, args=[hotkey.target], suppress=True)
    except ValueError as err:
        err_str = err.args[0]        
        unknown_key = err_str.split("'")[1]

def unregister_hk(hotkey):
    log(f"-- unregister {hotkey.source} -> {hotkey.target}")
    keyboard.remove_hotkey(hotkey.callback)

class HotkeyController(QObject):
    error_triggered = Signal(str, str)
    error_cleared = Signal()

    def __init__(self, model):
        super().__init__()
        self.model = model

    def sanitize(self):
        for hotkey in self.model._hotkeys:
            hotkey.disabled = False
        self.error_cleared.emit()

        source_duplicates = find_duplicates(self.model._hotkeys, "source")
        for hotkey in source_duplicates:
            hotkey.disabled = True
            self.error_triggered.emit(str(hotkey.id), "Shortcut already in use")

        target_duplicates = find_duplicates(self.model._hotkeys, "target")
        for hotkey in target_duplicates:
            hotkey.disabled = True      
            self.error_triggered.emit(str(hotkey.id), "Fn function already in use")

    def register_all(self):
        self.sanitize()
        for hotkey in self.model._hotkeys:
            if not hotkey.is_valid() or hotkey.is_registered() or hotkey.disabled:
                continue
            hotkey.callback = register_hk(hotkey)

    def unregister_all(self):        
        for hotkey in self.model._hotkeys:
            if not hotkey.is_registered():
                continue
            unregister_hk(hotkey)
            hotkey.callback = None

    def create(self, source="", target=""):   
        log(f"-- create hotkey {source} {target}")
        hotkey = HotkeyModel({"source": source, "target": target})
        self.model._hotkeys.append(hotkey)
        if hotkey.is_valid():
            hotkey.callback = register_hk(hotkey)

    def delete(self, uid):    
        hotkey = self.get_hotkey(uid)
        if hotkey.is_registered():
            unregister_hk(hotkey)
            
        self.model._hotkeys.remove(hotkey)
        self.sanitize()

    def modify_source(self, uid, source):
        hotkey = self.get_hotkey(uid)
        if hotkey == False:
            log("-- modify_source hotkey not found")
            return
        hotkey.source = source
        self.sanitize()

    def modify_target(self, uid, target):
        hotkey = self.get_hotkey(uid)
        if hotkey == False:
            log("-- modify_target hotkey not found")
            return
        hotkey.target = target
        self.sanitize()

    def get_hotkey(self, uid):
        uid = uuid.UUID(uid)    
        for hotkey in self.model._hotkeys:
            if hotkey.id == uid:
                return hotkey
        return False

