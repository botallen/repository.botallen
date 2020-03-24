import os
import kodiutils
import requests
import hmac
import time
import hashlib
import base64
import re
from urllib import urlencode
import json
import xbmc
import xbmcaddon

ADDON = xbmcaddon.Addon()
ADDONDATA = xbmc.translatePath(ADDON.getAddonInfo('profile')).decode("utf-8")


def check_login():
    username = kodiutils.get_setting('username')
    password = kodiutils.get_setting('password')

    if os.path.isfile(ADDONDATA + 'headers.json'):
        return True
    elif username and password and not os.path.isfile(ADDONDATA + 'headers.json'):
        login(username, password)
        return True
    else:
        kodiutils.notification(
            'Login Error', 'You need to login with Jio Username and password to use this plugin')
        kodiutils.show_settings()
        return False


def login(username, password):
    resp = requests.post(
        "https://api.jio.com/v3/dip/user/unpw/verify", headers={"x-api-key": "l7xx938b6684ee9e4bbe8831a9a682b8e19f"}, json={"identifier": username if '@' in username else "+91"+username, "password": password, "rememberUser": "T", "upgradeAuth": "Y", "returnSessionDetails": "T", "deviceInfo": {"consumptionDeviceName": "Jio", "info": {"type": "android", "platform": {"name": "vbox86p", "version": "8.0.0"}, "androidId": "6fcadeb7b4b10d77"}}})
    if resp.status_code == 200 and resp.json()['ssoToken']:
        data = resp.json()
        _CREDS = {"ssotoken": data['ssoToken'], "userId": data['sessionAttributes']['user']['uid'],
                  "uniqueId": data['sessionAttributes']['user']['unique'], "crmid": data['sessionAttributes']['user']['subscriberId']}
        headers = {
            "User-Agent": "JioTV Kodi",
            "os": "Kodi",
            "deviceId": "6fcadeb7b4b10d77",
            "versionCode": "226",
            "devicetype": "Kodi",
            "srno": "200206173037",
            "appkey": "NzNiMDhlYzQyNjJm",
            "channelid": "100",
            "usergroup": "tvYR7NSNn7rymo3F",
            "lbcookie": "1"
        }
        headers.update(_CREDS)
        with open(ADDONDATA + 'headers.json', 'w+') as f:
            json.dump(headers, f, indent=4)
    else:
        kodiutils.notification('Login Failed', 'Invalid credentials')


def _hotstarauth_key():
    def keygen(t):
        e = ""
        n = 0
        while len(t) > n:
            r = t[n] + t[n + 1]
            o = int(re.sub(r"[^a-f0-9]", "", r + "", re.IGNORECASE), 16)
            e += chr(o)
            n += 2

        return e

    start = int(time.time())
    expiry = start + 6000
    message = "st={}~exp={}~acl=/*".format(start, expiry)
    secret = keygen("05fc1a01cac94bc412fc53120775f9ee")
    signature = hmac.new(secret, message, digestmod=hashlib.sha256).hexdigest()
    return '{}~hmac={}'.format(message, signature)

def getHeaders():
    if os.path.isfile(ADDONDATA + 'headers.json'):
        with open(ADDONDATA + 'headers.json', 'r') as f:
            headers = json.load(f)
        return headers
    return False