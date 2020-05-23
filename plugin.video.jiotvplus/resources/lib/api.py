# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import urlquick
from functools import reduce
from .contants import BASE_HEADERS, url_constructor, CHANNELS_SRC, PLAY_URL, CHANNELS_FILTER
from .utils import check_addon
from codequick import Script
from codequick.script import Settings
from codequick.storage import PersistentDict
from xbmcgui import Dialog
import time
import hashlib
import hmac
from uuid import uuid4
from base64 import b64encode

# urlquick.cache_cleanup(-1)


def deep_get(dictionary, keys, default=None):
    return reduce(lambda d, key: d.get(key, default) if isinstance(d, dict) else default, keys.split("."), dictionary)


class JioAPI:

    def __init__(self):
        self.session = urlquick.Session()
        self.session.headers.update(BASE_HEADERS)

    def getPage(self, url):
        results = self.get(url)
        nextPageUrl = results.get("totalPages") and results.get(
            "totalPages") - 1 > int(url[-1:]) and url[:-1] + str(int(url[-1:])+1)
        return results.get("data"), nextPageUrl

    def getTray(self, url, search_query=None, post_json=None, isCarousal=False):
        if search_query:
            url = url_constructor(
                "/apis/2ccce09e59153fc9/v1/plus-search/search")
            results = self.post(url, json={"q": search_query})
            results['data']['items'] = [x for y in deep_get(
                results, "data.items") for x in y.get("items")]
        elif post_json:
            results = self.post(url, json=post_json)
        else:
            results = self.get(url)
            if isCarousal:
                results["data"] = list(
                    filter(lambda x: x.get("isCarousal"), results.get("data")))[0]
                del results["totalPages"]
        xitems = []
        if deep_get(results, "data.items"):
            items = deep_get(results, "data.items")
            for each in items:
                if deep_get(each, "app.type") == 16 or deep_get(each, "app.type") == 19 or deep_get(each, "app.type") == 10:
                    xitems.append(each)
                else:
                    xitems.append(self.get(url_constructor(
                        "/apis/2ccce09e59153fc9/v1/plus-metamore/get/%s" % each.get("id"))))
            nextPageUrl = results.get("totalPages") and results.get(
                "totalPages") > int(url[-1:]) and url[:-1] + str(int(url[-1:])+1)
        elif results.get("episodes"):
            xitems = results.get("episodes")
            nextPageUrl = None
        elif results.get("filter"):
            for i in results.get("filter"):
                if i.get("filter") == "":
                    xitems.append(self.get(url_constructor(
                        "/apis/2ccce09e59153fc9/v1/plus-metamore/get/%s/%s" % (results.get("id"), i.get("season")))))
                else:
                    for x in i.get("month"):
                        xitems.append(self.get(url_constructor(
                            "/apis/2ccce09e59153fc9/v1/plus-metamore/get/%s/%s/%s" % (results.get("id"), i.get("filter"), x))))

            nextPageUrl = None
        else:
            xitems, nextPageUrl = None, None
        return xitems, nextPageUrl

    def getPlay(self, Id, vendor, extId=None):
        url = url_constructor("/apis/common/v3/playbackrights/get/%s" % Id)
        headers, body = self._getPlayHeaders()
        resp = self.post(url, headers=headers, json=body, max_age=-1)
        Script.log("Got vender in api %s " % vendor, lvl=Script.INFO)
        if vendor is None:
            vendor = resp.get("vendorName")
            Script.log("Vendor is not provided. Choosing %s " %
                       vendor, lvl=Script.INFO)
        if vendor == "hotstar":
            if not extId:
                return None
            playUri = "https://api.hotstar.com/ph/v1/play?partnerId=7354739821&contentId=%s" % extId
            playbackUrl = self.session.get(
                playUri, headers={"x-country-code": "in", "x-platform-code": "tv"}, raise_for_status=False).json()
            playbackUrl = deep_get(playbackUrl, "body.results.playbackUrl")
            if not playbackUrl:
                if check_addon("plugin.video.botallen.hotstar", "0.0.25"):
                    return {"ext": "plugin://plugin.video.botallen.hotstar/resources/lib/main/play_ext/?_pickle_=", "contentId": extId}
                return None
            headers = {"hotstarauth": playbackUrl.split(
                "hdnea=")[-1], "User-Agent": "Hotstar;in.startv.hotstar/3.3.0 (Android/8.1.0)"}
            return {"playbackUrl": playbackUrl, "playbackProto": "hls", "headers": headers, "vendor": vendor}
        elif vendor == "Sony Pictures":
            if not extId:
                return None
            eUrl = "https://edge.api.brightcove.com/playback/v1/accounts/5182475815001/videos/ref:%s" % extId
            playbackUrl = self.get(eUrl, headers={
                                   "Accept": "application/json;pk=BCpkADawqM1cdm3Q1gfyCfaUavRbZmnJodHnuATjiP0ZEM_lVFZvx_WB2kGrjEWHc88nkelmJNtyAj2W403bibBfWo1svy3mYn--aoo_R2nb58T_7-H40Rr55InbrYnFhtVb_Gd7gKQsYEwF"})
            nonDRMplaybackUrl = list(filter(lambda x: (x.get(
                "ext_x_version") == "4" and x.get("type") == "application/x-mpegURL") or (x.get("type") == "application/vnd.apple.mpegurl"), playbackUrl.get("sources", [])))
            if nonDRMplaybackUrl:
                return {"playbackUrl": nonDRMplaybackUrl[0].get("src"), "playbackProto": "hls", "vendor": vendor}
            DRMPlaybackUrl = list(filter(lambda x: x.get(
                "type") == "application/dash+xml", playbackUrl.get("sources", [])))
            Script.log("licenceUrl %s " % deep_get(
                DRMPlaybackUrl[0], "key_systems.com.widevine.alpha"))
            return {"playbackUrl": DRMPlaybackUrl[0].get("src"), "licenseUrl": deep_get(DRMPlaybackUrl[0], "key_systems.com.widevine.alpha"), "playbackProto": "mpd", "vendor": vendor}
        playbackUrl = resp.get("high")
        licenseUrl = "http://vodwvproxy.media.jio.com/proxy?video_id=%s||R{SSM}|" % resp.get(
            "videoId")
        if playbackUrl is None:
            return None
        # playbackUrl = playbackUrl.replace("WEBDESKTOP_L", "TV_A") + ("&jct=%s&pxe=%s&st=%s" % (
        #     resp.get("jct"), resp.get("pxe"), resp.get("st") or resp.get("kid")))
        subtitles = resp.get("srt", []) and ["https://jiovod.cdn.jio.com/vod/_definst_/smil:vod/" +
                                             resp.get("srt")]
        return {
            "playbackUrl": playbackUrl,
            "licenseUrl": licenseUrl,
            "playbackProto": "mpd",
            "headers": headers,
            "vendor": vendor,
            "subtitles": subtitles
        }

    def doLogin(self):
        try:
            username = Settings.get_string("username", "plugin.video.jiotv") or Dialog().input(
                "Username (MobileNo / Email)")
            password = Settings.get_string(
                "password", "plugin.video.jiotv") or Dialog().input("Password")
        except RuntimeError:
            username = Dialog().input("Username (MobileNo / Email)")
            password = Dialog().input("Password")
        if username and password:
            body = {"identifier": username if '@' in username else "+91"+username, "password": password, "rememberUser": "T", "upgradeAuth": "Y", "returnSessionDetails": "T",
                    "deviceInfo": {"consumptionDeviceName": "Jio", "info": {"type": "android", "platform": {"name": "vbox86p", "version": "8.0.0"}, "androidId": "6fcadeb7b4b10d77"}}}
            resp = urlquick.post("https://api.jio.com/v3/dip/user/unpw/verify", json=body,
                                 headers={"x-api-key": "l7xx75e822925f184370b2e25170c5d5820a"}, verify=False, raise_for_status=False).json()
            if resp.get("ssoToken"):
                with PersistentDict("userdata.pickle") as db:
                    db["data"] = resp
                Script.notify("Login Successful",
                              "You have been logged in successfully")
            else:
                Script.notify(
                    "Login Failed", "Double check you username and password and try again")
        else:
            Script.notify("Login Required",
                          "Please login with you Jio credentials")

    def doLogout(self):
        with PersistentDict("userdata.pickle") as db:
            db.clear()
        Script.notify("Logout Success", "You are logged out")

    def get(self, url, **kwargs):
        try:
            response = self.session.get(url, **kwargs)
            return response.json()
        except Exception, e:
            Script.log(e, lvl=Script.INFO)
            self._handleError(e, url, **kwargs)

    def post(self, url, **kwargs):
        try:
            response = self.session.post(url, **kwargs)
            return response.json()
        except Exception, e:
            Script.log(e, lvl=Script.INFO)
            self._handleError(e, url, **kwargs)

    def _handleError(self, e, url, **kwargs):
        if e.__class__.__name__ == "ValueError":
            Script.log("Can not parse response of request url %s" %
                       url, lvl=Script.INFO)
            Script.notify("Internal Error", "")
        elif e.__class__.__name__ == "HTTPError":
            raise urlquick.HTTPError(e.filename, e.code, e.msg, e.hdrs)
        else:
            Script.log("Got unexpected response for request url %s" %
                       url, lvl=Script.INFO)
            Script.notify(
                "API Error", "Raise issue if you are continuously facing this error")

    @staticmethod
    def getTokenParams(delay=0):
        def magic(x): return b64encode(hashlib.md5(x.encode()).digest()).decode().replace(
            '=', '').replace('+', '-').replace('/', '_').replace('\r', '').replace('\n', '')
        pxe = str(int(time.time() + delay))
        jct = magic("cutibeau2icPoK6FNfXcwN50nI2RvulmA"+pxe)
        return "jct=%s&pxe=%s&st=PoK6FNfXcwN50nI2RvulmA" % (jct, pxe)
        # return {"jct": jct, "pxe": pxe, "st": "PoK6FNfXcwN50nI2RvulmA"}

        # backup
        # url = url_constructor("/apis/common/v3/playbackrights/get/0_kwl7ha1e")
        # headers, body = JioAPI._getPlayHeaders()
        # resp = urlquick.post(url, headers=headers,
        #                      json=body, max_age=-1).json()
        # return "jct=%s&pxe=%s&st=%s" % (resp.get("jct"), resp.get("pxe"), resp.get("st"))

    @staticmethod
    def getStarAuth(includeST=False):
        _AKAMAI_ENCRYPTION_KEY = b'\x05\xfc\x1a\x01\xca\xc9\x4b\xc4\x12\xfc\x53\x12\x07\x75\xf9\xee'
        st = int(time.time())
        exp = st + 6000
        auth = 'st=%d~exp=%d~acl=/*' % (
            st, exp) if includeST else 'exp=%d~acl=/*' % exp
        auth += '~hmac=' + hmac.new(_AKAMAI_ENCRYPTION_KEY,
                                    auth.encode(), hashlib.sha256).hexdigest()
        return auth

    @staticmethod
    def _getPlayHeaders():
        with PersistentDict("userdata.pickle") as db:
            data = db.get("data")
        Script.log(str(data), lvl=Script.INFO)
        return {
            "ssotoken": data.get("ssoToken"),
            "x-multilang": "true",
            "appkey": "2ccce09e59153fc9",
            "x-apisignatures": "543aba07839",
            "devicetype": "tv",
            "os": "Android",
            "User-Agent": "Jiotv+ Kodi",
            "AppName": "Jiotv+",
            "deviceId": str(uuid4()),
            "ua": "JioCinemaAndroidOS",
            "subid": deep_get(data, "sessionAttributes.user.subscriberId"),
            "lbcookie": "1",
            "AppVersion": "62"
        }, {"uniqueId": deep_get(data, "sessionAttributes.user.unique"), "bitrateProfile": "xxhdpi"}

    @staticmethod
    def _getLiveHeaders():
        with PersistentDict("userdata.pickle") as db:
            data = db.get("data")
        return {
            "appkey": "2ccce09e59153fc9",
            "uniqueId": deep_get(data, "sessionAttributes.user.unique"),
            "srno": "200414205625",
            "channelid": "100",
            "userId": deep_get(data, "sessionAttributes.user.uid"),
            "User-Agent": "Jiotv+ Kodi",
            "versionCode": "226",
            "ssotoken": data.get("ssoToken"),
            "devicetype": "Kodi",
            "deviceId": str(uuid4()),
            "crmid": deep_get(data, "sessionAttributes.user.subscriberId"),
            "usergroup": "tvYR7NSNn7rymo3F",
            "lbcookie": "1",
            "os": "Kodi"
        }

    @staticmethod
    def getLiveUrl(Id):
        resp = urlquick.get(CHANNELS_SRC).json()
        if Id in CHANNELS_FILTER:
            Id = CHANNELS_FILTER[Id]
        l = [x for x in resp if x.get("id") == int(Id)]
        return len(l) > 0 and PLAY_URL + l[0].get("data")
