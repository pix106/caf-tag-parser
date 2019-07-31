import urllib.request
import urllib.response
from bs4 import BeautifulSoup
import argparse
import json

from settings import default_config, releases_file_name

class caf_release:

    def __init__(self, date, tag, soc, manifest, android_version):
       self.date = date
       self.tag = tag
       self.soc = soc
       self.manifest = manifest
       self.android_version = android_version

    def as_dict(self):
       return {'tag': self.tag,
               'date': self.date,
               'soc': self.soc,
               'manifest': self.manifest,
               'android_version': self.android_version,
              }

    def as_dict_minimal(self):
       return {'tag': self.tag,
               'date': self.date,
              } 

    def as_section(self):
        lines = []
        release_dict = self.as_dict()
        for key in release_dict.keys():
            lines.append("%s : %s" % (key, release_dict.get(key,"")))
        return "%s%s%s" % ("\n", "\n".join(lines), "\n")

    def __str__(self):
        return self.as_section()

class CodeauroraReleaseParser:
    __releases = []

    def __init__(self, user_config={}):
        # use optional user_config to override default_config
        self.config = default_config
        self.config.update(user_config)

    @property
    def releases(self):
        return self.__releases

    def __parse_content(self, html):
        soup = BeautifulSoup(html, features='html.parser')
        table = soup.find("table")
        for row in table.findAll('tr')[1:]:
            col = row.findAll('td')
            date = col[0].get_text(strip=True)
            tag = col[1].get_text(strip=True)
            soc = col[2].get_text(strip=True)
            manifest = col[3].get_text(strip=True)
            android_version = col[4].get_text(strip=True)

            # WORKAROUND : bad android version 09.01.00
            if android_version == "09.01.00":
                android_version = "09.00.00"

            self.__releases.append(caf_release(date, tag, soc, manifest, android_version))

    def get_releases(self):
        request = urllib.request.Request(self.config.get('url'))
        request.add_header("User-Agent", self.config.get('user_agent'))
        # noinspection PyBroadException
        try:
            response = urllib.request.urlopen(request)
        except:
            response = None
            print("Error: Invalid URL. Exiting.")
            exit()
        html_content = response.read().decode("utf8")
        self.__parse_content(html_content)

    def filter_releases(self, soc=None, android_version=None):
        filtered_releases = []
        for release in self.releases:
            if soc or android_version:
                if (soc and android_version and release.soc == soc and release.android_version == android_version) \
                or (soc and not android_version and release.soc == soc) \
                or (not soc and android_version and release.android_version == android_versino):
                    filtered_releases.append(release)
            else:
                filtered_releases = self.releases

        return filtered_releases

    def print_releases(self, soc, android_version, number=None):
        releases = caf_parser.filter_releases(soc, android_version)
        if number:
            display_releases = releases[:number]
        else:
            display_releases = releases
        for release in releases:
            print(release)

    def get_releases_from_file(self):
        with open(releases_file_name, 'a+') as json_file:
            try:
                releases = json.load(json_file)
            except ValueError:
                releases = {}
        return releases

    def write_releases_to_file(self, releases):
        with open(releases_file_name, 'w') as json_file:
            json.dump(releases, json_file, indent=4, sort_keys=True)

    def update_releases_file(self, soc, android_version):
        latest_releases = {}
        for release in self.filter_releases(soc, android_version):
            if release.soc in latest_releases:
                if not release.android_version in latest_releases[release.soc]:
                    latest_releases[release.soc][release.android_version] = release.as_dict_minimal()
            else:
                latest_releases[release.soc] = {}
                latest_releases[release.soc][release.android_version] = release.as_dict_minimal()

        # update releases file
        releases_file = self.get_releases_from_file()
        releases_file.update(latest_releases) 
        self.write_releases_to_file(releases_file)


if __name__ == '__main__':
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument("-s", "--soc", help="soc to filter", type=str)
    args_parser.add_argument("-a" , "--android_version", help="android version to filter", type=str)
    args_parser.add_argument("-n", "--number", help="show last [number] releases", type=int)
    args = args_parser.parse_args()

    caf_parser = CodeauroraReleaseParser()
    caf_parser.get_releases()
#    caf_parser.print_releases(args.soc, args.android_version, args.number)
    caf_parser.update_releases_file(args.soc, args.android_version)

