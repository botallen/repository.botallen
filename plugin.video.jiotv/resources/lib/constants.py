# -*- coding: utf-8 -*-
from codequick.utils import urljoin_partial
import os
from kodi_six import xbmc, xbmcaddon

ADDON = xbmcaddon.Addon()

# Urls
IMG_PUBLIC = "https://jioimages.cdn.jio.com/imagespublic/"
IMG_CATCHUP = "http://jiotv.catchup.cdn.jio.com/dare_images/images/"
IMG_CATCHUP_SHOWS = "http://jiotv.catchup.cdn.jio.com/dare_images/shows/"
PLAY_URL = "plugin://plugin.video.jiotv/resources/lib/main/play/?_pickle_="
PLAY_EX_URL = "plugin://plugin.video.jiotv/resources/lib/main/play_ex/?_pickle_="
FEATURED_SRC = "https://tv.media.jio.com/apis/v1.6/getdata/featurednew?start=0&limit=30&langId=6"
EXTRA_CHANNELS = os.path.join(xbmc.translatePath(
    ADDON.getAddonInfo("path")), "resources", "extra", "channels.json")
CHANNELS_SRC = "http://jiotv.data.cdn.jio.com/apis/v1.3/getMobileChannelList/get/?os=android&devicetype=phone&version=6.0.5"
GET_CHANNEL_URL = "https://tv.media.jio.com/apis/v1.4/getchannelurl/getchannelurl?langId=6&userLanguages=All"
CATCHUP_SRC = "http://jiotv.data.cdn.jio.com/apis/v1.3/getepg/get?offset={0}&channel_id={1}&langId=6"
M3U_SRC = os.path.join(xbmc.translatePath(
    ADDON.getAddonInfo("profile")), "playlist.m3u")
EPG_SRC = "https://kodi.botallen.com/tv/epg.xml"

