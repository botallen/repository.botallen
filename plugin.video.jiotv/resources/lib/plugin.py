# -*- coding: utf-8 -*-

import routing
import logging
import json
import requests
from xbmcaddon import Addon
from xbmc import executebuiltin, translatePath
import os
import sys
from time import sleep, time
from urllib import urlencode
from datetime import datetime, date, timedelta
from resources.lib import kodiutils
from resources.lib import kodilogging
import inputstreamhelper
from xbmcgui import ListItem, Dialog
from xbmcplugin import addDirectoryItems, endOfDirectory, setResolvedUrl
from utils import check_login, _hotstarauth_key


ADDON = Addon()
ADDONDATA = translatePath(ADDON.getAddonInfo('profile')).decode("utf-8")
if not os.path.exists(ADDONDATA):
    os.mkdir(ADDONDATA)
logger = logging.getLogger(ADDON.getAddonInfo('id'))
kodilogging.config()
plugin = routing.Plugin()


@plugin.route('/')
def index():
    with open(translatePath("special://home/addons/plugin.video.jiotv/resources/extra/categories.json"), 'r') as f:
        categories = json.load(f)
    items = []
    for each in categories.keys():
        list_item = ListItem(
            label=each + '  ({})'.format(len(categories[each])))
        icon_url = "special://home/addons/plugin.video.jiotv/resources/extra/img/{}.png".format(
            each)
        list_item.setArt({
            'thumb': icon_url,
            'icon': icon_url
        })
        items.append(
            (plugin.url_for(show_category, each), list_item, True))
    addDirectoryItems(plugin.handle, items)
    endOfDirectory(plugin.handle)


@plugin.route('/category/<category_id>')
def show_category(category_id):
    with open(translatePath("special://home/addons/plugin.video.jiotv/resources/extra/categories.json"), 'r') as f:
        categories = json.load(f)
    with open(translatePath("special://home/addons/plugin.video.jiotv/resources/extra/channels.json"), 'r') as f:
        channels = json.load(f)
    channel_ids = [x for x in categories[category_id]]
    items = []
    for each in channel_ids:
        list_item = ListItem(label=channels[str(each)]['name'])
        img_url = channels[str(each)]['logo']
        list_item.setArt({
            'thumb': img_url,
            'icon': img_url
        })
        if channels[str(each)]['isCatchupAvailable']:
            items.append(
                (plugin.url_for(show_epg, day=0, channel_id=each, live_url=channels[str(each)]['url']), list_item, True))
        else:
            list_item.setInfo('video', {
                'title': channels[str(each)]['name'],
                'mediatype': 'tvshow',
            })
            list_item.setProperty('IsPlayable', 'true')
            items.append((channels[str(each)]['url'], list_item, False))

    addDirectoryItems(plugin.handle, items)
    endOfDirectory(plugin.handle)


@plugin.route('/channel/<day>/<channel_id>')
def show_epg(day, channel_id):
    resp = requests.get(
        "http://jiotv.data.cdn.jio.com/apis/v1.3/getepg/get?offset={0}&channel_id={1}&langId=6".format(day, channel_id)).json()
    epg = sorted(
        resp['epg'], key=lambda show: show['startEpoch'], reverse=True)
    livetext = '[COLOR red][B][ LIVE ][/B][/COLOR]'
    items = []
    for each in epg:
        current_epoch = int(time()*1000)
        if not each['stbCatchupAvailable'] or each['startEpoch'] > current_epoch:
            continue
        islive = each['startEpoch'] < current_epoch and each['endEpoch'] > current_epoch
        showtime = '   '+livetext if islive else datetime.fromtimestamp(
            int(each['startEpoch']*.001)).strftime('    [ %I:%M %p -') + datetime.fromtimestamp(int(each['endEpoch']*.001)).strftime(' %I:%M %p ]   %a')
        play_item = ListItem(
            label=each['showname'] + showtime)
        play_item.setArt({
            'thumb': "http://jiotv.catchup.cdn.jio.com/dare_images/shows/"+each['episodePoster'],
            'icon': "http://jiotv.catchup.cdn.jio.com/dare_images/shows/"+each['episodePoster'],
            'fanart': "http://jiotv.catchup.cdn.jio.com/dare_images/shows/"+each['episodePoster'],
        })
        play_item.setInfo('video', {
            'title': each['showname'],
            'genre': each['showGenre'],
            'plot': each['episode_desc'],
            'episode': 0 if each['episode_num'] == -1 else each['episode_num'],
            'cast': each['starCast'].split(', '),
            'director': each['director'],
            'duration': each['duration']*60,
            'tag': each['keywords'],
            'mediatype': 'tvshow' if each['episode_num'] == -1 else 'episode',
        })
        play_item.setProperty('IsPlayable', 'true')
        url = plugin.args.get('live_url')[0] if islive else plugin.url_for(
            playcatchup, channel_name=resp['logoUrl'][:-4], startEpoch=each['startEpoch'])
        items.append(
            (url, play_item, False))
    if len(items) == 0:
        live_item = ListItem(livetext)
        live_item.setArt({
            'thumb': "special://home/addons/plugin.video.jiotv/resources/extra/img/live.png",
            'icon': "special://home/addons/plugin.video.jiotv/resources/extra/img/live.png",
        })
        live_item.setInfo('video', {'title': livetext, 'mediatype': 'video'})
        live_item.setProperty('IsPlayable', 'true')
        items = [
            (plugin.args.get('live_url')[0], live_item, False),
            ('', ListItem('Catchup Not Available'), False)
        ]
    elif day == '0':
        for i in range(-1, -7, -1):
            label = 'Yesterday' if i == - \
                1 else (date.today() + timedelta(days=i)).strftime('%A %d %B')
            items.append(
                (plugin.url_for(show_epg, day=i, channel_id=channel_id), ListItem(label), True))

    addDirectoryItems(plugin.handle, items)
    endOfDirectory(plugin.handle)


