# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from codequick import Route, run, Script, Resolver

import resources.lib.utils as U
from xbmcgui import DialogProgress
import time
import urlquick
from .api import HotstarAPI
from .builder import Builder
from .contants import BASE_HEADERS, CONTENT_TYPE


@Route.register
def root(plugin):
    yield builder.buildSearch(tray_list)
    menuItmes = api.getMenu()
    for x in builder.buildMenu(menuItmes):
        yield x


@Route.register
def menu_list(plugin, url):
    items, nextPageUrl = api.getPage(url)
    for x in builder.buildPage(items, nextPageUrl):
        yield x


@Route.register
def tray_list(plugin, url, search_query=False):

    items, nextPageUrl = api.getTray(url, search_query=search_query)

    if not items or len(items) == 0:
        yield False
        Script.notify("No Result Found", "No items to show")
        raise StopIteration()

    plugin.content_type = items and CONTENT_TYPE.get(items[0].get("assetType"))
    for x in builder.buildTray(items, nextPageUrl):
        yield x


@Resolver.register
@U.isLoggedIn
def play_vod(plugin, contentId, subtag, label, drm=False):
    playbackUrl, licenceUrl, playbackProto = api.getPlay(
        contentId, subtag, drm)
    if playbackUrl:
        return builder.buildPlay(playbackUrl, licenceUrl, playbackProto, label, drm)
    return False


@Resolver.register
@U.isLoggedIn
def play_ext(plugin, contentId):
    drm, subtag, label = api.getExtItem(contentId)
    if drm is not None:
        playbackUrl, licenceUrl, playbackProto = api.getPlay(
            contentId, subtag, drm)
        if playbackUrl:
            return builder.buildPlay(playbackUrl, licenceUrl, playbackProto, label, drm)
    return False


@Script.register
def login(plugin):
    pdialog = DialogProgress()
    pdialog.create("Login", "1. Go to [B]hotstar.com/in/activate[/B]",
                   line2="2. Login with your hotstar account[CR]3. Enter the 4 digit code", line3="Loading...")
    for code, i in api.doLogin():
        if pdialog.iscanceled() or i == 100:
            break
        else:
            time.sleep(1)
        pdialog.update(i, line3="[B][UPPERCASE]%s[/UPPERCASE][/B]" % code)
    pdialog.close()


@Script.register
def logout(plugin):
    api.doLogout()


api = HotstarAPI()
builder = Builder([menu_list, tray_list, play_vod])
