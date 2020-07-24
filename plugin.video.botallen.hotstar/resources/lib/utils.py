from functools import wraps
from codequick import Script
from xbmc import executebuiltin
from codequick.storage import PersistentDict
from .contants import url_constructor
import urlquick
from uuid import uuid4


def deep_get(dictionary, keys, default=None):
    return reduce(lambda d, key: d.get(key, default) if isinstance(d, dict) else default, keys.split("."), dictionary)


def isLoggedIn(func):
    """
    Decorator to ensure that a valid login is present when calling a method
    """
    @wraps(func)
    def login_wrapper(*args, **kwargs):
        with PersistentDict("userdata.pickle") as db:
            if db.get("token"):
                return func(*args, **kwargs)
            elif db.get("isGuest") is None:
                db["token"] = guestToken()
                db["isGuest"] = True
                db.flush()
                return func(*args, **kwargs)
            else:
                # login require
                Script.notify(
                    "Login Error", "Please login to watch this content")
                executebuiltin(
                    "RunPlugin(plugin://plugin.video.botallen.hotstar/resources/lib/main/login/)")
                return False
    return login_wrapper


def guestToken():
    resp = urlquick.post(url_constructor("/in/aadhar/v2/firetv/in/user/guest-signup"), json={
        "idType": "device",
        "id": str(uuid4()),
    }).json()
    return deep_get(resp, "description.userIdentity")
