# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# xbmc imports
from xbmcaddon import Addon
from xbmc import executebuiltin, translatePath
from xbmcgui import ListItem, Dialog

# codequick imports
from codequick import Route, run, Listitem, Resolver, Script
from codequick.utils import keyboard
from codequick.script import Settings
from codequick.storage import PersistentDict

# add-on imports
from .utils import getHeaders, isLoggedIn, login as ULogin, logout as ULogout, check_addon
from .proxy import ChannelRequestHandler
from .constants import CONFIG, CHANNELS_SRC, IMG_CATCHUP, PLAY_URL, IMG_PUBLIC, IMG_CATCHUP_SHOWS, CATCHUP_PLAY, CATCHUP_SRC, M3U_SRC, EPG_SRC

# additional imports
import urlquick
from urllib import urlencode
import inputstreamhelper
import json
import os
from time import time, sleep
from datetime import datetime, timedelta, date


# Root path of plugin
@Route.register
def root(plugin):
    for e in ["Genres", "Languages"]:
        yield Listitem.from_dict(**{
            "label": e,
            "art": {
                "thumb": CONFIG[e][0].get("tvImg"),
                "icon": CONFIG[e][0].get("tvImg"),
                "fanart": CONFIG[e][0].get("promoImg"),
            },
            "callback": show_listby,
            "params": {"by": e}
        })


# Shows Filter options
@Route.register
def show_listby(plugin, by):
    for each in CONFIG[by]:
        yield Listitem.from_dict(**{
            "label": each.get("name"),
            "art": {
                "thumb": each.get("tvImg"),
                "icon": each.get("tvImg"),
                "fanart": each.get("promoImg")
            },
            "callback": show_category,
            "params": {"category_id": each.get("name").replace(" ", ""), "by": by}
        })


# Shows channels by selected filter/category
@Route.register
def show_category(plugin, category_id, by):
    resp = urlquick.get(CHANNELS_SRC).json()

    def fltr(x):
        fby = by.lower()[:-1]
        if fby == "genre":
            return x.get(fby) == category_id and Settings.get_boolean(x.get("language"))
        else:
            return x.get(fby) == category_id

    for each in filter(fltr, resp):
        art = {
            "thumb": IMG_CATCHUP + each.get("default_logo"),
            "icon": IMG_CATCHUP + each.get("default_logo"),
            "fanart": IMG_CATCHUP + each.get("default_logo")
        }
        if each.get("icon"):
            art["thumb"] = art["icon"] = IMG_PUBLIC + each.get("icon")
        if each.get("fanart"):
            art["fanart"] = IMG_PUBLIC + each.get("fanart")
        litm = Listitem.from_dict(**{
            "label": each.get("name"),
            "art": art,
            "callback": each.get("ext") or PLAY_URL + each.get("data")
        })
        if each.get("isCatchupAvailable"):
            litm.context.container(show_epg, "Catchup", 0, each.get(
                "id"), each.get("ext") or PLAY_URL + each.get("data"))
        yield litm


# Shows EPG container from Context menu
@Route.register
def show_epg(plugin, day, channel_id, live_url=""):
    resp = urlquick.get(CATCHUP_SRC.format(day, channel_id)).json()
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
        timestr = datetime.fromtimestamp(
            int(each.get("startEpoch", 0)*.001)).strftime('%d_%m_%y_%H_%M')
        yield Listitem.from_dict(**{
            "label": each['showname'] + showtime,
            "art": {
                'thumb': IMG_CATCHUP_SHOWS+each['episodePoster'],
                'icon': IMG_CATCHUP_SHOWS+each['episodePoster'],
                'fanart': IMG_CATCHUP_SHOWS+each['episodePoster'],
            },
            "callback": live_url if islive else play,
            "info": {
                'title': each['showname'] + showtime,
                'originaltitle': each['showname'],
                "tvshowtitle": each['showname'],
                'genre': each['showGenre'],
                'plot': each['description'],
                "episodeguide": each.get("episode_desc"),
                'episode': 0 if each['episode_num'] == -1 else each['episode_num'],
                'cast': each['starCast'].split(', '),
                'director': each['director'],
                'duration': each['duration']*60,
                'tag': each['keywords'],
                'mediatype': 'episode',
            },
            "params": {
                "dt": {
                    "proto": "hls",
                    "pUrl": CATCHUP_PLAY.format(resp['logoUrl'][:-4], timestr, urlencode(ChannelRequestHandler.getTokenParams(6000))),
                    "lUrl": "{TOKEN}|{HEADERS}|R{SSM}|",
                    "hdrs": "User-Agent=Jiotv"
                }
            }
        })
    if int(day) == 0:
        for i in range(-1, -7, -1):
            label = 'Yesterday' if i == - \
                1 else (date.today() + timedelta(days=i)).strftime('%A %d %B')
            yield Listitem.from_dict(**{
                "label": label,
                "callback": show_epg,
                "params": {
                    "day": i,
                    "channel_id": channel_id
                }
            })


# Play live stream/ catchup according to `playData`.
# Also insures that user is logged in.
@Resolver.register
@isLoggedIn
def play(plugin, dt):
    is_helper = inputstreamhelper.Helper(
        dt.get("proto", "mpd"), drm=dt.get("drm"))
    if is_helper.check_inputstream():
        licenseUrl = dt.get("lUrl") and dt.get("lUrl").replace("{HEADERS}", urlencode(
            getHeaders())).replace("{TOKEN}", urlencode(ChannelRequestHandler.getTokenParams(6000)))
        art = {}
        if dt.get("cLogo"):
            art['thumb'] = art['icon'] = IMG_CATCHUP + dt.get("cLogo")
        if dt.get("cImg"):
            art['fanart'] = IMG_PUBLIC + dt.get("cImg")
        return Listitem().from_dict(**{
            "label": dt.get("label") or plugin._title,
            "art": art or None,
            "callback": dt.get("pUrl"),
            "properties": {
                "IsPlayable": True,
                "inputstreamaddon": is_helper.inputstream_addon,
                "inputstream.adaptive.stream_headers": dt.get("hdrs"),
                "inputstream.adaptive.manifest_type": dt.get("proto", "mpd"),
                "inputstream.adaptive.license_type": dt.get("drm"),
                "inputstream.adaptive.license_key": licenseUrl,
            }
        })


# Login `route` to access from Settings
@Script.register
def login(plugin):
    username = Settings.get_string("username") or keyboard(
        "Username (MobileNo / Email)")
    password = Settings.get_string(
        "password") or keyboard("Password", hidden=True)
    ULogin(username, password)


# Logout `route` to access from Settings
@Script.register
def logout(plugin):
    ULogout()

# PVR Setup `route` to access from Settings
@Script.register
def pvrsetup(plugin):
    IDdoADDON = 'pvr.iptvsimple'
    if check_addon(IDdoADDON):
        Addon(IDdoADDON).setSetting(
            'm3uPathType', '1')
        Addon(IDdoADDON).setSetting(
            'm3uUrl', M3U_SRC)
        Addon(IDdoADDON).setSetting(
            'epgPathType', '1')
        Addon(IDdoADDON).setSetting(
            'epgUrl', EPG_SRC)

# Cache cleanup
@Script.register
def cleanup(plugin):
    urlquick.cache_cleanup(-1)
    with PersistentDict("proxy_cache") as cache:
        cache.clear()
    Script.notify("Cache Cleaned", "")
