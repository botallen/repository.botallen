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
            if db.get("token"):
                return func(*args, **kwargs)
            elif db.get("isGuest") is None:
                db["token"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJ1bV9hY2Nlc3MiLCJleHAiOjE1ODY3OTEzMzEsImlhdCI6MTU4NjcwNDkzMSwiaXNzIjoiVFMiLCJzdWIiOiJ7XCJjb3VudHJ5Q29kZVwiOlwiaW5cIixcImN1c3RvbWVyVHlwZVwiOlwibnVcIixcImRldmljZUlkXCI6XCI4OTUyYWE5ZS1mZGY5LTQ2ZTMtYjU2Mi1jNTViMzdjZTMyYTdcIixcImhJZFwiOlwiMDBkY2FkN2M4NmQ4NDJiNTgxYmU4Mjg4OTRjMWYyMzRcIixcImlwXCI6XCIxMDMuMjEyLjE0MS4yNFwiLFwiaXNFbWFpbFZlcmlmaWVkXCI6ZmFsc2UsXCJpc1Bob25lVmVyaWZpZWRcIjpmYWxzZSxcImlzc3VlZEF0XCI6MTU4NjcwNDkzMTUzMSxcIm5hbWVcIjpcIkd1ZXN0IFVzZXJcIixcInBJZFwiOlwiNTQ1ZmQzNmE1NWM4NGExNWFkOTE3OGNlYWFhZmI0YTBcIixcInByb2ZpbGVcIjpcIkFEVUxUXCIsXCJzdWJzY3JpcHRpb25zXCI6e1wiaW5cIjp7fX0sXCJ0eXBlXCI6XCJkZXZpY2VcIixcInZlcnNpb25cIjpcInYyXCJ9IiwidmVyc2lvbiI6IjFfMCJ9.X1uJowi4-4eVquBDdTis76pbH44gso1y16i5zKTwRfg"
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
