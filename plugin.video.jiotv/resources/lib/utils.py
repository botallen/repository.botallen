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
try:
    with open(ADDONDATA + 'channels.json', 'r') as f:
        raw = json.load(f)
except:
    pass

_STAR_CHANNELS = {160: u'sshd2livetvfp', 368: u'starvijay', 931: u'starbharat', 457: u'jalsamovies', 362: u'sshindifp', 459: u'asianetmovies', 460: u'ssselecthd1fp', 461: u'ssselecthd2fp', 367: u'starutsav', 336: u'starpravah',
                  370: u'starsuvarna', 317: u'starjalsa', 181: u'asianetplus', 758: u'maatv', 759: u'maagold', 760: u'maamovies', 443: u'asianethd', 156: u'stargold', 458: u'starsuvarnaplus', 158: u'starplushd', 159: u'sshd1livetvfp'}


def check_login():
    username = kodiutils.get_setting('username')
    password = kodiutils.get_setting('password')

    if os.path.isfile(ADDONDATA + 'channels.json'):
        return True
    elif username and password and not os.path.isfile(ADDONDATA + 'channels.json'):
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
        _CREDS = urlencode({"ssotoken": data['ssoToken'], "userId": data['sessionAttributes']['user']['uid'],
                            "uniqueId": data['sessionAttributes']['user']['unique'], "crmid": data['sessionAttributes']['user']['subscriberId']})
        with open(xbmc.translatePath('special://home/addons/plugin.video.jiotv/resources/extra/channels.json'), 'r') as f:
            raw = json.load(f)
        with open(ADDONDATA + 'channels.json', 'w+') as f:
            for cid, itm in raw.items():
                if int(cid) in _STAR_CHANNELS.keys():
                    raw[cid]['url'] = itm['url'] + \
                        "?hdnea={token}|User-Agent=Hotstar%3Bin.startv.hotstar%2F8.2.4+%28Linux%3BAndroid+8.0.0%29+ExoPlayerLib%2F2.9.5&"+_CREDS
                else:
                    raw[cid]['url'] = itm['url']+"?{token}|appkey=NzNiMDhlYzQyNjJm&lbcookie=1&devicetype=phone&deviceId=6fcadeb7b4b10d77&srno=200206173037&usergroup=tvYR7NSNn7rymo3F&versionCode=226&channelid=100&os=android&User-Agent=plaYtv%2F5.4.0+%28Linux%3BAndroid+8.0.0%29+ExoPlayerLib%2F2.3.0&"+_CREDS
            json.dump(raw, f, indent=2)
    else:
        kodiutils.notification('Login Failed', 'Invalid credentials')


def getChannelUrl(channel_id):
    global raw
    qmap = {'auto': '', 'low': '_LOW', 'medium': '_MED', 'high': '_HIG'}
    quality = kodiutils.get_setting('quality').lower()
    url = raw[str(channel_id)]['url']
    token_params = _hotstarauth_key() if 'hotstar' in url else getTokenParams()
    return url.format(token=token_params, q=qmap[quality])


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


def getTokenParams():
        # from https://github.com/allscriptz/jiotv/blob/master/jioToken.php
    def magic(x): return base64.b64encode(hashlib.md5(x.encode()).digest()).decode().replace(
        '=', '').replace('+', '-').replace('/', '_').replace('\r', '').replace('\n', '')
    # st = magic("AQIC5wM2LY4SfczEZE2fGevb0t17TAm-G9kAMvxhtxL4oGU.*AAJTSQACMDIAAlNLABQtMTkwNjA5MTA1OTI5NDc0NTI1MgACUzEAAjQ4*")
    pxe = str(int(time.time()+6000))
    jct = magic("cutibeau2ic9p-O_v1qIyd6E-rf8_gEOQ"+pxe)
    return "jct={}&pxe={}&st=9p-O_v1qIyd6E-rf8_gEOQ".format(jct, pxe)
