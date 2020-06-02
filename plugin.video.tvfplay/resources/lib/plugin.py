# -*- coding: utf-8 -*-

import routing
import logging
import xbmcaddon
from xbmc import log, LOGNOTICE
from resources.lib import kodiutils
from resources.lib import kodilogging
import requests
import sys
from urllib import unquote
from xbmcgui import ListItem
from xbmcplugin import addDirectoryItems, endOfDirectory, setResolvedUrl


ADDON = xbmcaddon.Addon()
logger = logging.getLogger(ADDON.getAddonInfo('id'))
kodilogging.config()
plugin = routing.Plugin()
plugin_url = "plugin://plugin.video.tvfplay"
tvf_api_url = "https://webapi-services.tvfplay.com"
session = requests.Session()
session.head("https://tvfplay.com/")


@plugin.route('/')
def index():
    rows = session.get(tvf_api_url+'/v2/api/v2/home/w/rows')
    itmes = []
    if rows.status_code == 200:
        rows = rows.json()['data']['rows']
        for row in rows:
            # path = row['web_api'][7:].replace(
            #     '/{{page}}/{{limit}}', '').replace('/w', '')
            # log(path, LOGNOTICE)
            # r = path.split('/')
            itmes.append((plugin.url_for(
                show_handle, row['web_api']), ListItem(row['name']), True))
            # args = {"handle": r[0], "category": r[1], "number": r[2]}
    addDirectoryItems(plugin.handle, itmes)
    endOfDirectory(plugin.handle)


def getArt(item):
    icon_host = "https://static1.tvfplay.com/%s"
    def _url(x): return icon_host % unquote(x or "")
    fanart = _url(item.get('aspect_xl_large_path')
                  or item.get('aspect_medium_path') or item.get('logo_medium_path'))
    # if not 'a4_medium_path' in item else _url('a4_medium_path')
    icon = _url(item.get('a4_medium_path')
                or item.get('aspect_medium_path') or item.get('logo_medium_path'))
    # if not 'logo_medium_path' in item else _url('logo_medium_path')
    thumb = _url(item.get('logo_medium_path') or item.get(
        'a4_medium_path') or item.get('aspect_medium_path'))
    return {
        'thumb': thumb,
        'icon': icon,
        'fanart': fanart
    }


@plugin.route('/<path:url>')
def show_handle(url):
    url = tvf_api_url+"/v2/" + \
        url.replace('/{{page}}/{{limit}}', '/1/14')
    results = session.get(url)
    itmes = []
    if results.status_code == 200:
        results = results.json()['data']['results']
        for each in results:
            list_item = ListItem(label=each['telemetry_data']['name'])
            list_item.setArt(getArt(each))
            if 'type' in each and each['type'] == 'series':
                if 'season_count' in each:
                    list_item.addSeason(
                        each['season_count'], each['telemetry_data']['name'])
                itmes.append((plugin.url_for(
                    list_series, "api/v2/series/{0}/1/15/default".format(each['telemetry_data']['id'])), list_item, True))
            else:
                list_item.setInfo('video', {
                    'title': each['telemetry_data']['name'],
                    'mediatype': 'video'
                })
                list_item.setProperty('IsPlayable', 'true')
                effective_path = plugin_url + '/play/' + str(each['id'])
                itmes.append((effective_path, list_item, False))
    addDirectoryItems(plugin.handle, itmes)
    endOfDirectory(plugin.handle)


@plugin.route('/series/<path:url>')
def list_series(url):
    url = tvf_api_url+"/v2/" + url
    itmes = []
    results = session.get(url).json()['seasons']
    for each in results:
        list_item = ListItem(label=each['telemetry_data']['name'])
        list_item.addSeason(
            int(each['season_number']), each['telemetry_data']['name'])
        itmes.append((plugin.url_for(
            list_episodes, "api/v2/season/{0}/1/15/default".format(each['season_id'])), list_item, True))
    addDirectoryItems(plugin.handle, itmes)
    endOfDirectory(plugin.handle)


@plugin.route('/episodes/<path:url>')
def list_episodes(url):
    url = tvf_api_url+"/v2/" + url
    itmes = []
    results = session.get(url).json()['episodes']
    for i, each in enumerate(results):
        list_item = ListItem(label=each['name'])
        list_item.setArt({
            'thumb': each['thumbnail_image_url'],
            'icon': each['aspect_medium_without_text'],
            'fanart': each['highlight_image_url']
        })
        list_item.setInfo('video', {
            'title': each['telemetry_data']['name'],
            'episode': i+1,
            'plot': each['description'],
            'mediatype': 'video'
        })
        list_item.setProperty('IsPlayable', 'true')
        itmes.append((plugin_url + '/play/' +
                      each['episode_id'], list_item, False))
    addDirectoryItems(plugin.handle, itmes)
    endOfDirectory(plugin.handle)


@plugin.route('/play/<id>')
def play(id):
    episode = session.get(
        tvf_api_url+'/ms/api/episode/playback/web/'+id, headers={"platform": "web_desktop", "guid": session.headers.get("__tvf_guid")}).json().get("data")
    if episode:
        src = episode.get("manifest_url")
        play_item = ListItem(path=src)
        play_item.setProperty('inputstreamaddon',
                              'inputstream.adaptive')
        play_item.setProperty(
            'inputstream.adaptive.manifest_type', 'hls')
        play_item.setMimeType('application/vnd.apple.mpegurl')
        play_item.setContentLookup(False)
        text_tracks = ["https://static1.tvfplay.com/" +
                       x for x in episode.get("subtitle", {}).values()]
        play_item.setSubtitles(text_tracks)
        setResolvedUrl(plugin.handle, True, listitem=play_item)


def run():
    plugin.run()
