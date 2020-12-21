# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# basic imports
import SimpleHTTPServer
import os
from urlparse import parse_qs, urlparse
from kodi_six import xbmc, xbmcaddon
from resources.lib.utils import login

# codequick imports
from codequick import Script

ADDON = xbmcaddon.Addon()
ADDON_PATH = ADDON.getAddonInfo("path")


class JioTVProxy(SimpleHTTPServer.SimpleHTTPRequestHandler):

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/web/login":
            self.send_response(200)

            html = os.path.join(xbmc.translatePath(
                ADDON_PATH), "resources", "login.html")
            try:
                f = open(html, 'rb')
            except IOError:
                self.send_error(404, "File not found")
                return None

            self.send_header("Content-type", "text/html")
            fs = os.fstat(f.fileno())
            self.send_header("Content-Length", str(fs.st_size))
            self.end_headers()
            self.wfile.write(bytes(f.read()))
            f.close()
            return
        else:
            self.send_error(404, "File not found")

    def do_POST(self):
        if self.path == "/login":
            data_string = self.rfile.read(
                int(self.headers['Content-Length']))

            qs = parse_qs(data_string)
            error = None
            try:
                error = login(qs.get("username")[0], qs.get("password")[0])
            except Exception as e:
                Script.log(e, lvl=Script.ERROR)
                error = e.message

            if error:
                location = "/web/login?error="+str(error)
            else:
                location = "/web/login?success"
            self.send_response(302)
            self.send_header('Location', location)
            self.end_headers()
            # self.wfile.write(bytes(qs.get("username")[0]))
        else:
            self.send_error(404, "File not found")
