# Welcome to your addon

1. You might want to move this folder into the kodi addon folder for convinience when debugging. It might also be needed to be `enabled` inside of the kodi addon browser.
2. Now start coding! Just open up the `.py` file in this folder and create what you would like Kodi to do! If you're creating a plugin, please check out [this kodi routing framework](https://github.com/tamland/kodi-plugin-routing) and copy a version of that module to your kodi addon folder.
3. Write some tests, maybe? Don't forget to activate [travis](https://travis-ci.org/) access to your repository. We've created a test folder and a travis config file for that, otherwise just delete those ;)
4. You might want to look at your `addon.xml` it should already be filled, but you will need to understand what your doing and might want to fill in some more info. So read up [here](http://kodi.wiki/view/Addon.xml).
5. Do you want some settings for your addon? Check the `settings.xml` in the resources folder. And read up [here](http://kodi.wiki/view/Settings.xml).
6. Read [this info](http://kodi.wiki/view/Add-on_structure#icon.png) and drop an icon for your addon into the `resource` folder and name it `icon.png`.
7. Read [this](http://kodi.wiki/view/Add-on_structure#fanart.jpg) and drop a addon background into the `resource` folder and name it `fanart.jpg`.
8. End up with a beautiful Kodi addon! Good for you :) Maybe you want to [share it with us](http://kodi.wiki/view/Submitting_Add-on_updates_on_Github)?

### Debugging
To get the debug logging to work, just set the global kodi logging to true and the debug logging in your addons settings.