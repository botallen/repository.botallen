from functools import wraps
from codequick import Script
from xbmc import executebuiltin
import urlquick
import hmac
import re
import time
import hashlib
from os import path
from codequick.storage import PersistentDict


def isLoggedIn(func):
    """
    Decorator to ensure that a valid login is present when calling a method
    """
    @wraps(func)
    def login_wrapper(*args, **kwargs):
        with PersistentDict("userdata.pickle") as db:
            token = db.get("token")
        if token:
            return func(*args, **kwargs)
        else:
            # login require
            Script.notify("Login Error", "Please login to use this add-on")
            executebuiltin(
                "RunPlugin(plugin://plugin.video.botallen.hotstar/resources/lib/main/login/)")
            return False
    return login_wrapper


def refreshToken():
    with PersistentDict("userdata.pickle") as db:
        token = db.get("token")
        if token:
            new_token = urlquick.get(
                "https://api.hotstar.com/in/aadhar/v2/firetv/in/users/refresh-token", headers={"userIdentity": token, "deviceId": db.get("deviceId")}).json().get("description").get("userIdentity")
        db['token'] = new_token


def getAuth(includeST=False):
    _AKAMAI_ENCRYPTION_KEY = b'\x05\xfc\x1a\x01\xca\xc9\x4b\xc4\x12\xfc\x53\x12\x07\x75\xf9\xee'
    st = int(time.time())
    exp = st + 6000
    auth = 'st=%d~exp=%d~acl=/*' % (st,
                                    exp) if includeST else 'exp=%d~acl=*' % exp
    auth += '~hmac=' + \
        hmac.new(_AKAMAI_ENCRYPTION_KEY,
                 auth.encode(), hashlib.sha256).hexdigest()
    return auth


def getPlayHeaders(includeST=False):
    with PersistentDict("userdata.pickle") as db:
        token = db.get("token")
    return {
        "hotstarauth": getAuth(includeST),
        "X-Country-Code": "in",
        "X-HS-AppVersion": "3.3.0",
        "X-HS-Platform": "firetv",
        "X-HS-UserToken": token,
        "User-Agent": "Hotstar;in.startv.hotstar/3.3.0 (Android/8.1.0)"
    }


def getPlayParams(subTag="", encryption="widevine"):
    with PersistentDict("userdata.pickle") as db:
        deviceId = db.get("deviceId")
    return {
        "os-name": "firetv",
        "desired-config": "audio_channel:stereo|encryption:%s|ladder:tv|package:dash|%svideo_codec:h264" % (encryption, subTag or ""),
        "device-id": str(deviceId),
        "os-version": "8.1.0"
    }


def findPlayback(playBackSets, encryption="widevine"):
    for each in playBackSets:
        if re.search("encryption:%s.*?ladder:tv.*?package:dash" % encryption, each.get("tagsCombination")):
            return (each.get("playbackUrl"), each.get("licenceUrl"))
    return (None, None)
