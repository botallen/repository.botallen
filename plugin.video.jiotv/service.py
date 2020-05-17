# -*- coding: utf-8 -*-

from resources.lib import proxy
from codequick import Script
import SocketServer
import threading
from xbmc import Monitor


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
Script.notify('JioTV Service', 'JioTV Background Service Started')

monitor = Monitor()
while not monitor.abortRequested():
    if monitor.waitForAbort(10):
        handler.shutdown()
        handler.server_close()
        break
