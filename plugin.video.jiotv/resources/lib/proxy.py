
import re
import json
import time
import requests
from urlparse import parse_qs, urlparse
import SimpleHTTPServer
import base64
import threading
import os
import hashlib
from xbmc import translatePath, log, LOGNOTICE
from xbmcaddon import Addon

ADDON = Addon()
ADDONDATA = translatePath(ADDON.getAddonInfo('profile')).decode("utf-8")
if os.path.isfile(ADDONDATA + 'headers.json'):
    with open(ADDONDATA + 'headers.json', 'r') as f:
        headers = json.load(f)


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

        self.channel_name = self.path.split('/')[2]
        self.ishls = 'hls' in self.params
        self.hlsrx = '' if not self.ishls else '/'+self.params['hls'][0]

        try:
            if play_url:
                self.getMaster()
            elif m3u8_url:
                self.getM3U8()
            elif key_url:
                self.getKey()
            elif ts_url:
                self.resolveTS()
            else:
                self.proxy.send_response(404)
        except Exception, e:
            log(str(e), LOGNOTICE)
            self.proxy.send_response(500)
            self.proxy.send_header('Connection', 'close')
            self.proxy.end_headers()

    def getMaster(self):
        effective_url = "http://jiotvstb.live.cdn.jio.com{0}/{1}{2}/{1}_STB.m3u8".format(
            self.hlsrx, self.channel_name, '_HLS' if self.ishls else '')
        resp = ChannelRequestHandler.make_requests(effective_url)
        self.proxy.send_response(resp.status_code)
        self.proxy.send_header('Content-Type', 'application/vnd.apple.mpegurl')
        self.proxy.send_header('Content-Length', len(resp.content))
        self.proxy.end_headers()
        self.proxy.wfile.write(resp.content)

    def getM3U8(self):
        m3u8 = self.path.split('/')[3]
        effective_url = "http://jiotvstb.live.cdn.jio.com{0}/{1}{2}/{3}".format(
            self.hlsrx, self.channel_name,  '_HLS' if self.ishls else '', m3u8)
        resp = ChannelRequestHandler.make_requests(effective_url)

        ts = self.getTS(resp.text)
        while not ts or resp.status_code != 200:
            resp = ChannelRequestHandler.make_requests(effective_url)
            ts = self.getTS(resp.text)

        if not self.ishls:
            full_ts = self.getTS(resp.text, full=True)
            ts_url = 'http://jiotvstb.live.cdn.jio.com/{0}/{1}'.format(
                self.channel_name, re.sub('\_\d+\-', '_1200-', full_ts.group()[1:]))
            check_filter = requests.head(ts_url)
            quality = False if check_filter.status_code == 404 <= 1200 else re.sub(
                '\_\d+\-', '_1200-', ts.group()[1:])
        else:
            quality = m3u8[:1] + ts.group()[2:]

        resp_text = self.updateTS(resp.text, quality)
        resp_text = self.updateKey(resp_text, quality)
        self.proxy.send_response(resp.status_code)
        self.proxy.send_header('Content-Type', 'application/vnd.apple.mpegurl')
        self.proxy.send_header('Content-Length', len(resp_text))
        self.proxy.end_headers()
        self.proxy.wfile.write(resp_text)

    def resolveTS(self):
        ts = self.path.split('/')[3]
        for _ in range(0, 3):
            effective_url = "http://jiotv.live.cdn.jio.com/{0}/{1}".format(
                self.channel_name, ts)
            resp = requests.get(effective_url)
            if resp.status_code == 200:
                break
            elif resp.status_code == 404:
                timestamp = ts[ts.index('-')+1:ts.index('.')]
                ts = ts.replace(timestamp, str(int(timestamp)+2000))

        if resp.status_code == 200:
            self.proxy.send_response(resp.status_code)
            self.proxy.send_header('Content-Type', 'video/mp2t')
            self.proxy.send_header('Connection', 'keep-alive')
            self.proxy.send_header('Content-Length', len(resp.content))
            self.proxy.end_headers()
            self.proxy.wfile.write(resp.content)
        else:
            self.proxy.send_response(resp.status_code)

    def getKey(self):
        global headers
        key = self.path.split('/')[3]
        effective_url = "https://tv.media.jio.com/streams_live/{0}/{1}".format(
            self.channel_name, key)
        if not headers:
            with open(ADDONDATA + 'headers.json', 'r') as f:
                headers = json.load(f)
        resp = ChannelRequestHandler.make_requests(effective_url, headers)
        self.proxy.send_response(resp.status_code)
        self.proxy.send_header('Content-Type', 'application/octet-stream')
        self.proxy.send_header('Content-Length', len(resp.content))
        self.proxy.end_headers()
        self.proxy.wfile.write(resp.content)

    def getTS(self, text, full=False):
        return re.search('\n(\d+\_\d+|\d+\-\d+)\.ts' if self.ishls else '\n' +
                         self.channel_name+'(\_\d+\-\d+)\.ts', text) if full else re.search('\n(\d+\_|\d+\-)' if self.ishls else '\n' +
                                                                                            self.channel_name+'(\_\d+\-)', text)

    def updateTS(self, text, quality=False):
        ts_re = '\n(\d+\_|\d+\-)' if self.ishls else '\n' + \
            self.channel_name+'(\_\d+\-)'
        if quality:
            return re.sub(ts_re, '\nhttp://jiotvstb.live.cdn.jio.com{0}/{1}_HLS/{2}'.format(
                self.hlsrx, self.channel_name, quality), text) if self.ishls else re.sub(ts_re, '\n{0}'.format(quality), text)
        return re.sub(ts_re, '\nhttp://jiotvstb.live.cdn.jio.com{0}/{1}_HLS/{2}'.format(
            self.hlsrx, self.channel_name, self.getTS(text).group()[1:]), text) if self.ishls else re.sub(ts_re, '\n{0}'.format(self.getTS(text).group()[1:]), text)

    def updateKey(self, text, quality=False):
        if self.ishls:
            return text.replace('https://tv.media.jio.com/streams_live', 'http://sngprecdnems14.cdnsrv.jio.com/jiotvstb.live.cdn.jio.com/streams_live')
        # key_re = self.channel_name+'(\_\d+\-\d+)\.key'
        # key_find = re.search(key_re, text)
        # quality = quality and re.sub('\_\d+\-', '_1200-', key_find.group())
        return re.sub('([\w_\/:\.]*)(\_\d+\-)(\d+)\.key', '{0}{1}.key'.format(self.channel_name, '\\2\\3' if not quality else '_1200-\\3'), text)

    @staticmethod
    def make_requests(url, headers=False, stream=False):
        params = ChannelRequestHandler.getTokenParams()
        headers = headers or {"User-Agent": "jiotv"}
        return requests.get(url, params=params, headers=headers, stream=stream)

    @staticmethod
    def getTokenParams():
        def magic(x): return base64.b64encode(hashlib.md5(x.encode()).digest()).decode().replace(
            '=', '').replace('+', '-').replace('/', '_').replace('\r', '').replace('\n', '')
        delay = 2000
        pxe = str(int(time.time() + delay))
        jct = magic("cutibeau2ic9p-O_v1qIyd6E-rf8_gEOQ"+pxe)
        return {"jct": jct, "pxe": pxe, "st": "9p-O_v1qIyd6E-rf8_gEOQ"}


class JioTVProxy(SimpleHTTPServer.SimpleHTTPRequestHandler):

    def do_GET(self):
        ChannelRequestHandler(self)

    def do_HEAD(self):
        self.send_response(200)
