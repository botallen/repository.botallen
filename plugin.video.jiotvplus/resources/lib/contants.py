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
CHANNELS_SRC = "https://raw.githubusercontent.com/botallen/repository.botallen/master/plugin.video.jiotv/resources/extra/channels.json"
PLAY_URL = "plugin://plugin.video.jiotv/resources/lib/main/play/?_pickle_="

# Configs
ROOT_CONFIG = [("Home", "100059"), ("Movies", "100021"), ("TV Shows", "100023"),
               ("Live TV", "100057"), ("Kids", "100025"), ("Music", "100027")]

MOVIE, TVSHOW, MUSIC, EPISODE, CHANNEL, CHANNEL_CAT = 0, 1, 2, 7, 17, 19
BASE_HEADERS = {"x-apisignatures": "543aba07839",
                "User-Agent": "Jiotv+ Kodi", "devicetype": "tv", "os": "Android", "x-multilang": "true", "AppName": "Jiotv+", "deviceId": "d40ce1e81fe914ee", "appkey": "2ccce09e59153fc9"}
CONTENT_TYPE = {MOVIE: "movies", TVSHOW: "tvshows",
                EPISODE: "episodes", MUSIC: "musicvideos"}
MEDIA_TYPE = {MOVIE: "movie", TVSHOW: "tvshow",
              TVSHOW: "season", EPISODE: "episode", MUSIC: "musicvideo"}

url_constructor = urljoin_partial(API_BASE_URL)

CHANNELS_FILTER = {1141: 160, 1127: 931, 1143: 367, 1121: 336, 300243: 370, 1126: 317,
                   300236: 758, 300242: 759, 1125: 156, 1116: 158, 1142: 159, 300222: 502, 300223: 497}
