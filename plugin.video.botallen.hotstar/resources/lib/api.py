# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import urlquick
from xbmc import executebuiltin
from functools import reduce
from .contants import API_BASE_URL, BASE_HEADERS, url_constructor
import resources.lib.utils as U
from codequick import Script
from codequick.storage import PersistentDict
from urllib import quote_plus
from urlparse import urlparse, parse_qs
import time
import hashlib
import hmac
import json
import re
from uuid import uuid4
from base64 import b64decode

deep_get = U.deep_get


class HotstarAPI:

    def __init__(self):
        self.session = urlquick.Session()
        self.session.headers.update(BASE_HEADERS)

    def getMenu(self):
        url = url_constructor("/o/v2/menu")
        resp = self.get(
            url, headers={"x-country-code": "in", "x-platform-code": "ANDROID_TV"})
        return deep_get(resp, "body.results.menuItems")

    def getPage(self, url):
        results = deep_get(self.get(url), "body.results")
        itmes = deep_get(results, "trays.items")
        nextPageUrl = results.get("nextOffsetURL") or deep_get(
            results, "trays.nextOffsetURL")
        return itmes, nextPageUrl

    def getTray(self, url, search_query=None):
        if search_query:
            url = url_constructor("/s/v1/scout?q=%s&size=30" %
                                  quote_plus(search_query))
        results = self.get(url)

        if "data" in results:
            results = results.get("data")
            results['items'] = deep_get(results, "data.itmes").values()
        else:
            results = deep_get(results, "body.results")

        items = results.get("items") or deep_get(
            results, "assets.items") or (results.get("map") and results.get("map").values())
        nextPageUrl = deep_get(
            results, "assets.nextOffsetURL") or results.get("nextOffsetURL")
        return items, nextPageUrl

    def getPlay(self, contentId, subtag, drm=False):
        url = url_constructor("/play/v1/playback/content/%s" % contentId)
        encryption = "widevine" if drm else "plain"
        resp = self.get(
            url, headers=self._getPlayHeaders(), params=self._getPlayParams(subtag, encryption), max_age=-1)
        playBackSets = deep_get(resp, "data.playBackSets")
        if playBackSets is None:
            return None, None, None
        playbackUrl, licenceUrl, playbackProto = HotstarAPI._findPlayback(
            playBackSets, encryption)
        return playbackUrl, licenceUrl, playbackProto

    def getExtItem(self, contentId):
        url = url_constructor(
            "/o/v1/multi/get/content?ids={0}".format(contentId))
        resp = self.get(url)
        url = deep_get(resp, "body.results.map.{0}.uri".format(contentId))
        if url is None:
            return None, None, None
        resp = self.get(url)
        item = deep_get(resp, "body.results.item")
        if int(contentId) in [1260000033, 1260000025, 1260000034, 1260000024, 1260000035]:
            item["encrypted"] = True
        return "com.widevine.alpha" if item.get("encrypted") else False, item.get("isSubTagged") and "subs-tag:%s|" % item.get("features")[0].get("subType"), item.get("title")

    def doLogin(self):
        url = url_constructor(
            "/in/aadhar/v2/firetv/in/users/logincode/")
        resp = self.post(url, headers={"Content-Length": "0"})
        code = deep_get(resp, "description.code")
        yield (code, 1)
        for i in range(2, 101):
            resp = self.get(url+code, max_age=-1)
            token = deep_get(resp, "description.userIdentity")
            if token:
                with PersistentDict("userdata.pickle") as db:
                    db["token"] = token
                    db["deviceId"] = uuid4()
                    db["udata"] = json.loads(json.loads(
                        b64decode(token.split(".")[1]+"========")).get("sub"))
                    if db.get("isGuest"):
                        del db["isGuest"]
                    db.flush()
                yield code, 100
                break
            yield code, i

    def doLogout(self):
        with PersistentDict("userdata.pickle") as db:
            db.clear()
            db.flush()
        Script.notify("Logout Success", "You are logged out")

    def get(self, url, **kwargs):
        try:
            response = self.session.get(url, **kwargs)
            return response.json()
        except Exception, e:
            return self._handleError(e, url, "get", **kwargs)

    def post(self, url, **kwargs):
        try:
            response = self.session.post(url, **kwargs)
            return response.json()
        except Exception, e:
            return self._handleError(e, url, "post", **kwargs)

    def _handleError(self, e, url, _rtype, **kwargs):
        if e.__class__.__name__ == "ValueError":
            Script.log("Can not parse response of request url %s" %
                       url, lvl=Script.DEBUG)
            Script.notify("Internal Error", "")
        elif e.__class__.__name__ == "HTTPError":
            if e.code == 402 or e.code == 403:
                with PersistentDict("userdata.pickle") as db:
                    if db.get("isGuest"):
                        Script.notify(
                            "Login Error", "Please login to watch this content")
                        executebuiltin(
                            "RunPlugin(plugin://plugin.video.botallen.hotstar/resources/lib/main/login/)")
                    else:
                        Script.notify(
                            "Subscription Error", "You don't have valid subscription to watch this content", display_time=2000)
            elif e.code == 401:
                new_token = self._refreshToken()
                if new_token:
                    kwargs.get("headers") and kwargs['headers'].update(
                        {"X-HS-UserToken": new_token})
                    if _rtype == "get":
                        return self.get(url, **kwargs)
                    else:
                        return self.post(url, **kwargs)
                else:
                    Script.notify("Token Error", "Token not found")

            elif e.code == 474 or e.code == 475:
                Script.notify(
                    "VPN Error", "Your VPN provider does not support Hotstar")
            else:
                raise urlquick.HTTPError(e.filename, e.code, e.msg, e.hdrs)
            return False
        else:
            Script.log("Got unexpected response for request url %s" %
                       url, lvl=Script.DEBUG)
            Script.notify(
                "API Error", "Raise issue if you are continuously facing this error")

    def _refreshToken(self):
        try:
            with PersistentDict("userdata.pickle") as db:
                oldToken = db.get("token")
                if oldToken:
                    resp = self.session.get(url_constructor("/in/aadhar/v2/firetv/in/users/refresh-token"),
                                            headers={"userIdentity": oldToken, "deviceId": db.get("deviceId", uuid4())}, raise_for_status=False, max_age=-1).json()
                    if resp.get("errorCode"):
                        return resp.get("message")
                    new_token = deep_get(resp, "description.userIdentity")
                    db['token'] = new_token
                    db.flush()
                    return new_token
            return False
        except Exception, e:
            return e

    @staticmethod
    def _getPlayHeaders(includeST=False, playbackUrl=None):
        with PersistentDict("userdata.pickle") as db:
            token = db.get("token")
        auth = HotstarAPI._getAuth(includeST)
        if playbackUrl:
            parsed_url = urlparse(playbackUrl)
            qs = parse_qs(parsed_url.query)
            hdnea = "hdnea=%s;" % qs.get("hdnea")[0]
            Script.log(hdnea, lvl=Script.DEBUG)
        return {
            "hotstarauth": auth,
            "X-Country-Code": "in",
            "X-HS-AppVersion": "3.3.0",
            "X-HS-Platform": "firetv",
            "X-HS-UserToken": token,
            "Cookie": playbackUrl and hdnea,
            "User-Agent": "Hotstar;in.startv.hotstar/3.3.0 (Android/8.1.0)"
        }

    @staticmethod
    def _getAuth(includeST=False):
        _AKAMAI_ENCRYPTION_KEY = b'\x05\xfc\x1a\x01\xca\xc9\x4b\xc4\x12\xfc\x53\x12\x07\x75\xf9\xee'
        st = int(time.time())
        exp = st + 6000
        auth = 'st=%d~exp=%d~acl=/*' % (st,
                                        exp) if includeST else 'exp=%d~acl=/*' % exp
        auth += '~hmac=' + hmac.new(_AKAMAI_ENCRYPTION_KEY,
                                    auth.encode(), hashlib.sha256).hexdigest()
        return auth

    @staticmethod
    def _getPlayParams(subTag="", encryption="widevine"):
        with PersistentDict("userdata.pickle") as db:
            deviceId = db.get("deviceId") or uuid4()
        return {
            "os-name": "firetv",
            "desired-config": "audio_channel:stereo|encryption:%s|ladder:tv|package:dash|%svideo_codec:h264" % (encryption, subTag or ""),
            "device-id": str(deviceId),
            "os-version": "8.1.0"
        }

    @staticmethod
    def _findPlayback(playBackSets, encryption="widevine"):
        for each in playBackSets:
            Script.log("Checking combination %s for encryption %s" %
                       (each.get("tagsCombination"), encryption), lvl=Script.DEBUG)
            if re.match(".*?encryption:%s.*?ladder:tv.*?package:dash.*" % encryption, each.get("tagsCombination")):
                Script.log("Found Stream! URL : %s LicenceURL: %s Encryption: %s" %
                           (each.get("playbackUrl"), each.get("licenceUrl"), encryption), lvl=Script.DEBUG)
                return (each.get("playbackUrl"), each.get("licenceUrl"), "mpd")
            elif re.match(".*?encryption:plain.*?ladder:tv.*?package:dash.*", each.get("tagsCombination")):
                Script.log("Found Stream! URL : %s LicenceURL: %s Encryption: %s" %
                           (each.get("playbackUrl"), each.get("licenceUrl"), "plain"), lvl=Script.DEBUG)
                return (each.get("playbackUrl"), each.get("licenceUrl"), "mpd")
            elif re.match(".*?encryption:plain.*?ladder:tv.*?package:hls.*", each.get("tagsCombination")):
                Script.log("Found Stream! URL : %s LicenceURL: %s Encryption: %s" %
                           (each.get("playbackUrl"), each.get("licenceUrl"), "plain"), lvl=Script.DEBUG)
                return (each.get("playbackUrl"), each.get("licenceUrl"), "hls")
        playbackUrl = playBackSets[0].get("playbackUrl")
        licenceUrl = playBackSets[0].get("licenceUrl")
        Script.log("No stream found for desired config. Using %s" %
                   playbackUrl, lvl=Script.INFO)
        return (playbackUrl, licenceUrl, "hls" if ".m3u8" in playbackUrl else "mpd")