# Configs
GENRE_CONFIG = [
    {
        "name": "News",
        "tvImg":  IMG_PUBLIC + "logos/langGen/news_1579517470920.jpg",
        "promoImg": IMG_PUBLIC + "logos/langGen/news_1579517470920.jpg",
    },
    {
        "name": "Music",
        "tvImg":  IMG_PUBLIC + "logos/langGen/Music_1579245819981.jpg",
        "promoImg": IMG_PUBLIC + "logos/langGen/Music_1579245819981.jpg",
    },
    {

        "name": "Sports",
        "tvImg":  IMG_PUBLIC + "logos/langGen/Sports_1579245819981.jpg",
        "promoImg": IMG_PUBLIC + "logos/langGen/Sports_1579245819981.jpg",

    },
    {

        "name": "Entertainment",
        "tvImg":  IMG_PUBLIC + "38/52/Entertainment_1584620980069_tv.jpg",
        "promoImg": IMG_PUBLIC + "logos/langGen/Entertainment_1579245819981.jpg",

    },
    {

        "name": "Devotional",
        "tvImg":  IMG_PUBLIC + "logos/langGen/devotional_1579517470920.jpg",
        "promoImg": IMG_PUBLIC + "logos/langGen/devotional_1579517470920.jpg",

    },
    {
        "name": "Movies",
        "tvImg":  IMG_PUBLIC + "logos/langGen/movies_1579517470920.jpg",
        "promoImg": IMG_PUBLIC + "logos/langGen/movies_1579517470920.jpg",

    },
    {
        "name": "Infotainment",
        "tvImg":  IMG_PUBLIC + "logos/langGen/infotainment_1579517470920.jpg",
        "promoImg": IMG_PUBLIC + "logos/langGen/infotainment_1579517470920.jpg",

    },
    {
        "name": "Business",
        "tvImg":  IMG_PUBLIC + "logos/langGen/business_1579517470920.jpg",
        "promoImg": IMG_PUBLIC + "logos/langGen/business_1579517470920.jpg",
    },
    {
        "name": "Kids",
        "tvImg":  IMG_PUBLIC + "logos/langGen/kids_1579517470920.jpg",
        "promoImg": IMG_PUBLIC + "logos/langGen/kids_1579517470920.jpg",
    },
    {
        "name": "Lifestyle",
        "tvImg":  IMG_PUBLIC + "logos/langGen/lifestyle_1579517470920.jpg",
        "promoImg": IMG_PUBLIC + "logos/langGen/lifestyle_1579517470920.jpg",
    },
    {
        "name": "Jio Darshan",
        "tvImg":  IMG_PUBLIC + "logos/langGen/jiodarshan_1579517470920.jpg",
        "promoImg": IMG_PUBLIC + "logos/langGen/jiodarshan_1579517470920.jpg",
    },
    {
        "name": "Shopping",
        "tvImg":  IMG_PUBLIC + "logos/langGen/shopping_1579517470920.jpg",
        "promoImg": IMG_PUBLIC + "logos/langGen/shopping_1579517470920.jpg",
    },
    {
        "name": "Educational",
        "tvImg":  IMG_PUBLIC + "logos/langGen/educational_1579517470920.jpg",
        "promoImg": IMG_PUBLIC + "logos/langGen/educational_1579517470920.jpg",
    }
]
LANGUAGE_CONFIG = [
    {
        "name": "Hindi",
        "tvImg": IMG_PUBLIC + "logos/langGen/Hindi_1579245819981.jpg",
        "promoImg": IMG_PUBLIC+"98/98/Hindi_1580458058289_promo.jpg",
    },
    {
        "name": "English",
        "tvImg": IMG_PUBLIC + "logos/langGen/English_1579245819981.jpg",
        "promoImg": IMG_PUBLIC+"52/8/English_1580458071796_promo.jpg",
    },
    {
        "name": "Marathi",
        "tvImg": IMG_PUBLIC + "logos/langGen/Marathi_1579245819981.jpg",
        "promoImg": IMG_PUBLIC+"30/23/Marathi_1580458084801_promo.jpg",
    },
    {
        "name": "Telugu",
        "tvImg": IMG_PUBLIC + "logos/langGen/Telugu_1579245819981.jpg",
        "promoImg": IMG_PUBLIC+"89/86/Telugu_1580458096736_promo.jpg",
    },
    {
        "name": "Kannada",
        "tvImg": IMG_PUBLIC + "logos/langGen/Kannada_1579245819981.jpg",
        "promoImg": IMG_PUBLIC+"37/41/Kannada_1580458557594_promo.jpg",
    },
    {
        "name": "Tamil",
        "tvImg": IMG_PUBLIC + "logos/langGen/Tamil_1579245819981.jpg",
        "promoImg": IMG_PUBLIC+"58/79/Tamil_1580458708325_promo.jpg",
    },
    {
        "name": "Punjabi",
        "tvImg": IMG_PUBLIC + "logos/langGen/Punjabi_1579245819981.jpg",
        "promoImg": IMG_PUBLIC+"79/58/Punjabi_1580458722849_promo.jpg",
    },
    {
        "name": "Gujarati",
        "tvImg": IMG_PUBLIC + "logos/langGen/Gujarati_1579245819981.jpg",
        "promoImg": IMG_PUBLIC+"41/66/Gujarati_1580459392856_promo.jpg",
    },
    {
        "name": "Bengali",
        "tvImg": IMG_PUBLIC + "logos/langGen/Bengali_1579245819981.jpg",
        "promoImg": IMG_PUBLIC+"72/66/Bengali_1580459416363_promo.jpg",
    },
    {
        "name": "Bhojpuri",
        "tvImg": IMG_PUBLIC + "logos/langGen/Bhojpuri_1579245819981.jpg",
        "promoImg": IMG_PUBLIC+"87/70/Bhojpuri_1580459428665_promo.jpg",
    },
    {
        "name": "Malayalam",
        "tvImg": IMG_PUBLIC + "logos/langGen/Malayalam_1579245819981.jpg",
        "promoImg": IMG_PUBLIC+"67/0/Malayalam_1580459753008_promo.jpg",
    }
]
LANG_MAP = {6: "English", 1: "Hindi", 2: "Marathi", 3: "Punjabi", 4: "Urdu", 5: "Bengali", 7: "Malayalam", 8: "Tamil",
            9: "Gujarati", 10: "Odia", 11: "Telugu", 12: "Bhojpuri", 13: "Kannada", 14: "Assamese", 15: "Nepali", 16: "French"}
GENRE_MAP = {8: "Sports", 5: "Entertainment", 6: "Movies", 12: "News", 13: "Music", 7: "Kids", 9: "Lifestyle",
             10: "Infotainment", 15: "Devotional", 16: "Business", 17: "Educational", 18: "Shopping", 19: "JioDarshan"}
CONFIG = {"Genres": GENRE_CONFIG, "Languages": LANGUAGE_CONFIG}
