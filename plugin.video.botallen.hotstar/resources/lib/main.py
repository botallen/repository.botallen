# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from codequick import Route, Listitem, run, Script, Resolver
from codequick.utils import urljoin_partial, bold
from codequick.storage import PersistentDict
import resources.lib.utils as U
from xbmcgui import DialogProgress
import time
import re
import json
from base64 import b64decode
from uuid import uuid4
import urlquick
import xbmcgui
import inputstreamhelper
from urllib import urlencode, quote_plus

PROTOCOL = 'mpd'
DRM = 'com.widevine.alpha'
is_helper = inputstreamhelper.Helper(PROTOCOL, drm=DRM)

# for development only
# urlquick.cache_cleanup(-1)

# Base url constructor
API_BASE = "https://api.hotstar.com"
IMG_HOST = "http://img1.hotstar.com/image/upload/f_auto,w_1920,h_1080/%s.jpg"
url_constructor = urljoin_partial(API_BASE)

BASE_HEADERS = {"x-country-code": "in", "x-platform-code": "ANDROID"}

CONTENT_TYPE = {"MOVIE": "movies", "SHOW": "tvshows",
                "SEASON": "tvshows", "EPISODE": "episodes"}
# TRAY_IDENTIFIERS = {
#     "CONTINUE_WATCHING_TRAY": "v1/users/{P_ID}/preferences/continue-watching?size=20",
#     "WATCHLIST_TRAY": "v1/users/{P_ID}/trays/watchlist?meta=true&limit=20"}

Script.log(U.getAuth(), lvl=Script.INFO)


@Route.register
def root(plugin):
    # Request the online resource
    url = url_constructor("/o/v2/menu")
    resp = urlquick.get(
        url, headers={"x-country-code": "in", "x-platform-code": "ANDROID_TV"}).json()

    root_elem = resp['body']['results']['menuItems']
    yield Listitem().search(tray_list, url="")
    # Parse each category
    for each in root_elem:
        if not each.get("pageUri"):
            continue
        item = Listitem()

        # The image tag contains both the image url and title
        # img = elem.find(".//img")

        # Set the thumbnail image
        item.art["fanart"] = "https://secure-media.hotstar.com/static/firetv/v1/poster_%s_in.jpg" % each.get(
            "name").lower()

        # Set the title
        item.label = each.get("name")

        # Fetch the url
        url = each.get("pageUri").replace(
            "offset=0&size=20&tao=0&tas=5", "offset=0&size=100&tao=0&tas=1")

        # This will set the callback that will be called when listitem is activated.
        # 'video_list' is the route callback function that we will create later.
        # The 'url' argument is the url of the category that will be passed
        # to the 'video_list' callback.
        if each.get("pageType"):
            item.set_callback(menu_list, url=url)
        else:
            item.set_callback(tray_list, url=url, max_age=-1)

        # Return the listitem as a generator.
        yield item


@Route.register
def menu_list(plugin, url):
    # Request the online resource.
    results = urlquick.get(url, headers=BASE_HEADERS).json()[
        'body']['results']

    for each in results['trays']['items']:
        if not each.get("traySource") or each.get("traySource") == "THIRD_PARTY":
            continue

        item = Listitem()

        # Set the thumbnail image
        # item.art["thumb"] = img.get("src")

        # Set the title
        item.label = each.get("title")
        headers = BASE_HEADERS
        if each.get("traySource") == "CATALOG":
            url = url_constructor(
                "/o/v1/tray/e/%s/items?tao=0&tas=15" % each.get("id"))
        elif each.get("traySource") == "GRAVITY":
            continue
            # with PersistentDict("userdata.pickle") as db:
            #     udata = db.get("udata")
            # if udata:
            #     pId = json.loads(udata.get("sub").encode('utf-8')).get("pId")
            #     # if each.get("addIdentifier") in TRAY_IDENTIFIERS:
            #     #     addIdentifier = TRAY_IDENTIFIERS[each.get("addIdentifier")]
            #     if "P_ID" in each.get("addIdentifier"):
            #         url = "https://persona.hotstar.com/" + \
            #             each.get("addIdentifier").format(P_ID=pId)
            #         headers = U.getPlayHeaders(includeST=True)
            #     else:
            #         continue
            # else:
            #     continue
        item.set_callback(tray_list, url=url, headers=headers)

        # Return the listitem as a generator.
        yield item
    # Return the next page listitem as a generator if required.
    if results.get("nextOffsetURL") or results['trays'].get("nextOffsetURL"):
        url = esults.get("nextOffsetURL") or results['trays'].get(
            "nextOffsetURL")
        yield Listitem().next_page(url=url)


