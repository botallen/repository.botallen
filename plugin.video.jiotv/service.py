from resources.lib import proxy, kodiutils
import SocketServer
import threading
from xbmc import Monitor

SocketServer.ThreadingTCPServer.allow_reuse_address = True
_PORT = 48996
handler = SocketServer.ThreadingTCPServer(("", _PORT), proxy.JioTVProxy)
t = threading.Thread(target=handler.serve_forever)
t.setDaemon(True)
t.start()
kodiutils.notification('Proxy Server Started', 'Proxy server for HD')

monitor = Monitor()
while not monitor.abortRequested():
    if monitor.waitForAbort(5):
        handler.shutdown()
        handler.server_close()
        break
