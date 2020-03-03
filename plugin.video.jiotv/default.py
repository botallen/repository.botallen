import sys
import os
from urllib import urlencode
import json
import hmac
import time
import hashlib
import base64
import re
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import requests
from urlparse import parse_qsl

# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])
__addon__ = xbmcaddon.Addon()
__profile__ = xbmc.translatePath(
    __addon__.getAddonInfo('profile')).decode("utf-8")
if not os.path.exists(__profile__):
    os.mkdir(__profile__)

_CATEGORY_MAP = {
    8: "Sports",
    16: "Business News",
    15: "Devotional",
    17: "Educational",
    5: "Entertainment",
    10: "Infotainment",
    7: "Kids",
    9: "Lifestyle",
    19: "Jio Darshan",
    6: "Movies",
    13: "Music",
    12: "News",
    18: "Shopping"
}
_STAR_CHANNELS = {160: u'sshd2livetvfp', 368: u'starvijay', 931: u'starbharat', 457: u'jalsamovies', 362: u'sshindifp', 459: u'asianetmovies', 460: u'ssselecthd1fp', 461: u'ssselecthd2fp', 367: u'starutsav', 336: u'starpravah',
                  370: u'starsuvarna', 317: u'starjalsa', 181: u'asianetplus', 758: u'maatv', 759: u'maagold', 760: u'maamovies', 443: u'asianethd', 156: u'stargold', 458: u'starsuvarnaplus', 158: u'starplushd', 159: u'sshd1livetvfp'}


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


# hot_params = {
#     "client": "android",
#     "clientVersion": "8.2.4",
#     "desiredConfig": "dvr:short;encryption:plain;ladder:phone;package:hls",
#     "deviceId": "63BFE79015312541F0C7C94CADDC30D662713BCA",
#     "osName": "android",
#     "osVersion": "8.0.0"
# }
# _auth = _hotstarauth_key()
# _GET_HEADERS = {
#     "Origin": "https://ca.hotstar.com",
#     "hotstarauth": _auth,
#     "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.80 Safari/537.36",
#     "x-country-code": "IN",
#     "x-client-code": "LR",
#     "x-platform-code": "PCTV",
#     "Accept": "*/*",
#     "Referer": "https://ca.hotstar.com/",
#     "Accept-Encoding": "gzip, deflate, br",
#     "Accept-Language": "en-US,en;q=0.9",
#     "x-dst-drm": "DASH/WIDEVINE",
# }


def login(username, password):
    resp = requests.post(
        "https://api.jio.com/v3/dip/user/unpw/verify", headers={"x-api-key": "l7xx938b6684ee9e4bbe8831a9a682b8e19f"}, json={"identifier": "+91"+username, "password": password, "rememberUser": "T", "upgradeAuth": "Y", "returnSessionDetails": "T", "deviceInfo": {"consumptionDeviceName": "Jio", "info": {"type": "android", "platform": {"name": "vbox86p", "version": "8.0.0"}, "androidId": "6fcadeb7b4b10d77"}}})
    if resp.status_code == 200 and resp.json()['ssoToken']:
        data = resp.json()
        _CREDS = urlencode({"ssotoken": data['ssoToken'], "userId": data['sessionAttributes']['user']['uid'],
                            "uniqueId": data['sessionAttributes']['user']['unique'], "crmid": data['sessionAttributes']['user']['subscriberId']})
        with open(xbmc.translatePath('special://home/addons/plugin.video.jiotv/resources/raw.json'), 'r') as f:
            raw = json.load(f)
        with open(__profile__ + 'raw.json', 'w+') as f:
            for i, itm in raw.items():
                for q, url in itm.items():
                    raw[i][q] = url+'&'+_CREDS
            json.dump(raw, f, indent=2)
        main()
    else:
        xbmcgui.Dialog().notification('Login Failed', 'Invalid credentials',
                                      __addon__.getAddonInfo('icon'), 5000, True)


def getChannelUrl(channel_id):
    quality = __addon__.getSetting('quality').strip().decode('utf-8').lower()
    try:
        with open(__profile__ + 'raw.json', 'r') as f:
            raw = json.load(f)
    except:
        return False
    url = raw[channel_id][quality]
    token_params = _hotstarauth_key() if 'hotstar' in url else getTokenParams()
    return url.format(token_params)


def getCatchupUrl(channel_id, epoch):
    try:
        showtime = time.strftime('%H%M%S', time.localtime(epoch))
        srno = time.strftime('%Y%m%d', time.localtime(epoch))
        resp = requests.post(
            'http://tv.media.jio.com/apis/v1.4/getchannelurl/getchannelurl', json={"channel_id": channel_id, "showtime": showtime, "srno": srno, "stream_type": "Catchup"})
        quality = __addon__.getSetting(
            'quality').strip().decode('utf-8').lower()
        catchup_url = resp.json()['bitrates'][quality]
        listitem = xbmcgui.ListItem()
        xbmcplugin.addDirectoryItem(_handle, catchup_url, listitem)
        xbmcplugin.endOfDirectory(_handle, cacheToDisc=False)
    except:
        pass


def getTokenParams():
        # from https://github.com/allscriptz/jiotv/blob/master/jioToken.php
    def magic(x): return base64.b64encode(hashlib.md5(x.encode()).digest()).decode().replace(
        '=', '').replace('+', '-').replace('/', '_').replace('\r', '').replace('\n', '')
    # st = magic("AQIC5wM2LY4SfczEZE2fGevb0t17TAm-G9kAMvxhtxL4oGU.*AAJTSQACMDIAAlNLABQtMTkwNjA5MTA1OTI5NDc0NTI1MgACUzEAAjQ4*")
    pxe = str(int(time.time()+6000))
    jct = magic("cutibeau2ic9p-O_v1qIyd6E-rf8_gEOQ"+pxe)
    return "jct={}&pxe={}&st=9p-O_v1qIyd6E-rf8_gEOQ".format(jct, pxe)


