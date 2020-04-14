
import re
import json
import time
import requests
from urlparse import parse_qs, urlparse
import SimpleHTTPServer
import base64
import threading
import os
from datetime import datetime
import hashlib
from xbmc import translatePath, log, LOGNOTICE
from resources.lib import utils, kodiutils

headers = utils.getHeaders()
qmap = {"Low": "_LOW", "Medium": "_MED", "High": "_HIG", "STB": "_STB"}

SERVER = "https://jiotv.live.cdn.jio.com"


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
        self.maxq = 'maxq' in self.params and int(self.params['maxq'][0])
        self.hlsrx = '' if not self.ishls else '/'+self.params['hls'][0]
        self.quality = qmap[kodiutils.get_setting('quality')]

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
                self.proxy.send_response(404, "Not Found")
        except Exception, e:
            log(str(e), LOGNOTICE)
            if(self.proxy):
                self.proxy.send_response(
                    500, "Internal Server Error")

    def getMaster(self):
        effective_url = "{4}{0}/{1}{2}/{1}{3}.m3u8".format(
            self.hlsrx, self.channel_name, '_HLS' if self.ishls else '', self.quality, SERVER)
        resp = ChannelRequestHandler.make_requests(effective_url)
        if resp.status_code == 411:
            kodiutils.notification(
                "Error", "JioTV can not be accessed from outside India")
        self.proxy.send_response(resp.status_code, "OK")
        for key, val in resp.headers.items():
            self.proxy.send_header(key, val)
        # self.proxy.send_header('Content-Length', len(resp.content))
        self.proxy.end_headers()
        self.proxy.wfile.write(resp.content)

    def getM3U8(self):
        m3u8 = self.path.split('/')[3]
        effective_url = "{4}{0}/{1}{2}/{3}".format(
            self.hlsrx, self.channel_name,  '_HLS' if self.ishls else '', m3u8, SERVER)
        resp = ChannelRequestHandler.make_requests(effective_url)
        if resp.status_code == 411:
            kodiutils.notification(
                "Error", "JioTV can not be accessed from outside India")
        ts = self.getTS(resp.text)
        while not ts or resp.status_code != 200:
            resp = ChannelRequestHandler.make_requests(effective_url)
            ts = self.getTS(resp.text)

        if not self.ishls:
            rq = int(re.search('(.*?_)(\d+)\.m3u8', m3u8).group(2))
            quality = rq >= self.maxq and re.sub(
                '\_\d+\-', '_{0}-'.format(self.maxq), ts.group()[1:])
        else:
            quality = m3u8[:1] + ts.group()[2:]

        resp_text = self.updateTS(resp.text, quality)
        resp_text = self.updateKey(resp_text, quality)
        self.proxy.send_response(resp.status_code, 'OK')
        self.proxy.send_header('Content-Type', 'application/vnd.apple.mpegurl')
        self.proxy.send_header('Connection', 'keep-alive')
        self.proxy.send_header('Content-Length', len(resp_text))
        self.proxy.end_headers()
        self.proxy.wfile.write(resp_text)

    def resolveTS(self):
        ts = self.path.split('/')[3]
        for _ in range(0, 3):
            effective_url = "{2}/{0}/{1}".format(
                self.channel_name, ts, SERVER)
            resp = requests.get(effective_url)
            if resp.status_code == 200:
                break
            elif resp.status_code == 404:
                timestamp = ts[ts.index('-')+1:ts.index('.')]
                ts = ts.replace(timestamp, str(int(timestamp)+2000))

        if resp.status_code == 200:
            self.proxy.send_response(resp.status_code, 'OK')
            self.proxy.send_header('Content-Type', 'video/mp2t')
            self.proxy.send_header('Connection', 'keep-alive')
            self.proxy.send_header('Content-Length', len(resp.content))
            self.proxy.end_headers()
            self.proxy.wfile.write(resp.content)
        elif resp.status_code == 411:
            kodiutils.notification(
                "Error", "JioTV can not be accessed from outside India")
        else:
            self.proxy.send_response(resp.status_code)

    def getKey(self):
        global headers
        key = self.path.split('/')[3]
        effective_url = "https://tv.media.jio.com/streams_live/{0}/{1}".format(
            self.channel_name, key)
        if not headers:
            headers = utils.getHeaders()
        resp = ChannelRequestHandler.make_requests(effective_url, headers)
        if resp.status_code == 411:
            kodiutils.notification(
                "Error", "JioTV can not be accessed from outside India")
        self.proxy.send_response(resp.status_code, 'OK')
        self.proxy.send_header('Content-Type', 'application/octet-stream')
        self.proxy.send_header('Connection', 'keep-alive')
        self.proxy.send_header('Content-Length', len(resp.content))
        self.proxy.end_headers()
        self.proxy.wfile.write(resp.content)

    def getTS(self, text):
        return re.search('\n(\d+\_|\d+\-)' if self.ishls else '\n' + self.channel_name+'(\_\d+\-)', text)

    def updateTS(self, text, quality=False):
        ts_re = '\n(\d+\_|\d+\-)' if self.ishls else '\n' + \
            self.channel_name+'(\_\d+\-)'
        if quality:
            return re.sub(ts_re, '\n{3}{0}/{1}_HLS/{2}'.format(
                self.hlsrx, self.channel_name, quality, SERVER), text) if self.ishls else re.sub(ts_re, '\n'+quality, text)
        return re.sub(ts_re, '\n{3}{0}/{1}_HLS/{2}'.format(
            self.hlsrx, self.channel_name, self.getTS(text).group()[1:], SERVER), text) if self.ishls else re.sub(ts_re, '\n{0}'.format(self.getTS(text).group()[1:]), text)

    def updateKey(self, text, quality=False):
        if self.ishls:
            return text.replace('https://tv.media.jio.com/streams_live', SERVER+'/streams_live')
        return re.sub('([\w_\/:\.]*)(\_\d+\-)(\d+)\.key', '{0}{1}.key'.format(self.channel_name, '\\2\\3' if not quality else '_{0}-\\3'.format(self.maxq)), text)

    @staticmethod
    def make_requests(url, headers=False, stream=False, delay=6000):
        params = ChannelRequestHandler.getTokenParams(delay=delay)
        headers = headers or {"User-Agent": "jiotv"}
        return requests.get(url, params=params, headers=headers, stream=stream)

    @staticmethod
    def getTokenParams(delay):
        def magic(x): return base64.b64encode(hashlib.md5(x.encode()).digest()).decode().replace(
            '=', '').replace('+', '-').replace('/', '_').replace('\r', '').replace('\n', '')
        pxe = str(int(time.time() + delay))
        jct = magic("cutibeau2ic9p-O_v1qIyd6E-rf8_gEOQ"+pxe)
        return {"jct": jct, "pxe": pxe, "st": "9p-O_v1qIyd6E-rf8_gEOQ"}


