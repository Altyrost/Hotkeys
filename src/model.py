import json
import uuid
import os
import sys

from log import log

# determine if application is a script file or frozen exe
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
elif __file__:
    application_path = os.path.dirname(__file__)

CONFIG_PATH = os.path.join(application_path, "data.json")

class HotkeyModel:
    def __init__(self, data):
        self._target = data["target"]
        self._source =  data["source"]
        self._id =  uuid.uuid4()
        self._callback = None
        self.disabled = False

    @property
    def target(self):
        return self._target

    @target.setter
    def target(self, value):
        self._target = value

    @property
    def source(self):
        return self._source

    @source.setter
    def source(self, value):
        self._source = value

    @property
    def id(self):
        return self._id

    @property
    def callback(self):
        return self._callback

    @callback.setter
    def callback(self, value):
        self._callback = value

    def is_registered(self):
        return self._callback != None

    def is_valid(self):
        return self._source != "" and self._target != ""

    def asdict(self):
        return {
            "source": self._source,
            "target": self._target
        }

    def __eq__(self, uid: str):
        return self.id == uid

class HotkeyListModel:
    def __init__(self):
        self._hotkeys = [] 
        self.load()

    def get_sources(self):
        return [hotkey.source for hotkey in self._hotkeys]

    def get_targets(self):
        return [hotkey.target for hotkey in self._hotkeys]

    def load(self):
        try:
            with open(CONFIG_PATH, "r") as json_data:
                datas = json.load(json_data)
                for data in datas:
                    hotkey_model = HotkeyModel(data)
                    self._hotkeys.append(hotkey_model)
        except FileNotFoundError:
            self.save()
        except ValueError:
            self.save()            
        log(f" -- datas loaded: {datas}")

    def save(self):        
        json_data = [hk.asdict() for hk in self._hotkeys if hk.is_valid()]
        log(f" -- datas saved: {json_data}")
        with open(CONFIG_PATH, "w") as json_file:
            json.dump(json_data, json_file)
