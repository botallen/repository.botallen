# -*- coding: utf-8 -*-
from codequick.utils import urljoin_partial

NAME = "plugin.video.botallen.hotstar"

# URLs
API_BASE_URL = "https://prod.media.jio.com"
IMG_PUBLIC = "https://jioimages.cdn.jio.com/imagespublic/"
IMG_BASE = "http://jioimages.cdn.jio.com/content/entry/dynamiccontent/thumbs"
IMG_FANART_H_URL = IMG_BASE + "/1920/1080/0/"
IMG_POSTER_V_URL = IMG_BASE + "/1000/-/0/"
IMG_THUMB_H_URL = IMG_BASE + "/1920/1080/0/"

# Configs
ROOT_CONFIG = [("Watch Now", "100019"), ("Movies", "100021"), ("TV Shows",
                                                               "100023"), ("Live TV", "100057"), ("Kids", "100025"), ("Music", "100027")]

MOVIE, TVSHOW, MUSIC, EPISODE, CHANNEL, CHANNEL_CAT = 0, 1, 2, 7, 17, 19
BASE_HEADERS = {"x-apisignatures": "543aba07839",
                "User-Agent": "Jiotv+ Kodi", "devicetype": "tv", "os": "Android", "x-multilang": "true", "AppName": "Jiotv+", "deviceId": "d40ce1e81fe914ee", "appkey": "2ccce09e59153fc9"}
CONTENT_TYPE = {MOVIE: "movies", TVSHOW: "tvshows",
                EPISODE: "episodes", MUSIC: "musicvideos"}
MEDIA_TYPE = {MOVIE: "movie", TVSHOW: "tvshow",
              TVSHOW: "season", EPISODE: "episode", MUSIC: "musicvideo"}

url_constructor = urljoin_partial(API_BASE_URL)

_STAR_CHANNELS = {1141: u'sshd2livetvwv', 368: u'starvijay', 1127: u'starbharat', 457: u'jalsamovies', 362: u'sshindiwv', 459: u'asianetmovies', 460: u'ssselecthd1wv', 461: u'ssselecthd2wv', 1143: u'starutsav', 1121: u'starpravah',
                  300243: u'starsuvarna', 1126: u'starjalsa', 181: u'asianetplus', 300236: u'maatv', 759: u'maagold', 300242: u'maagold', 760: u'maamovies', 443: u'asianethd', 1125: u'stargold', 458: u'starsuvarnaplus', 1116: u'starplushd', 1142: u'sshd1livetvwv'}


# def plugin_url_constructor(
#     x): return "plugin://%s/resources/lib/main/%s/" % (NAME, x)

# TRAY_IDENTIFIERS = {
#     "CONTINUE_WATCHING_TRAY": "v1/users/{P_ID}/preferences/continue-watching?size=20",
#     "WATCHLIST_TRAY": "v1/users/{P_ID}/trays/watchlist?meta=true&limit=20"}
