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
tvf_cookies = {
    "__tvf_guid": "06316369-2ede-483a-9d4a-2370ba161e56:1jBD48:AjXXDD_BEPjR4Eq8A5zUnWOF3Os"}
tvf_api_url = "https://webapi-services.tvfplay.com"


@plugin.route('/')
def index():
    rows = requests.get(
        tvf_api_url+'/v2/api/v2/home/w/rows', cookies=tvf_cookies)
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
    icon_host = "https://static1.tvfplay.com/"
    def _url(x): return icon_host + x
    fanart = _url(item.get('aspect_xl_large_path', 0)
                  or item.get('aspect_medium_path', 0) or item.get('logo_medium_path', 0))
    # if not 'a4_medium_path' in item else _url('a4_medium_path')
    icon = _url(item.get('a4_medium_path', 0)
                or item.get('aspect_medium_path', 0) or item.get('logo_medium_path', 0))
    # if not 'logo_medium_path' in item else _url('logo_medium_path')
    thumb = _url(item.get('logo_medium_path', 0) or item.get(
        'a4_medium_path', 0) or item.get('aspect_medium_path', 0))
    return {
        'thumb': thumb,
        'icon': icon,
        'fanart': fanart
    }


@plugin.route('/<path:url>')
def show_handle(url):
    url = tvf_api_url+"/v2/" + \
        url.replace('/{{page}}/{{limit}}', '/1/14')
    results = requests.get(url, cookies=tvf_cookies)
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
    results = requests.get(url, cookies=tvf_cookies)
    itmes = []
    results = requests.get(url, cookies=tvf_cookies).json()['seasons']
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
    results = requests.get(url, cookies=tvf_cookies)
    itmes = []
    results = requests.get(url, cookies=tvf_cookies).json()['episodes']
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
    episode = requests.get(
        tvf_api_url+'/v2/api/v2/episode/w/v2/episode/'+id, cookies=tvf_cookies)
    if episode.status_code == 200:
        episode = episode.json()['data']['episode']
        video_account_id = episode.get('video_account_id')
        bc_video_id = episode.get('bc_video_id')
        if video_account_id and bc_video_id:
            headers = {
                "Accept": "application/json;pk=BCpkADawqM0CNpGQ_gjGNHvcbXKSBaE3xAK6dMh56dYfFe6ZLAwm5GoJ8PcDhHhM57pANu4lYZ9NOclXjsm-9ZPbjqiHavsJMIRM1DpBqPfYuyDRmvuXBznZaJvWowTx5FdOtZUVGDNXpLUxzQ41BbqXSt2finG5l6Ca8a-Z1---0Tft12T4pJXpsxC0GYgnqbOszz5FK93P4v4lKgENtl6K-E-PbaTFguoeaaCZEqJqfJwn_lT86ki11U_C6cuKY8-34J4Iln0Mi3q_9FtW76WikdAvIX_gWLZm0NdYdciESwt1U1ddRY_iZP8fFfP0qugwfOFKTx4b50lPjp-vMfG-eB3IQzuZA7jyq2A26FsJ13v2VM0jS-0ERm4wluwwrpNW3Ko_BZNIg_Clu2nPqZe0rpcm62A991rTFbBRPU4DZP1DNrziHTk34HZBNpLEBfqHTK_6YRgkrOQ5NnAzh8g_GX5CNDQq--PVHueNdkTCQsUuiD9iQPE0-Cs4X0Uqjnr3MZt7KdVqT7ux_6wFTWuKDWA_Jcz7-B8Diqv5B3kwi8ihaNk0h15KNUQjqix-ZMdHb69zPIUh_QzrVDqBN6PZ3lhP1N03fNpwloPoQ6_09E--ZNYSzwU_Hec7h-W5e89AMqUxYnBYZ6wnUnMJbrav_EjIfcDtgkbtfIjz9rCM3NokKhhupZPaiqJojkD-QTxVQ-EcGHH4uHXPN2t1Rk9nETiHGxct1Rbb0w",
                "Origin": "https://tvfplay.com"
            }
            url = "https://edge.api.brightcove.com/playback/v1/accounts/{0}/videos/{1}".format(
                video_account_id, bc_video_id)
            result = requests.get(url, headers=headers).json()
            src = result.get('sources')[0]['src']
            text_tracks = [x.get('src') for x in result.get('text_tracks')]
            play_item = ListItem(path=src)
            play_item.setProperty('inputstreamaddon',
                                  'inputstream.adaptive')
            play_item.setProperty(
                'inputstream.adaptive.manifest_type', 'hls')
            play_item.setMimeType('application/vnd.apple.mpegurl')
            play_item.setContentLookup(False)

            play_item.setSubtitles(text_tracks)

            # Pass the item to the Kodi player.
            setResolvedUrl(plugin.handle, True, listitem=play_item)


def run():
    plugin.run()
