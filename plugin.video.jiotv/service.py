from resources.lib import proxy
import SocketServer
import threading
from resources.lib import kodiutils

handler = SocketServer.ThreadingTCPServer(("", 48996), proxy.JioTVProxy)
t = threading.Thread(target=handler.serve_forever)
t.setDaemon(True)
t.start()
kodiutils.notification('Proxy Server Started', 'Proxy server for HD')
