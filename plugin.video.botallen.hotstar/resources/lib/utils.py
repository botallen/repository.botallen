from functools import wraps
from codequick import Script
from xbmc import executebuiltin
from codequick.storage import PersistentDict


def isLoggedIn(func):
    """
    Decorator to ensure that a valid login is present when calling a method
    """
    @wraps(func)
    def login_wrapper(*args, **kwargs):
        with PersistentDict("userdata.pickle") as db:
            token = db.get("token")
        if token:
            return func(*args, **kwargs)
        else:
            # login require
            Script.notify("Login Error", "Please login to use this add-on")
            executebuiltin(
                "RunPlugin(plugin://plugin.video.botallen.hotstar/resources/lib/main/login/)")
            return False
    return login_wrapper