class CatchupRequestHandler():

    def __init__(self, proxy):
        self.proxy = proxy
        p = urlparse(proxy.path)
        self.path = p.path
        self.params = parse_qs(p.query)

        self.channel_name = self.path.split('/')[2]
        self.startEpoch = 0 if not 'startEpoch' in self.params else int(
            self.params['startEpoch'][0])

        try:
            if self.path.endswith('.m3u8'):
                self.getM3U8()
            elif self.path.endswith('.key'):
                self.getKey()
            else:
                self.proxy.send_response(404)
        except Exception, e:
            log(str(e), LOGNOTICE)
            self.proxy.send_response(500)
            self.proxy.send_header('Connection', 'close')
            self.proxy.end_headers()

    def getM3U8(self):
        timestr = datetime.fromtimestamp(
            int(self.startEpoch*.001)).strftime('%d_%m_%y_%H_%M')
        self.mp4 = '{0}_4000_{1}.mp4'.format(self.channel_name, timestr)
        catchup_url = "http://jiotv.catchup.cdn.jio.com/{0}/{1}/index-v1-a1.m3u8".format(
            self.channel_name, self.mp4)
        resp = ChannelRequestHandler.make_requests(catchup_url, delay=10)
        resp_text = self.updateTS(resp.text)
        resp_text = self.updateKey(resp_text)
        self.proxy.send_response(resp.status_code)
        self.proxy.send_header('Content-Type', 'application/vnd.apple.mpegurl')
        self.proxy.send_header('Content-Length', len(resp_text))
        self.proxy.end_headers()
        self.proxy.wfile.write(resp_text)

    def updateTS(self, text):
        ts_re = '\n(seg\-\d+\-)'
        return re.sub(ts_re, '\nhttp://jiotv.catchup.cdn.jio.com/{0}/{1}/\\1'.format(self.channel_name, self.mp4), text)

    def updateKey(self, text):
        return text.replace('https://tv.media.jio.com/streams_catchup/{0}/'.format(self.channel_name), '')

    def getKey(self):
        global headers
        mp4 = self.path.split('/')[3]
        key = self.path.split('/')[4]
        effective_url = "https://tv.media.jio.com/streams_catchup/{0}/{1}/{2}".format(
            self.channel_name, mp4, key)
        if not headers:
            headers = utils.getHeaders()
        resp = ChannelRequestHandler.make_requests(effective_url, headers)
        self.proxy.send_response(resp.status_code)
        self.proxy.send_header('Content-Type', 'application/octet-stream')
        self.proxy.send_header('Content-Length', len(resp.content))
        self.proxy.end_headers()
        self.proxy.wfile.write(resp.content)


class JioTVProxy(SimpleHTTPServer.SimpleHTTPRequestHandler):

    def do_GET(self):
        self.protocol_version = 'HTTP/1.1'
        if 'catchup' in self.path:
            CatchupRequestHandler(self)
        else:
            ChannelRequestHandler(self)
