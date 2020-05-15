# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import urlquick
from functools import reduce
from .contants import API_BASE_URL, BASE_HEADERS, url_constructor
from codequick import Script
from codequick.storage import PersistentDict
from urllib import quote_plus
from urlparse import urlparse, parse_qs
import time
import hashlib
import xbmcaddon
import hmac
import json
import re
import web_pdb
from uuid import uuid4
from base64 import b64decode

# urlquick.cache_cleanup(-1)

ADDON = xbmcaddon.Addon()

def deep_get(dictionary, keys, default=None):
    return reduce(lambda d, key: d.get(key, default) if isinstance(d, dict) else default, keys.split("."), dictionary)


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
        # Script.log(self._getPlayHeaders(), lvl=Script.INFO)
        # Script.log(self._getPlayParams(subtag, encryption), lvl=Script.INFO)
        resp = self.get(
            url, headers=self._getPlayHeaders(), params=self._getPlayParams(subtag, encryption), max_age=-1)
        playBackSets = deep_get(resp, "data.playBackSets")
        if playBackSets is None:
            return None, None, None
        playbackUrl, licenceUrl, playbackProto = HotstarAPI._findPlayback(
            playBackSets, encryption)
        subtitleUrl = re.sub(
            "([\w:\/\.]*)(master[\w+\_\-]*?\.[\w+]{3})([\w\/\?=~\*\-]*)", "\1subtitle/lang_en/subtitle.vtt\3", playbackUrl)
        Script.log(subtitleUrl, lvl=Script.INFO)
        return playbackUrl, licenceUrl, playbackProto

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
                    db["udata"] = json.loads(
                        b64decode(token.split(".")[1]+"========"))
                    db.flush()
                yield code, 100
                break
            yield code, i


    def doLoginFree(self):

        token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJ1bV9hY2Nlc3MiLCJleHAiOjE1ODY3OTEzMzEsImlhdCI6MTU4NjcwNDkzMSwiaXNzIjoiVFMiLCJzdWIiOiJ7XCJjb3VudHJ5Q29kZVwiOlwiaW5cIixcImN1c3RvbWVyVHlwZVwiOlwibnVcIixcImRldmljZUlkXCI6XCI4OTUyYWE5ZS1mZGY5LTQ2ZTMtYjU2Mi1jNTViMzdjZTMyYTdcIixcImhJZFwiOlwiMDBkY2FkN2M4NmQ4NDJiNTgxYmU4Mjg4OTRjMWYyMzRcIixcImlwXCI6XCIxMDMuMjEyLjE0MS4yNFwiLFwiaXNFbWFpbFZlcmlmaWVkXCI6ZmFsc2UsXCJpc1Bob25lVmVyaWZpZWRcIjpmYWxzZSxcImlzc3VlZEF0XCI6MTU4NjcwNDkzMTUzMSxcIm5hbWVcIjpcIkd1ZXN0IFVzZXJcIixcInBJZFwiOlwiNTQ1ZmQzNmE1NWM4NGExNWFkOTE3OGNlYWFhZmI0YTBcIixcInByb2ZpbGVcIjpcIkFEVUxUXCIsXCJzdWJzY3JpcHRpb25zXCI6e1wiaW5cIjp7fX0sXCJ0eXBlXCI6XCJkZXZpY2VcIixcInZlcnNpb25cIjpcInYyXCJ9IiwidmVyc2lvbiI6IjFfMCJ9.X1uJowi4-4eVquBDdTis76pbH44gso1y16i5zKTwRfg"

        with PersistentDict("userdata.pickle") as db:
            db["token"] = token
            db["deviceId"] = uuid4()
            db["udata"] = json.loads(
                b64decode(token.split(".")[1]+"========"))
            db.flush()

     	Script.notify("Login Free Success", "You have done Free Login")
                

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
            # Script.log(e, lvl=Script.INFO)
            self._handleError(e, url, **kwargs)

    def post(self, url, **kwargs):
        try:
            response = self.session.post(url, **kwargs)
            return response.json()
        except Exception, e:
            # Script.log(e, lvl=Script.INFO)
            self._handleError(e, url, **kwargs)

    def _handleError(self, e, url, **kwargs):
        if e.__class__.__name__ == "ValueError":
            Script.log("Can not parse response of request url %s" %
                       url, lvl=Script.INFO)
            Script.notify("Internal Error", "")
        elif e.__class__.__name__ == "HTTPError":
            if e.code == 402:
                Script.notify("Subscription Error",
                              "You don't have valid subscription to watch this content")
            elif e.code == 401:
                status = self._refreshToken()
                if(status is True):
                    return self.get(url, **kwargs)
                else:
                    Script.notify("Token Error", str(status))

            elif e.code == 474 or e.code == 475:
                Script.notify(
                    "VPN Error", "Your VPN provider does not support Hotstar")
            else:
                raise urlquick.HTTPError(e.filename, e.code, e.msg, e.hdrs)
        else:
            Script.log("Got unexpected response for request url %s" %
                       url, lvl=Script.INFO)
            Script.notify(
                "API Error", "Raise issue if you are continuously facing this error")

    def _refreshToken(self):
        try:
            with PersistentDict("userdata.pickle") as db:
                oldToken = db.get("token")
                if oldToken:
                    resp = self.session.get(url_constructor("/in/aadhar/v2/firetv/in/users/refresh-token"),
                                            headers={"userIdentity": oldToken, "deviceId": db.get("deviceId")}, raise_for_status=False).json()
                    if resp.get("errorCode"):
                        return resp.get("message")
                    new_token = deep_get(resp, "description.userIdentity")
                    db['token'] = new_token
                    ADDON.setSettingString(id='token',value=new_token)
                    return True
                return "Token not found"
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
            Script.log("hdnea=%s" % hdnea, lvl=Script.INFO)
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
            deviceId = db.get("deviceId")
        return {
            "os-name": "firetv",
            "desired-config": "audio_channel:stereo|encryption:%s|ladder:tv|package:dash|%svideo_codec:h264" % (encryption, subTag or ""),
            "device-id": str(deviceId),
            "os-version": "8.1.0"
        }

    @staticmethod
    def _findPlayback(playBackSets, encryption="widevine"):
        for each in playBackSets:
            if re.search("encryption:%s.*?ladder:tv.*?package:dash" % encryption, each.get("tagsCombination")):
                Script.log("Found Stream! URL : %s LicenceURL: %s" %
                           (each.get("playbackUrl"), each.get("licenceUrl")), lvl=Script.INFO)
                return (each.get("playbackUrl"), each.get("licenceUrl"), "mpd")
        playbackUrl = playBackSets[0].get("playbackUrl")
        Script.log("No stream found for desired config. Using %s" %
                   playbackUrl, lvl=Script.INFO)
        return (playbackUrl, None, "hls" if "master.m3u8" in playbackUrl else "mpd")
