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
_CREDS = None
_RAW_RESULT = None
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


hot_params = {
    "client": "android",
    "clientVersion": "8.2.4",
    "desiredConfig": "dvr:short;encryption:plain;ladder:phone;package:hls",
    "deviceId": "63BFE79015312541F0C7C94CADDC30D662713BCA",
    "osName": "android",
    "osVersion": "8.0.0"
}
_auth = _hotstarauth_key()
_GET_HEADERS = {
    "Origin": "https://ca.hotstar.com",
    "hotstarauth": _auth,
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.80 Safari/537.36",
    "x-country-code": "IN",
    "x-client-code": "LR",
    "x-platform-code": "PCTV",
    "Accept": "*/*",
    "Referer": "https://ca.hotstar.com/",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
    "x-dst-drm": "DASH/WIDEVINE",
}


def genXML():
    global _RAW_RESULT, _CATEGORY_MAP

    if os.path.exists(__profile__ + '../../../addons/pvr.demo'):
        path = __profile__ + '../../../addons/pvr.demo/PVRDemoAddonSettings.xml'
    elif os.path.exists('/usr/share/kodi/addons/pvr.demo'):
        path = '/usr/share/kodi/addons/pvr.demo/PVRDemoAddonSettings.xml'
    else:
        return
    channels, channelgroups, epgStr = "", "", ""
    category = {}

    # def getEPGIcon(eachEGP):
    #     try:
    #         return "http://jiotv.catchup.cdn.jio.com/dare_images/shows/{}".format(eachEGP['episodeThumbnail'].encode('utf-8').strip())
    #     except:
    #         return ""

    if _RAW_RESULT:
        for each in _RAW_RESULT:
            channels += "\n\t\t<channel>\n\t\t\t<name>{name}</name>\n\t\t\t<radio>0</radio>\n\t\t\t<number>{order}</number>\n\t\t\t<encryption>0</encryption>\n\t\t\t<icon>http://jiotv.catchup.cdn.jio.com/dare_images/images/{icon}</icon>\n\t\t\t<stream>plugin://plugin.video.jiotv/?channelId={id}</stream>\n\t\t</channel>".format(
                name=each['channel_name'].encode('utf-8').strip(), order=str(int(each['channel_order'])+1), icon=each['logoUrl'].encode('utf-8').strip(), id=each['channel_id'])
            # epg = requests.get(
            #     "http://jiotv.data.cdn.jio.com/apis/v1.3/getepg/get?offset=-1&channel_id={}&langId=6".format(each['channel_id'])).json()
            # # for eachEGP in epg['epg']:
            # eachEGP = epg['epg'][0]
            # epgStr += "\n\t\t<entry>\n\t\t\t<broadcastid>{broadcastid}</broadcastid>\n\t\t\t<title>{title}</title>\n\t\t\t<channelid>{channelid}</channelid>\n\t\t\t<start>{start}</start>\n\t\t\t<end>{end}</end>\n\t\t\t<plotoutline>{shortDesc}</plotoutline>\n\t\t\t<plot>{longDesc}</plot>\n\t\t\t<episode>{episode}</episode>\n\t\t\t<episodetitle>{episodetitle}</episodetitle>\n\t\t\t<icon></icon>\n\t\t\t<genretype>1</genretype>\n\t\t\t<genresubtype>0</genresubtype>\n\t\t</entry>".format(
            #     broadcastid=str(int(each['channel_order'])+1),
            #     # broadcastid=each['channel_id']*100,
            #     title=eachEGP['showname'].encode('utf-8').strip(),
            #     channelid=eachEGP['channel_id'],
            #     start=eachEGP['startTime'],
            #     end=(eachEGP['startTime']+eachEGP['duration']),
            #     shortDesc='Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
            #     longDesc=eachEGP['description'],
            #     episode=(0, eachEGP['episode_num'])[
            #         eachEGP['episode_num'] >= 0],
            #     episodetitle='Lorem ipsum'
            # )
            if each['channelCategoryId'] in category.keys():
                # category[epg['channel_category_name']].append(each['channel_order'])
                category[each['channelCategoryId']].append(
                    int(each['channel_order'])+1)
            else:
                # category[epg['channel_category_name']] = [each['channel_order']]
                category[each['channelCategoryId']] = [
                    int(each['channel_order'])+1]

    for index, item in enumerate(category.items()):
        key, value = item
        members = "".join(
            ["\n\t\t\t\t<member>"+str(x)+"</member>" for x in value])
        channelgroups += "\n\t\t<group>\n\t\t\t<name>{name}</name>\n\t\t\t<radio>0</radio>\n\t\t\t<position>{index}</position>\n\t\t\t<members>{members}\n\t\t\t</members>\n\t\t</group>".format(
            name=_CATEGORY_MAP[key], index=index+1, members=members)

    with open(path, 'w+') as f:
        f.write("<demo>\n\t<channels>{}\n\t</channels>\n\t<channelgroups>{}\n\t</channelgroups>\n</demo>".format(
            channels, channelgroups, epgStr))


