#!/usr/bin/env python
# coding: utf-8
# License: GPL v.3 <http://www.gnu.org/licenses/gpl-3.0.en.html>

"""
Create Kodi addons zip file
"""

from __future__ import print_function
import re
import os
# import argparse
import os.path
import zipfile


def clean_pyc(folder):
    cwd = os.getcwd()
    os.chdir(folder)
    paths = os.listdir(folder)
    for path in paths:
        abs_path = os.path.abspath(path)
        if os.path.isdir(abs_path):
            clean_pyc(abs_path)
        elif path[-4:] == '.pyc':
            print('deleting <%s>' % abs_path)
            os.remove(abs_path)
    os.chdir(cwd)


def create_zip(zip_name, root_dir, addon_name):
    clean_pyc(root_dir)
    print('%s cleaned.' % root_dir)

    with zipfile.ZipFile(zip_name, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        base_path = os.path.normpath(root_dir)
        print('Creating zip file...')
        for dirpath, dirnames, filenames in os.walk(root_dir):
            filenames = [f for f in filenames if not f[0] == '.']
            dirnames[:] = [d for d in dirnames if not d[0] == '.']
            for name in sorted(dirnames):
                path = os.path.normpath(os.path.join(dirpath, name))
                print("+ <%s>" % path)
                zf.write(path, os.path.join(
                    addon_name, os.path.relpath(path, base_path)))
            for name in filenames:
                path = os.path.normpath(os.path.join(dirpath, name))
                if os.path.isfile(path) and not path.endswith(".zip") and not path.endswith("deploy_addon.py"):
                    print("+ <%s>" % path)
                    zf.write(path, os.path.join(
                        addon_name, os.path.relpath(path, base_path)))

    print('ZIP created successfully.')


# Argument parsing
# parser = argparse.ArgumentParser(description='Creates an addon zip file')
# parser.add_argument('addon', nargs='?', help='addon ID',
#                     action='store', default='')
# args = parser.parse_args()

# # Define paths
# if not args.addon:
#     addon = os.environ['ADDON']
# else:
#     addon = args.addon

root_dir = os.path.dirname(os.path.abspath(__file__))
addon = root_dir.split(os.sep)[-1]
with open(os.path.join(root_dir, 'addon.xml'), 'rb') as addon_xml:
    version = re.search(r'(?<!xml )version="(.+?)"', addon_xml.read()).group(1)
zip_name = '{0}-{1}'.format(addon, version) + '.zip'

# Start working
os.chdir(root_dir)
create_zip(zip_name, root_dir, addon)
