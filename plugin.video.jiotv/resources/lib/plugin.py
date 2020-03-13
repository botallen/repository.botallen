# -*- coding: utf-8 -*-

import routing
import logging
import json
import requests
from xbmcaddon import Addon
from xbmc import executebuiltin, translatePath
import os
import sys
from time import sleep
from resources.lib import kodiutils
from resources.lib import kodilogging
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
        items.append(
            (plugin.url_for(show_category, each), ListItem(each), True))
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
        list_item.setInfo('video', {
            'title': channels[str(each)]['name'],
            'genre': category_id,
            'plot': '',
            'mediatype': 'video'
        })
        list_item.setProperty('IsPlayable', 'true')
        items.append((channels[str(each)]['url'], list_item, False))
    addDirectoryItems(plugin.handle, items)
    endOfDirectory(plugin.handle)


@plugin.route('/play/<channel_name>')
def play(channel_name):
    play_item = ListItem()
    hls = '' if not 'hls' in plugin.args else "?hls="+plugin.args['hls'][0]
    url = "http://127.0.0.1:48996/play/{0}/master.m3u8{1}".format(
        channel_name, hls)
    if not url:
        return
    play_item.setPath(url)
    play_item.setProperty('inputstreamaddon', 'inputstream.adaptive')
    play_item.setProperty('inputstream.adaptive.manifest_type', 'hls')
    play_item.setMimeType('application/vnd.apple.mpegurl')
    play_item.setContentLookup(False)

    setResolvedUrl(plugin.handle, True, listitem=play_item)


@plugin.route('/playstar/<channel_name>')
def playstar(channel_name):
    play_item = ListItem()
    _auth = _hotstarauth_key()
    url = "http://hotstar.live.cdn.jio.com/hotstar_isl/{0}/master.m3u8?hdnea={1}".format(
        channel_name, _auth)
    if not url:
        return
    play_item.setPath(url)
    play_item.setProperty('inputstreamaddon', 'inputstream.adaptive')
    play_item.setProperty('inputstream.adaptive.manifest_type', 'hls')
    play_item.setProperty(
        'inputstream.adaptive.stream_headers', "User-Agent=hotstar")
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