def login(username, password):
    global _CREDS
    resp = requests.post(
        "https://api.jio.com/v3/dip/user/unpw/verify", headers={"x-api-key": "l7xx938b6684ee9e4bbe8831a9a682b8e19f"}, json={"identifier": "+91"+username, "password": password, "rememberUser": "T", "upgradeAuth": "Y", "returnSessionDetails": "T", "deviceInfo": {"consumptionDeviceName": "Jio", "info": {"type": "android", "platform": {"name": "vbox86p", "version": "8.0.0"}, "androidId": "6fcadeb7b4b10d77"}}})
    if resp.status_code == 200 and resp.json()['ssoToken']:
        data = resp.json()
        _CREDS = {"ssotoken": data['ssoToken'], "userId": data['sessionAttributes']['user']['uid'],
                  "uniqueId": data['sessionAttributes']['user']['unique'], "crmid": data['sessionAttributes']['user']['subscriberId']}
        with open(__profile__+'creds.txt', 'w+') as f:
            json.dump(_CREDS, f, indent=2)
        main()
    else:
        xbmcgui.Dialog().notification('Login Failed', 'Invalid credentials',
                                      __addon__.getAddonInfo('icon'), 5000, True)


def getChannelUrl(channel_id):
    global _STAR_CHANNELS
    try:
        if int(channel_id) in _STAR_CHANNELS:
            xbmc.log('its star channel ' + channel_id, xbmc.LOGNOTICE)
            # liveClipContentId = requests.get('https://api.hotstar.com/o/v1/multi/get/content?ids=' + _STAR_CHANNELS[channel_id], headers={
            #                                  "x-country-code": "in"}).json()['body']['results']['map'][_STAR_CHANNELS[channel_id]]['liveClipContentId']
            # resp = requests.get('https://api.hotstar.com/h/v2/play/in/contents/'+liveClipContentId, headers={"hotstarauth": _hotstarauth_key(
            # )}, params={"desiredConfig": "dvr:short;encryption:plain;ladder:phone;package:hls", "client": "android"}).json()['body']['results']['playBackSets']
            return "http://hotstar.live.cdn.jio.com/hotstar_isl/{}/master.m3u8?faxs=1&hdnea={}".format(_STAR_CHANNELS[int(channel_id)], _hotstarauth_key())
        resp = requests.post(
            'http://tv.media.jio.com/apis/v1.4/getchannelurl/getchannelurl', json={"channel_id": channel_id})
        quality = __addon__.getSetting(
            'quality').strip().decode('utf-8').lower()
        return resp.json()['bitrates'][quality]
    except:
        return ""


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
    if not _CREDS:
        return
    if int(channel_id) in _STAR_CHANNELS:
        stream_headers = urlencode({
            "User-Agent": "Hotstar;in.startv.hotstar/8.2.4 (Linux;Android 8.0.0) ExoPlayerLib/2.9.5"})
        # stream_headers = "&".join(
        #     [key+"="+quote_plus(value) for key, value in stream_headers.items()])

        # xbmc.log(stream_headers, xbmc.LOGNOTICE)
    else:
        stream_headers = {
            "User-Agent": "plaYtv/5.4.0 (Linux;Android 8.0.0) ExoPlayerLib/2.3.0",
            "os": "android",
            "deviceId": "6fcadeb7b4b10d77",
            "versionCode": "226",
            "devicetype": "phone",
            "srno": "200206173037",
            "appkey": "NzNiMDhlYzQyNjJm",
            "channelid": channel_id,
            "usergroup": "tvYR7NSNn7rymo3F",
            "lbcookie": "1"
        }
        stream_headers.update(_CREDS)
        stream_headers = urlencode(stream_headers)
        # stream_headers = "&".join([key+"="+quote_plus(value)
        #                            for key, value in stream_headers.items()])
        # stream_headers += "&" + "&".join([key+"="+quote_plus(value)
        #                                   for key, value in _CREDS.items()])
        # xbmc.log(stream_headers, xbmc.LOGNOTICE)

    token_params = getTokenParams()
    play_item = xbmcgui.ListItem()
    if int(channel_id) in _STAR_CHANNELS:
        play_item.setPath(getChannelUrl(channel_id))
    else:
        play_item.setPath(getChannelUrl(channel_id)+"?"+token_params)
    play_item.setProperty('inputstreamaddon', 'inputstream.adaptive')
    play_item.setProperty('inputstream.adaptive.manifest_type', 'hls')
    play_item.setProperty(
        'inputstream.adaptive.stream_headers', stream_headers)
    if int(channel_id) in [362, 160, 159, 461, 460]:
        xmap = {362: 1260000025, 160: 1260000033,
                159: 1260000035, 461: 1260000024, 460: 1260000034}
        resp = requests.get('https://api.hotstar.com/h/v2/play/in/contents/' +
                            str(xmap[int(channel_id)]), headers=_GET_HEADERS, params=hot_params).json()
        licenceUrl = resp['body']['results']['playBackSets'][2]['licenceUrl']
        xbmc.log(licenceUrl, xbmc.LOGNOTICE)
        play_item.setProperty(
            'inputstream.adaptive.license_type', 'com.widevine.alpha')
        play_item.setProperty(
            'inputstream.adaptive.license_key', licenceUrl+'|'+stream_headers + '|R{SSM}|')
    else:
        play_item.setProperty(
            'inputstream.adaptive.license_key', get_license_url())
    play_item.setProperty(
        'inputstream.adaptive.media_renewal_url', _url + '?action=renew_token')
    play_item.setMimeType('application/vnd.apple.mpegurl')
    play_item.setContentLookup(False)

    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)