def play(channel_id):

    play_item = xbmcgui.ListItem()
    url = getChannelUrl(channel_id)
    if not url:
        return
    play_item.setPath(url)
    play_item.setProperty('inputstreamaddon', 'inputstream.adaptive')
    play_item.setProperty('inputstream.adaptive.manifest_type', 'hls')
    play_item.setProperty(
        'inputstream.adaptive.stream_headers', url.split('|')[1])
    # if channel_id in [362, 160, 159, 461, 460]:
    #     xmap = {362: 1260000025, 160: 1260000033,
    #             159: 1260000035, 461: 1260000024, 460: 1260000034}
    #     resp = requests.get('https://api.hotstar.com/h/v2/play/in/contents/' +
    #                         str(xmap[channel_id]), headers=_GET_HEADERS, params=hot_params).json()
    #     licenceUrl = resp['body']['results']['playBackSets'][2]['licenceUrl']
    #     xbmc.log(licenceUrl, xbmc.LOGNOTICE)
    #     play_item.setProperty(
    #         'inputstream.adaptive.license_type', 'com.widevine.alpha')
    #     play_item.setProperty(
    #         'inputstream.adaptive.license_key', licenceUrl+'|'+url.split('|')[1] + '|R{SSM}|')
    # else:
    #     play_item.setProperty(
    #         'inputstream.adaptive.license_key', get_license_url())
    play_item.setProperty(
        'inputstream.adaptive.license_key', url.split('?')[1])
    play_item.setProperty(
        'inputstream.adaptive.media_renewal_url', _url + '?channelId=' + channel_id)
    play_item.setMimeType('application/vnd.apple.mpegurl')
    play_item.setContentLookup(False)

    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)


def list_channels():
    global _CATEGORY_MAP
    raw = requests.get(
        'http://jiotv.data.cdn.jio.com/apis/v1.4/getMobileChannelList/get/?os=android&devicetype=phone')
    if raw.status_code == 200:
        result = raw.json()['result']
    xbmcplugin.setPluginCategory(_handle, 'Channels')
    # xbmcplugin.setContent(_handle, 'videos')
    for each in result:
        if 'channelIdForRedirect' in each:
            _STAR_CHANNELS[each['channel_id']] = each['channelIdForRedirect']
        list_item = xbmcgui.ListItem(label=each['channel_name'])
        img_url = "http://jiotv.catchup.cdn.jio.com/dare_images/images/" + \
            each['logoUrl']
        list_item.setArt({
            'thumb': img_url,
            'icon': img_url,
            'fanart': img_url
        })
        list_item.setInfo('video', {
            'title': each['channel_name'],
            'genre': _CATEGORY_MAP[each['channelCategoryId']],
            'plot': '',
            'mediatype': 'video'
        })
        list_item.setProperty('IsPlayable', 'true')
        xbmcplugin.addDirectoryItem(
            _handle, _url + '?channelId={}'.format(each['channel_id']), list_item, False)
    xbmcplugin.endOfDirectory(_handle)


def main():
    list_channels()


def check_login():
    username = __addon__.getSetting('username').strip().decode('utf-8')
    password = __addon__.getSetting('password').strip().decode('utf-8')

    if os.path.isfile(__profile__ + 'raw.json'):
        return True
    elif username and password and not os.path.isfile(__profile__ + 'raw.json'):
        login(username, password)
        return True
    else:
        xbmcgui.Dialog().notification('Login Error', 'You need to login with Jio Username and password to use this plugin',
                                      __addon__.getAddonInfo('icon'), 5000, True)
        __addon__.openSettings()
        return False


def pvrsetup():
    IDdoADDON = 'pvr.iptvsimple'
    pathTOaddon = os.path.join(xbmc.translatePath(
        'special://home/addons'), IDdoADDON)
    pathTOaddon2 = os.path.join(xbmc.translatePath(
        'special://xbmc/addons'), IDdoADDON)
    if not os.path.exists(pathTOaddon) or not os.path.exists(pathTOaddon2):
        xbmc.executebuiltin('InstallAddon(%s)' % (IDdoADDON))
        xbmc.executebuiltin('SendClick(11)'), time.sleep(2), xbmcgui.Dialog().ok(
            "Add-on Install", "The addon was not present. Please wait for installation to finish and try again.")
    else:
        xbmcaddon.Addon(IDdoADDON).setSetting(
            'm3uPath', os.path.join(xbmc.translatePath('special://home/addons/plugin.video.jiotv/resources').decode('utf-8'), 'jiotv.m3u'))
        xbmcaddon.Addon(IDdoADDON).setSetting(
            'epgUrl', "https://kodi.botallen.com/tv/epg.xml")
        xbmcaddon.Addon(IDdoADDON).setSetting(
            'epgPathType', '1')
        xbmcaddon.Addon(IDdoADDON).setSetting(
            'm3uPathType', '0')


if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring

    params = dict(parse_qsl(sys.argv[2][1:]))
    if 'channelId' in params and check_login():
        play(params['channelId'])
    elif 'action' in params and params['action'] == 'logout':
        os.path.isfile(
            __profile__ + 'raw.json') and os.remove(__profile__ + 'raw.json')
        __addon__.setSetting('username', '')
        __addon__.setSetting('password', '')
    elif 'action' in params and params['action'] == 'catchup':
        getCatchupUrl(params['channel_id'], params['epoch'])
    elif 'action' in params and params['action'] == 'pvrsetup':
        pvrsetup()
    elif check_login():
        main()
