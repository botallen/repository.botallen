# -*- coding: utf-8 -*-
from codequick.utils import urljoin_partial

NAME = "plugin.video.botallen.hotstar"

# URLs
API_BASE_URL = "https://api.hotstar.com"
IMG_BASE = "https://img1.hotstar.com/image/upload"
IMG_FANART_H_URL = IMG_BASE + "/f_auto,w_1920,h_1080/%s.jpg"
IMG_POSTER_V_URL = IMG_BASE + "/f_auto,t_web_vl_3x/%s.jpg"
IMG_THUMB_H_URL = IMG_BASE + "/f_auto,t_web_hs_3x/%s.jpg"

BASE_HEADERS = {"x-country-code": "in", "x-platform-code": "ANDROID"}
CONTENT_TYPE = {"MOVIE": "movies", "SHOW": "tvshows",
                "SEASON": "tvshows", "EPISODE": "episodes"}
MEDIA_TYPE = {"MOVIE": "movie", "SHOW": "tvshow",
              "SEASON": "season", "EPISODE": "episode"}

url_constructor = urljoin_partial(API_BASE_URL)


# def plugin_url_constructor(
#     x): return "plugin://%s/resources/lib/main/%s/" % (NAME, x)

# TRAY_IDENTIFIERS = {
#     "CONTINUE_WATCHING_TRAY": "v1/users/{P_ID}/preferences/continue-watching?size=20",
#     "WATCHLIST_TRAY": "v1/users/{P_ID}/trays/watchlist?meta=true&limit=20"}