@Route.register
def tray_list(plugin, url, max_age=urlquick.MAX_AGE, search_query=False, headers=BASE_HEADERS):
    if search_query:
        url = url_constructor("/s/v1/scout?q=%s&size=30" %
                              quote_plus(search_query))
    # Request the online resource.
    results = urlquick.get(url, headers=headers, max_age=max_age).json()
    if "data" in results:
        results = results.get("data")
        results['items'] = results.get("items").values()
    else:
        results = results['body']['results']
    if results.get("totalResults") == 0:
        yield False
        Script.notify("No Result Found", "No items to show")
        raise StopIteration()
    if not "items" in results:
        results = results.get("assets")
    plugin.content_type = results.get("items") and CONTENT_TYPE.get(
        results.get("items")[0].get("assetType"))
    for each in results.get("items"):
        item = Listitem()

        # Set the thumbnail image
        if each.get("images"):
            img = IMG_HOST % each.get("images").get("h")
            item.art["thumb"] = img
            item.art["fanart"] = img

        if each.get("assetType") == "SEASON":
            # Set the title
            item.label = "Season %d (%d) " % (
                each.get("seasonNo"), each.get("episodeCnt"))
            item.set_callback(tray_list, url=each.get("uri"))

            # Return the listitem as a generator.
            yield item
        elif each.get("assetType") == "SHOW":
            # Set the title
            item.label = each.get("title")

            url = url_constructor(
                "/o/v1/tray/g/2/items?eid=%d&etid=2&tao=0&tas=100" % each.get("id"))
            item.set_callback(tray_list, url=url)

            # Return the listitem as a generator.
            yield item
        elif each.get("assetType") in ["CHANNEL", "GENRE", "GAME", "LANGUAGE"]:
            # Set the title
            item.label = each.get("title")
            callback = menu_list if each.get(
                "assetType") == "GAME" or each.get("pageType") == "HERO_LANDING_PAGE" else tray_list
            item.set_callback(callback, url=each.get("uri"))

            # Return the listitem as a generator.
            yield item
        else:
            # Set the title
            item.label = each.get("title")
            # Set the duration of the video
            item.info["duration"] = each.get("duration")

            # Set thel plot info
            item.info["plot"] = each.get("description")

            item.stream.hd(2)

            subtag = each.get(
                "isSubTagged") and "subs-tag:Hotstar%s|" % each.get("labels")[0]
            callback = play_drm if each.get("encrypted") == True else play_vod
            item.set_callback(callback, contentId=each.get(
                "contentId"), subtag=subtag, label=each.get("title"))

            # Return the listitem as a generator.
            yield item

    # Return the next page listitem as a generator if required.
    if results.get("nextOffsetURL"):
        yield Listitem().next_page(url=results.get("nextOffsetURL"))


@Resolver.register
@U.isLoggedIn
def play_drm(plugin, contentId, subtag, label):
    # refreshToken()
    url = url_constructor("/play/v1/playback/content/%s" % contentId)
    headers = U.getPlayHeaders()
    params = U.getPlayParams(subtag)
    try:
        playBackSets = urlquick.get(
            url, params=params, headers=headers, max_age=-1).json().get("data").get("playBackSets")
    except urlquick.HTTPError, e:
        if e.code == 402:
            Script.notify(
                "Subscription Error", "You don't have valid subscription to watch this content")
            return False
        else:
            raise
    playbackUrl, licenceUrl = U.findPlayback(playBackSets)
    if playbackUrl and licenceUrl and is_helper.check_inputstream():
        Script.log("Found Widevine stream %s" % playbackUrl, lvl=Script.INFO)
        play_item = Listitem()
        play_item.label = label
        play_item.path = playbackUrl
        play_item.property['inputstreamaddon'] = is_helper.inputstream_addon
        play_item.property['inputstream.adaptive.manifest_type'] = PROTOCOL
        play_item.property['inputstream.adaptive.license_type'] = DRM
        play_item.property[
            'inputstream.adaptive.stream_headers'] = urlencode(headers)
        play_item.property['inputstream.adaptive.license_key'] = licenceUrl + \
            '|%s&Content-Type=application/octet-stream|R{SSM}|' % urlencode(
                headers)
        return play_item
    return False


@Resolver.register
@U.isLoggedIn
def play_vod(plugin, contentId, subtag, label):
    url = url_constructor("/play/v1/playback/content/%s" % contentId)
    headers = U.getPlayHeaders()
    params = U.getPlayParams(subtag)
    try:
        playBackSets = urlquick.get(
            url, params=params, headers=headers, max_age=-1).json().get("data").get("playBackSets")
    except urlquick.HTTPError, e:
        if e.code == 402:
            Script.notify(
                "Subscription Error", "You don't have valid subscription to watch this content")
            return False
        else:
            raise
    playbackUrl, _ = U.findPlayback(playBackSets, encryption="plain")
    Script.log("Found plain stream for %s" % contentId, lvl=Script.INFO)
    if playbackUrl:
        playbackProto = "mpd"
    else:
        playbackUrl = playBackSets[0].get("playbackUrl")
        playbackProto = "hls"
    play_item = Listitem()
    play_item.label = label
    play_item.path = playbackUrl
    play_item.property['inputstreamaddon'] = "inputstream.adaptive"
    play_item.property['inputstream.adaptive.manifest_type'] = playbackProto
    play_item.property['inputstream.adaptive.stream_headers'] = urlencode(
        headers)
    return play_item


@Script.register
def login(plugin):
    url = url_constructor("/in/aadhar/v2/firetv/in/users/logincode")
    code = urlquick.post(
        url, headers={"Content-Length": "0"}).json().get("description").get("code")
    pdialog = DialogProgress()
    pdialog.create("Login", "1. Go to [B]hotstar.com/in/activate[/B]",
                   line2="2. Login with your hotstar account", line3="3. Enter the 4 digit code [B][UPPERCASE]%s[/UPPERCASE][/B]" % code)
    for i in range(1, 101):
        if(pdialog.iscanceled()):
            break
        # if i % 4 == 0:
        token = urlquick.get(
            url+"/%s" % code, max_age=-1).json().get("description").get("userIdentity")
        Script.log(token, lvl=Script.INFO)
        if token:
            with PersistentDict("userdata.pickle") as db:
                db["token"] = token
                db["deviceId"] = uuid4()
                db["udata"] = json.loads(
                    b64decode(token.split(".")[1]+"========"))
                db.flush()
            break
        else:
            time.sleep(1)
        pdialog.update(i)
    pdialog.close()


@Script.register
def logout(plugin):
    with PersistentDict("userdata.pickle") as db:
        db.clear()
        db.flush()
    Script.notify("Logout Success", "You are logged out")
