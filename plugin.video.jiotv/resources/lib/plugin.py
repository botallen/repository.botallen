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
from utils import check_login, getChannelUrl


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
    not_working_channels = [1074, 1213, 1214, 1215, 247, 362,
                            160, 159, 461, 460, 1266, 1275, 1276, 1280, 932, 1066, 1061, 1059, 1061]
    channel_ids = [x for x in categories[category_id]
                   if not x in not_working_channels]
    items = []
    for each in channel_ids:
        list_item = ListItem(label=channels[str(each)]['name'])
        img_url = channels[str(each)]['logo']
        list_item.setArt({
            'thumb': img_url,
            'icon': img_url,
            'fanart': img_url
        })
        list_item.setInfo('video', {
            'title': channels[str(each)]['name'],
            'genre': category_id,
            'plot': '',
            'mediatype': 'video'
        })
        list_item.setProperty('IsPlayable', 'true')
        items.append(("plugin://plugin.video.jiotv/play/" +
                      str(each), list_item, False))
    addDirectoryItems(plugin.handle, items)
    endOfDirectory(plugin.handle)


@plugin.route('/play/<channel_id>')
def play(channel_id):
    play_item = ListItem()
    url = getChannelUrl(channel_id)
    if not url:
        return
    play_item.setPath(url)
    play_item.setProperty('inputstreamaddon', 'inputstream.adaptive')
    play_item.setProperty('inputstream.adaptive.manifest_type', 'hls')
    play_item.setProperty(
        'inputstream.adaptive.stream_headers', url.split('|')[1])
    play_item.setProperty(
        'inputstream.adaptive.license_key', url.split('?')[1])
    play_item.setProperty(
        'inputstream.adaptive.media_renewal_url', sys.argv[0])
    play_item.setMimeType('application/vnd.apple.mpegurl')
    play_item.setContentLookup(False)

    setResolvedUrl(plugin.handle, True, listitem=play_item)


@plugin.route('/logout')
def logout():
    os.path.isfile(
        ADDONDATA + 'channels.json') and os.remove(ADDONDATA + 'channels.json')
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
