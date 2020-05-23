# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import urlquick
import json
from uuid import uuid4
from functools import wraps
from distutils.version import LooseVersion
from codequick import Script
from codequick.script import Settings
from codequick.storage import PersistentDict
from xbmc import executebuiltin
from xbmcgui import Dialog


def isLoggedIn(func):
    """
    Decorator to ensure that a valid login is present when calling a method
    """
    @wraps(func)
    def login_wrapper(*args, **kwargs):

        with PersistentDict("creds") as db:
            username = db.get("username")
            password = db.get("password")

        # token is 5 days old ?
        with PersistentDict("headers") as db:
            headers = db.get("headers")
        if headers:
            return func(*args, **kwargs)
        elif username and password:
            login(username, password)
            return func(*args, **kwargs)
        else:
            Script.notify(
                'Login Error', 'You need to login with Jio Username and password to use this add-on')
            executebuiltin(
                "RunPlugin(plugin://plugin.video.jiotv/resources/lib/main/login/)")
            return False
    return login_wrapper


def login(username, password):
    body = {"identifier": username if '@' in username else "+91"+username, "password": password, "rememberUser": "T", "upgradeAuth": "Y", "returnSessionDetails": "T",
            "deviceInfo": {"consumptionDeviceName": "Jio", "info": {"type": "android", "platform": {"name": "vbox86p", "version": "8.0.0"}, "androidId": "6fcadeb7b4b10d77"}}}
    resp = urlquick.post(
        "https://api.jio.com/v3/dip/user/unpw/verify", headers={"x-api-key": "l7xx938b6684ee9e4bbe8831a9a682b8e19f"}, json=body, verify=False)
    if resp.status_code == 200 and resp.json()['ssoToken']:
        data = resp.json()
        _CREDS = {"ssotoken": data['ssoToken'], "userId": data['sessionAttributes']['user']['uid'],
                  "uniqueId": data['sessionAttributes']['user']['unique'], "crmid": data['sessionAttributes']['user']['subscriberId']}
        headers = {
            "User-Agent": "JioTV Kodi",
            "os": "Kodi",
            "deviceId": str(uuid4()),
            "versionCode": "226",
            "devicetype": "Kodi",
            "srno": "200206173037",
            "appkey": "NzNiMDhlYzQyNjJm",
            "channelid": "100",
            "usergroup": "tvYR7NSNn7rymo3F",
            "lbcookie": "1"
        }
        headers.update(_CREDS)
        with PersistentDict("headers", ttl=432000) as db:
            db["headers"] = headers
    else:
        Script.notify('Login Failed', 'Invalid credentials')


def logout():
    with PersistentDict("headers") as db:
        del db["headers"]


def getHeaders():
    with PersistentDict("headers") as db:
        return db.get("headers", False)


def check_addon(addonid, minVersion=False):
    """Checks if selected add-on is installed."""
    try:
        curVersion = Script.get_info("version", addonid)
        if minVersion and LooseVersion(curVersion) < LooseVersion(minVersion):
            Script.log('{addon} {curVersion} doesn\'t setisfy required version {minVersion}.'.format(
                addon=addonid, curVersion=curVersion, minVersion=minVersion))
            Dialog().ok("Error", "{minVersion} version of {addon} is required to play this content.".format(
                addon=addonid, minVersion=minVersion))
            return False
        return True
    except RuntimeError:
        Script.log('{addon} is not installed.'.format(addon=addonid))
        if not _install_addon(addonid):
            # inputstream is missing on system
            Dialog().ok("Error",
                        "[B]{addon}[/B] is missing on your Kodi install. This add-on is required to play this content.".format(addon=addonid))
            return False
        return True


def _install_addon(addonid):
    """Install addon."""
    try:
        # See if there's an installed repo that has it
        executebuiltin('InstallAddon({})'.format(addonid), wait=True)

        # Check if add-on exists!
        version = Script.get_info("version", addonid)

        Script.log(
            '{addon} {version} add-on installed from repo.'.format(addon=addonid, version=version))
        return True
    except RuntimeError:
        Script.log('{addon} add-on not installed.'.format(addon=addonid))
        return False
