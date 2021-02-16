import json
import sqlite3


class World:
    def __init__(self):
        self.enabled = True
        self.settings = {}
        self.entrypoint = None
        self.datapath = None
        self.db = None
        self.bot = None
        self.actions = None

    def getSetting(w, name):
        if name in w.settings:
            return w.settings[name]

        c = w.db.cursor()
        c.execute("SELECT setting_value FROM settings WHERE setting_name=?", (name,))
        r = c.fetchone()
        if r != None:
            r = json.loads(r[0])
        w.settings[name] = r
        return r

    def updateSetting(w, name, value):
        r = json.dumps(value)
        c = w.db.cursor()
        c.execute("INSERT OR REPLACE INTO settings VALUES (?, ?)", (name, r))
        w.settings[name] = r
