# -*- coding: utf-8 -*-

from resources.lib import proxy
from codequick import Script
from codequick.script import Settings
import SocketServer
import threading
from xbmc import Monitor
from kodi_six import xbmcgui


def serveForever(handler):
    try:
        handler.serve_forever()
    except Exception as e:
        Script.log(e, lvl=Script.DEBUG)
        pass


SocketServer.ThreadingTCPServer.allow_reuse_address = True
_PORT = 48996
handler = SocketServer.ThreadingTCPServer(("", _PORT), proxy.JioTVProxy)
t = threading.Thread(target=serveForever, args=(handler,))
t.setDaemon(True)
t.start()

if not Settings.get_boolean("popup"):
    xbmcgui.Dialog().ok("JioTV Notification", "Now you can create your custom playlist from BotAllen Dashboard. [CR]Find out more at [B]https://botallen.com/#dashboard[/B] [CR][CR]If you like this add-on then consider donating from [B]https://botallen.com/#donate[/B] [CR][CR]Github: [B]https://github.com/botallen/repository.botallen[/B] [CR]Discord: [B]https://botallen.com/discord[/B] [CR][CR][I]You can disable this popup from settings[/I]")

monitor = Monitor()
while not monitor.abortRequested():
    if monitor.waitForAbort(10):
        handler.shutdown()
        handler.server_close()
        break