@plugin.route('/play/<channel_name>')
def play(channel_name):
    is_helper = inputstreamhelper.Helper('hls')
    if is_helper.check_inputstream():
        play_item = ListItem()
        params = "?"+"&".join([key+'='+value[0]
                               for key, value in plugin.args.items()])
        url = "http://127.0.0.1:48996/play/{0}/master.m3u8{1}".format(
            channel_name, params)
        if not url:
            return
        play_item.setPath(url)
        play_item.setProperty('inputstreamaddon', is_helper.inputstream_addon)
        play_item.setProperty('inputstream.adaptive.manifest_type', 'hls')
        play_item.setMimeType('application/vnd.apple.mpegurl')
        play_item.setContentLookup(False)

        setResolvedUrl(plugin.handle, True, listitem=play_item)


@plugin.route('/playstar/<channel_name>')
def playstar(channel_name):
    is_helper = inputstreamhelper.Helper('hls')
    if is_helper.check_inputstream():
        play_item = ListItem()
        _auth = _hotstarauth_key()
        url = "http://hotstar.live.cdn.jio.com/hotstar_isl/{0}/master.m3u8?hdnea={1}".format(
            channel_name, _auth)
        if not url:
            return
        play_item.setPath(url)
        play_item.setProperty('inputstreamaddon', is_helper.inputstream_addon)
        play_item.setProperty('inputstream.adaptive.manifest_type', 'hls')
        play_item.setProperty(
            'inputstream.adaptive.stream_headers', "User-Agent=hotstar")
        play_item.setMimeType('application/vnd.apple.mpegurl')
        play_item.setContentLookup(False)

        setResolvedUrl(plugin.handle, True, listitem=play_item)


@plugin.route('/playdash/<channel_name>')
def playdash(channel_name):
    is_helper = inputstreamhelper.Helper('mpd', drm='com.widevine.alpha')
    if is_helper.check_inputstream():
        play_item = ListItem()
        _auth = _hotstarauth_key()
        url = "http://hotstar.live.cdn.jio.com/hotstar_isl/{0}/master.mpd?hdnea={1}".format(
            channel_name, _auth)
        play_item.setPath(url)
        play_item.setProperty('inputstreamaddon', is_helper.inputstream_addon)
        play_item.setProperty('inputstream.adaptive.manifest_type', 'mpd')
        play_item.setProperty(
            'inputstream.adaptive.license_type', 'com.widevine.alpha')
        play_item.setProperty('inputstream.adaptive.license_key',
                              'https://ipl.service.expressplay.com/hms/wv/rights/?ExpressPlayToken=BQAAABNlKfMAAAAAAGB5RXIUhuAKhb0o_gG4s6_qdxw4y5xQZyNGjvsbfiltjdLAStqy3hyJnAzQPRNmTknPc1nMTsezyHAxVCdu2VYmI-bCaJTYMefMpfs-fql1lF_B7Zrj-qyxdlafY1xKq42c6z1i9s1FPsE_z8wV6FC8BHNpMw&req_id=2f652cd6|User-Agent=hotstar&Content-Type=application/octet-stream|R{SSM}|')
        play_item.setProperty(
            'inputstream.adaptive.stream_headers', "User-Agent=hotstar")
        play_item.setMimeType('application/dash+xml')
        play_item.setContentLookup(False)

        setResolvedUrl(plugin.handle, True, listitem=play_item)


@plugin.route('/playcatchup/<channel_name>/<startEpoch>')
def playcatchup(channel_name, startEpoch):
    is_helper = inputstreamhelper.Helper('hls')
    if is_helper.check_inputstream():
        play_item = ListItem()
        url = "http://127.0.0.1:48996/catchup/{0}/master.m3u8?startEpoch={1}".format(
            channel_name, startEpoch)
        if not url:
            return
        play_item.setPath(url)
        play_item.setProperty('inputstreamaddon', is_helper.inputstream_addon)
        play_item.setProperty('inputstream.adaptive.manifest_type', 'hls')
        play_item.setMimeType('application/vnd.apple.mpegurl')
        play_item.setContentLookup(False)

        setResolvedUrl(plugin.handle, True, listitem=play_item)


@plugin.route('/logout')
def logout():
    os.path.isfile(
        ADDONDATA + 'headers.json') and os.remove(ADDONDATA + 'headers.json')
    kodiutils.set_setting('username', '')
    kodiutils.set_setting('password', '')


@plugin.route('/pvrsetup')
def pvrsetup():
    IDdoADDON = 'pvr.iptvsimple'
    pathTOaddon = os.path.join(translatePath(
        'special://home/addons'), IDdoADDON)
    pathTOaddon2 = os.path.join(translatePath(
        'special://xbmc/addons'), IDdoADDON)
    if os.path.exists(pathTOaddon) or os.path.exists(pathTOaddon2):
        Addon(IDdoADDON).setSetting(
            'm3uPath', os.path.join(translatePath('special://home/addons/plugin.video.jiotv/resources/extra').decode('utf-8'), 'jiotv.m3u'))
        Addon(IDdoADDON).setSetting(
            'epgUrl', "https://kodi.botallen.com/tv/epg.xml")
        Addon(IDdoADDON).setSetting(
            'epgPathType', '1')
        Addon(IDdoADDON).setSetting(
            'm3uPathType', '0')
    else:
        executebuiltin('InstallAddon(%s)' % (IDdoADDON))
        executebuiltin('SendClick(11)'), sleep(2), Dialog().ok(
            "Add-on Install", "The addon was not present. Please wait for installation to finish and try again.")


def run():
    if check_login():
        plugin.run()
