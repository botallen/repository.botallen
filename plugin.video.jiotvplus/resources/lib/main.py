# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from codequick import Route, run, Script, Resolver

import resources.lib.utils as U
import time
from .api import JioAPI
from .builder import Builder
from .contants import CONTENT_TYPE


@Route.register
def root(plugin):
    yield builder.buildSearch(tray_list)
    for x in builder.buildMenu():
        yield x


@Route.register
def menu_list(plugin, url):
    data, nextPageUrl = api.getPage(url)
    for x in builder.buildPage(data, nextPageUrl, url):
        yield x


@Route.register
def tray_list(plugin, url="", search_query=False, post_json=None, isCarousal=False):
    items, nextPageUrl = api.getTray(
        url, search_query=search_query, post_json=post_json, isCarousal=isCarousal)

    if not items or len(items) == 0:
        yield False
        Script.notify("No Result Found", "No items to show")
        raise StopIteration()

    plugin.content_type = items and CONTENT_TYPE.get(
        items[0].get("app", {}).get("type"))
    for x in builder.buildTray(items, nextPageUrl):
        yield x


@Resolver.register
@U.isLoggedIn
def play_vod(plugin, Id, label, vendor, extId=None):
    data = api.getPlay(
        Id, vendor, extId)
    if data:
        return builder.buildPlay(data, label)
    return False


@Resolver.register
@U.isLoggedIn
def play_url(plugin, playbackUrl, licenseUrl, label="", headers={}):
    return builder.buildPlayFromURL(playbackUrl, licenseUrl, label, headers)


@Resolver.register
def play_ext(plugin, label, playbackUrl, addonid, minVersion=False):
    return builder.buildExt(label, playbackUrl, addonid, minVersion)


@Script.register
def login(plugin):
    api.doLogin()


@Script.register
def logout(plugin):
    api.doLogout()


api = JioAPI()
builder = Builder([menu_list, tray_list, play_vod, play_ext, play_url])
