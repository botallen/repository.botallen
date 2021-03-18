""" addons.xml generator """

import os
import gzip
import requests
import hashlib

GITHUB_USERNAME = "botallen"
ADDONS = [
    "plugin.video.botallen.hotstar"
]


class Generator:
    """
        Generates a new addons.xml file from each addons addon.xml file
        and a new addons.xml.md5 hash file. Must be run from the root of
        the checked-out repo. Only handles single depth folder structure.
    """

    def __init__(self):
        # generate files
        self._generate_addons_file()
        self._generate_md5_file()
        # notify user
        print("Finished updating addons xml and md5 files")

    def _generate_addons_file(self):
        global ADDONS, GITHUB_USERNAME
        # final addons text
        addons_xml = u"<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>\n<addons>\n"
        # loop thru and add each addons addon.xml file
        for addon in ADDONS:
            print(addon)
            resp = requests.get(
                f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{addon}/main/addon.xml")
            if resp.status_code != 200:
                print(f"Invalid status code: {addon} - {resp.status_code}")
                continue
            # split lines for stripping
            xml_lines = resp.text.splitlines()
            # new addon
            addon_xml = ""
            # loop thru cleaning each line
            for line in xml_lines:
                # skip encoding format line
                if (line.find("<?xml") >= 0):
                    continue
                # add line
                addon_xml += line.rstrip() + "\n"
            # we succeeded so add to our final addons.xml text
            addons_xml += addon_xml.rstrip() + "\n\n"
            # except Exception as e:
            #     # missing or poorly formatted addon.xml
            #     print(f"Excluding {_path} for {e}")
        # clean and add closing tag
        addons_xml = addons_xml.strip() + u"\n</addons>\n"
        # save file
        self._save_file(addons_xml, file="addons.xml")
        with gzip.open("addons.xml.gz", "wb") as f:
            f.write(bytes(addons_xml, encoding="utf-8"))

    def _generate_md5_file(self):
        try:
            # create a new md5 hash
            md5 = hashlib.md5()
            with open("addons.xml.gz", 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    md5.update(chunk)
            # save file
            self._save_file(md5.hexdigest(), file="addons.xml.gz.md5")
        except Exception as e:
            # oops
            print(f"An error occurred creating addons.xml.gz.md5 file!\n{e}")

    def _save_file(self, data, file):
        try:
            # write data to the file
            open(file, "w").write(data)
        except Exception as e:
            # oops
            print(f"An error occurred saving {file} file!\n{e}")


if (__name__ == "__main__"):
    # start
    Generator()
