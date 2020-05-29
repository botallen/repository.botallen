# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# basic imports
import re
import time
import urlquick
from urlparse import parse_qs, urlparse
import SimpleHTTPServer
import base64
import os
from datetime import datetime
import hashlib
from random import randint

# add-on imports
from resources.lib import utils

# codequick imports
from codequick import Script
from codequick.script import Settings
from codequick.storage import PersistentDict

headers = utils.getHeaders()
qmap = {"Low": "_LOW", "Medium": "_MED", "High": "_HIG", "STB": "_STB"}

_server = "jiotv.live.cdn.jio.com"
cdn = ["http://sklktcdnems06.cdnsrv.jio.com", "http://sbglrcdnems01.cdnsrv.jio.com", "http://sklktcdnems05.cdnsrv.jio.com",
       "http://sbglrcdnems03.cdnsrv.jio.com", "http://sptnacdnems03.cdnsrv.jio.com", "http://ssrigcdnems02.cdnsrv.jio.com"]
SERVER = cdn[randint(0, 5)] + "/" + _server


class ChannelRequestHandler():

    def __init__(self, proxy):
        self.proxy = proxy
        p = urlparse(proxy.path)
        self.path = p.path
        self.params = parse_qs(p.query)
        play_url = self.path.endswith('master.m3u8')
        m3u8_url = self.path.endswith('.m3u8')
        ts_url = self.path.endswith('.ts')
        key_url = self.path.endswith('.key')

        self.ishls = 'packagerx' in self.path
        self.channel_name = self.path.split(
            '/')[3] if self.ishls else self.path.split('/')[2]
        self.maxq = 'maxq' in self.params and int(self.params['maxq'][0])
        self.hlsrx = '' if not self.ishls else "/"+self.path.split('/')[2]
        self.quality = qmap[Settings.get_string('quality')]

        try:
            if play_url:
                self.getMaster()
            elif m3u8_url:
                self.getM3U8()
            elif key_url:
                self.resolveKey()
            elif ts_url:
                self.resolveTS()
            else:
                Script.log("Resource not found by proxy", lvl=Script.INFO)
                self.proxy.send_error(404, "Not Found")
        except Exception, e:
            Script.log(e, lvl=Script.INFO)
            if(self.proxy):
                self.proxy.send_error(500, "Internal Server Error")
                self.proxy.wfile.write(str(e).encode("utf-8"))

    def getMaster(self):
        effective_url = "{4}{0}/{1}{2}/{1}{3}.m3u8".format(
            self.hlsrx, self.channel_name, '_HLS' if self.ishls else '', self.quality, SERVER)
        resp = ChannelRequestHandler.make_requests(effective_url)
        if resp.status_code == 411:
            Script.notify(
                "Error", "JioTV can not be accessed from outside India")
        self.proxy.send_response(resp.status_code, "OK")
        for k, v in resp.headers.items():
            self.proxy.send_header(k, v)
        self.proxy.end_headers()
        self.proxy.wfile.write(resp.text)

    def getM3U8(self):
        m3u8 = self.path.split('/')[-1]
        effective_url = "{4}{0}/{1}{2}/{3}".format(
            self.hlsrx, self.channel_name,  '_HLS' if self.ishls else '', m3u8, SERVER)
        resp = ChannelRequestHandler.make_requests(effective_url)
        if resp.status_code == 411 or resp.status_code == 451:
            Script.notify(
                "Error", "JioTV can not be accessed from outside India")
            self.proxy.send_error(resp.status_code)
        else:
            if self.ishls:
                resp_text = self.refine(resp.text, quality=m3u8[:1])
            else:
                rq = int(re.search('(.*?_)(\d+)\.m3u8', m3u8).group(2))
                quality = rq >= self.maxq and self.maxq
                resp_text = self.refine(resp.text, quality)

            self.proxy.send_response(resp.status_code, 'OK')
            resp.headers.pop("Content-Length")
            for k, v in resp.headers.items():
                self.proxy.send_header(k, v)
            self.proxy.send_header('Content-Length', len(resp_text))
            self.proxy.end_headers()
            self.proxy.wfile.write(resp_text)

    def refine(self, text, quality=False):
        if self.ishls:
            rpls_regx = "{{0}}/{{1}}/{{2}}_HLS/{0}\g<2>".format(quality)
            text = re.sub(
                '(\d{1})([\-\_]?\d+\.ts)', rpls_regx.format(SERVER, self.hlsrx, self.channel_name), text)
            return text.replace('https://tv.media.jio.com/streams_live', SERVER+'/streams_live')
        elif quality:
            rpls_regx = "_{}".format(quality) if quality else "_\g<1>"
            text = re.sub('\_(\d{3,4})\-', rpls_regx+"-", text)
            with PersistentDict("proxy_cache", ttl=180) as cache:
                allkeys = re.findall(
                    self.channel_name+"\_\d{3,4}\-\d{13}\.key", text)
                Script.log("Found %d different keys" %
                           len(allkeys), lvl=Script.DEBUG)
                diff = None
                for key in allkeys:
                    original_timestamp = re.search(
                        "\-(\d{13})\.key", key).group(1)
                    if cache.get(key):
                        timestamp, newIV = cache.get(key)
                        Script.log("Using cached timestamp %s" %
                                   timestamp, lvl=Script.DEBUG)
                    elif diff:
                        timestamp = int(original_timestamp) - int(diff)
                        newIV = '0x%0*X' % (32, int(timestamp))
                        cache[key] = (timestamp, newIV)
                        Script.log("Using diff predicted timestamp %s" %
                                   timestamp, lvl=Script.DEBUG)
                    else:
                        timestamp = self._find_valid_key(key)
                        diff = int(original_timestamp) - int(timestamp)
                        newIV = '0x%0*X' % (32, int(timestamp))
                        cache[key] = (timestamp, newIV)
                        Script.log("Using new valid timestamp %s" %
                                   timestamp, lvl=Script.DEBUG)

                    Script.log("Replacing old IV with %s" %
                               newIV, lvl=Script.DEBUG)
                    text = re.sub('(\_\d{{3,4}}\-){0}(\.key\",IV=)[\w\d]*'.format(original_timestamp),
                                  "\g<1>{0}\g<2>{1}".format(timestamp, newIV), text)
            return text.replace("https://tv.media.jio.com/streams_live/{0}/".format(self.channel_name), "")
        else:
            rpls_regx = "{0}/{1}/\g<1>".format(SERVER, self.channel_name)
            text = re.sub(
                '([\w_\/:\.]*\_\d{3,4}\-\d{13}\.ts)', rpls_regx, text)
            return text
            # text = re.sub(',IV=[\w\d]*', ",IV=0x00000000000000000000000000000000", text)
            # return text.replace("https://tv.media.jio.com/streams_live/{0}/".format(self.channel_name), "")

    def getTS(self, text):
        return re.search('(\d+\_\d+\.ts|\d+\-\d+\.ts)' if self.ishls else '([\w_\/:\.]*\_\d{3,4}\-\d{13}\.ts)', text)

    def resolveTS(self):
        ts = self.path.split('/')[-1]

        effective_url = "{2}/{0}/{1}".format(
            self.channel_name, ts, SERVER)
        resp = urlquick.get(effective_url, raise_for_status=False, max_age=-1)

        if resp.status_code == 404:
            with PersistentDict("proxy_cache", ttl=180) as cache:
                if cache.get(ts):
                    Script.log("Found cached ts effective url",
                               lvl=Script.DEBUG)
                    resp = urlquick.get(
                        cache.get(ts), raise_for_status=False, max_age=-1)
                else:
                    for i in range(1, 5):
                        timestamp = re.search("\-(\d{13})\.ts", ts).group(1)
                        ts = ts.replace(timestamp, str(int(timestamp)+(i*2000))
                                        if i % 2 == 0 else str(int(timestamp)-(i*2000)))
                        effective_url = "{2}/{0}/{1}".format(
                            self.channel_name, ts, SERVER)
                        resp = urlquick.get(
                            effective_url, raise_for_status=False, max_age=-1)
                        if resp.status_code == 200:
                            cache[ts] = effective_url
                            break
        if resp.status_code == 200:
            self.proxy.send_response(resp.status_code, 'OK')
            self.proxy.send_header('Content-Type', 'video/mp2t')
            self.proxy.send_header('Connection', 'keep-alive')
            self.proxy.send_header('Content-Length', len(resp.content))
            self.proxy.end_headers()
            self.proxy.wfile.write(resp.content)
        elif resp.status_code == 411 or resp.status_code == 451:
            Script.notify(
                "Error", "JioTV can not be accessed from outside India")
            self.proxy.send_error(resp.status_code)
        elif resp.status_code >= 400:
            self.proxy.send_error(resp.status_code)
        else:
            self.proxy.send_response(resp.status_code)

    def _find_valid_key(self, key):
        global headers
        if not headers:
            headers = utils.getHeaders()

        for _ in range(1, 15):
            effective_url = "https://tv.media.jio.com/streams_live/{0}/{1}".format(
                self.channel_name, key)
            resp = ChannelRequestHandler.make_requests(
                effective_url, headers, max_age=urlquick.MAX_AGE)
            timestamp = re.search("\-(\d{13})\.key", key).group(1)
            if resp.status_code == 200:
                return timestamp
            elif resp.status_code == 404:
                key = key.replace(timestamp, str(
                    int(timestamp)+(_*2000)) if _ % 2 == 0 else str(int(timestamp)-(_*2000)))
        return timestamp

    def resolveKey(self):
        global headers
        key = self.path.split('/')[-1]
        effective_url = "https://tv.media.jio.com/streams_live/{0}/{1}".format(
            self.channel_name, key)
        if not headers:
            headers = utils.getHeaders()
        resp = ChannelRequestHandler.make_requests(
            effective_url, headers, max_age=urlquick.MAX_AGE)

        if resp.status_code == 411 or resp.status_code == 451:
            Script.notify(
                "Error", "JioTV can not be accessed from outside India")
            self.proxy.send_error(resp.status_code)
        elif resp.status_code >= 400:
            self.proxy.send_error(resp.status_code)
        else:
            self.proxy.send_response(resp.status_code, 'OK')
            self.proxy.send_header('Content-Type', 'application/octet-stream')
            self.proxy.send_header('Connection', 'keep-alive')
            self.proxy.send_header('Content-Length', len(resp.content))
            self.proxy.end_headers()
            self.proxy.wfile.write(resp.content)

    @staticmethod
    def make_requests(url, headers=False, delay=6000, max_age=-1, **kwargs):
        params = ChannelRequestHandler.getTokenParams(delay=delay)
        headers = headers or {"User-Agent": "jiotv"}
        return urlquick.get(url, params=params, headers=headers, max_age=max_age, raise_for_status=False, **kwargs)

    @staticmethod
    def getTokenParams(delay):
        def magic(x): return base64.b64encode(hashlib.md5(x.encode()).digest()).decode().replace(
            '=', '').replace('+', '-').replace('/', '_').replace('\r', '').replace('\n', '')
        pxe = str(int(time.time() + delay))
        jct = magic("cutibeau2ic9p-O_v1qIyd6E-rf8_gEOQ"+pxe)
        return {"jct": jct, "pxe": pxe, "st": "9p-O_v1qIyd6E-rf8_gEOQ"}


class JioTVProxy(SimpleHTTPServer.SimpleHTTPRequestHandler):

    def do_GET(self):
        self.protocol_version = 'HTTP/1.1'
        try:
            ChannelRequestHandler(self)
        except Exception, e:
            Script.log(e, lvl=Script.DEBUG)
            pass

    def do_HEAD(self):
        self.protocol_version = 'HTTP/1.1'
        self.send_response(200, "OK")