def get_license_url():
    stream_headers = {
        "User-Agent": "plaYtv/5.4.0 (Linux;Android 8.0.0) ExoPlayerLib/2.3.0",
        "os": "android",
        "deviceId": "6fcadeb7b4b10d77",
        "versionCode": "226",
        "devicetype": "phone",
        "srno": "200206173037",
        "appkey": "NzNiMDhlYzQyNjJm",
        "channelid": 1,
        "usergroup": "tvYR7NSNn7rymo3F",
        "lbcookie": "1"
    }
    stream_headers.update(_CREDS)
    token_params = getTokenParams()
    return token_params + '|' + urlencode(stream_headers)


def updateRaw():
    global _RAW_RESULT
    raw = requests.get(
        'http://jiotv.data.cdn.jio.com/apis/v1.4/getMobileChannelList/get/?os=android&devicetype=phone')
    if raw.status_code == 200:
        _RAW_RESULT = raw.json()['result']


def renew_token():
    listitem = xbmcgui.ListItem()
    xbmcplugin.addDirectoryItem(_handle, get_license_url(), listitem)
    xbmcplugin.endOfDirectory(_handle, cacheToDisc=False)


def list_channels():
    global _CATEGORY_MAP
    result = _RAW_RESULT
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
    global _CREDS
    with open(__profile__ + 'creds.txt', 'r') as f:
        _CREDS = json.load(f)
    updateRaw()
    # genXML()
    if params and params['channelId']:
        play(params['channelId'])
    else:
        list_channels()


def check_login():
    username = __addon__.getSetting('username').strip().decode('utf-8')
    password = __addon__.getSetting('password').strip().decode('utf-8')

    if os.path.isfile(__profile__ + 'creds.txt'):
        main()
    elif username and password and not os.path.isfile(__profile__ + 'creds.txt'):
        login(username, password)
    else:
        xbmcgui.Dialog().notification('Login Error', 'You need to login with Jio Username and password to use this plugin',
                                      __addon__.getAddonInfo('icon'), 5000, True)
        __addon__.openSettings()


def pvrsetup():
    IDdoADDON = 'pvr.iptvsimple'
    pathTOaddon = os.path.join(xbmc.translatePath(
        'special://home/addons'), IDdoADDON)
    if not os.path.exists(pathTOaddon) == True:
        xbmc.executebuiltin('InstallAddon(%s)' % (IDdoADDON))
        xbmc.executebuiltin('SendClick(11)'), time.sleep(2), xbmcgui.Dialog().ok(
            "Add-on Install", "The addon was not present. Please wait for installation to finish.")
    else:
        pass
    if os.path.exists(pathTOaddon) == True:
        xbmcaddon.Addon(IDdoADDON).setSetting(
            'm3uPath', xbmc.translatePath('special://home/addons/plugin.video.jiotv/resources/jiotv.m3u').decode('utf-8'))
        xbmcaddon.Addon(IDdoADDON).setSetting(
            'epgUrl', "https://kodi.botallen.com/tv/epg.xml")
        xbmcaddon.Addon(IDdoADDON).setSetting(
            'epgPathType', '1')
        xbmcaddon.Addon(IDdoADDON).setSetting(
            'm3uPathType', '0')
        xbmc.executebuiltin('RunAddon(%s)' % (IDdoADDON))
    else:
        xbmcgui.Dialog().ok("Add-on Error", "Could not install or open add-on. Please try again...")


if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring

    params = dict(parse_qsl(sys.argv[2][1:]))

    if 'action' in params and params['action'] == 'logout':
        os.path.isfile(
            __profile__ + 'creds.txt') and os.remove(__profile__ + 'creds.txt')
        __addon__.setSetting('username', '')
        __addon__.setSetting('password', '')
    elif 'action' in params and params['action'] == 'renew_token':
        renew_token()
    elif 'action' in params and params['action'] == 'catchup':
        getCatchupUrl(params['channel_id'], params['epoch'])
    elif 'action' in params and params['action'] == 'pvrsetup':
        pvrsetup()
    else:
        check_login()
