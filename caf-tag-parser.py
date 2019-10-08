import urllib.request
import urllib.response
from bs4 import BeautifulSoup
import argparse
import json

from colorama import Fore, Back, Style

from settings import config


class CafRelease:

    def __init__(self, date, tag, soc, manifest, android_version):
        self.date = date
        self.tag = tag
        self.soc = soc
        self.manifest = manifest
        self.android_version = android_version

    def version(self):
        return int(self.tag.split("-")[1])

    def as_dict(self):
        return {'tag': self.tag,
                'date': self.date,
                'soc': self.soc,
                'android_version': self.android_version,
                'manifest': self.manifest,
                }

    def __str__(self):
        return "\n".join(["%s %s" % (key, value) for key, value in self.as_dict().items()])


class CodeauroraReleaseParser:

    def __init__(self):

        self.url = config.get('url')
        self.user_agent = config.get('user_agent')
        self.releases = self.get_releases()

    def parse_content(self, html):
        print("=== Parsing CAF releases")
        releases = []
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

            releases.append(CafRelease(date, tag, soc, manifest, android_version))
        return releases

    def get_releases(self):
        print("=== Downloading CAF releases from %s ..." % self.url)
        request = urllib.request.Request(self.url)
        request.add_header("User-Agent", self.user_agent)
        try:
            response = urllib.request.urlopen(request)
        except:
            response = None
            print("Error: Invalid URL. Exiting.")
            exit()
        html_content = response.read().decode("utf8")
        return self.parse_content(html_content)

    def filter_releases(self, soc=None, android_version=None, number=None):
        if soc and android_version:
            filtered_releases = [release for release in self.releases
                                 if release.soc == soc and release.android_version == android_version]
        elif soc or android_version:
            if soc:
                filtered_releases = [release for release in self.releases
                                     if release.soc == soc]

            elif android_version:
                filtered_releases = [release for release in self.releases
                                     if release.sandroid_versionoc == android_version]
        else:
            filtered_releases = self.releases

        if filtered_releases and number:
            filtered_releases = filtered_releases[:number]
        return filtered_releases

    def print_releases(self, soc=None, android_version=None, number=None):
        releases = self.filter_releases(soc, android_version, number)
        releases.reverse()

        print("== Found %d releases" % len(releases))
        separator = "---------------------------------------"
        for release in releases:
            print(release)
            print(separator)

    def get_latest_releases(self, soc, android_version, number=None):
        filtered_releases = self.filter_releases(soc, android_version, number)
        latest_parsed_releases = {}
        latest_releases = []
        for release in filtered_releases:
            if release.soc not in latest_parsed_releases:
                latest_parsed_releases[release.soc] = {}
            if release.android_version not in latest_parsed_releases[release.soc]:
                latest_parsed_releases[release.soc][release.android_version] = release.tag
                latest_releases.append(release)
        return latest_releases

    def get_latest_release(self, soc, android_version):
        latest_releases = self.get_latest_releases(soc, android_version, 1)
        if latest_releases:
            latest_release = latest_releases[0]
        else:
            latest_release = None
        return latest_release


class CafReleasesFile:

    def __init__(self, args):
        self.releases_file = config['releases_file_name']

    def get_tags(self):
        releases = {}
        try:
            with open(self.releases_file, 'r') as json_file:
                try:
                    releases = json.load(json_file)
                except ValueError:
                    print("Empty or invalid file")
        except FileNotFoundError:
            pass
        return releases

    def get_tag(self, soc, android_version):
        file_tags = self.get_tags()
        try:
            file_tag = file_tags[soc][android_version]
        except:
            file_tag = None
        return file_tag

    def get_version(self, soc, android_version):
        file_tag = self.get_tag(soc, android_version)
        if file_tag:
            file_version = int(file_tag.split("-")[1])
        else:
            file_version = 0
        return file_version

    def write_releases(self, releases):
        with open(self.releases_file, 'w+') as json_file:
            json.dump(releases, json_file, indent=4, sort_keys=True)

    def write_tag(self, soc, android_version, tag):
        file_releases = self.get_tags()

        if soc not in file_releases:
            file_releases[soc] = {}
        file_releases[soc][android_version] = tag
        self.write_releases(file_releases)

    def print_releases(self):
        print(json.dumps(self.get_tags(), indent=4))

    def update_tag(self, parser, soc, android_version):
        latest_release = parser.get_latest_release(soc, android_version)
        current_tag = self.get_tag(soc, android_version)
        file_current_version = self.get_version(soc, android_version)

        print("%s - Android %s - %s" % (soc, android_version, current_tag))
        if latest_release.version() > file_current_version:
            print(Style.BRIGHT + "  => UPDATED TAG : %s" % latest_release.tag + Style.RESET_ALL)
            self.write_tag(soc, android_version, latest_release.tag)

    def update_tags(self, parser, soc=None, android_version=None):
        latest_releases = parser.get_latest_releases(soc, android_version)
        for release in latest_releases:
            self.update_tag(parser, release.soc, release.android_version)

    def update_file_tags(self, parser):
        tags = self.get_tags()
        for soc in tags.keys():
            for android_version in tags[soc].keys():
                self.update_tag(parser, soc, android_version)


if __name__ == '__main__':
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument("-s", "--soc", help="soc to filter", type=str, default=None)
    args_parser.add_argument("-a", "--android_version", help="android version to filter", type=str, default=None)
    args_parser.add_argument("-n", "--number", help="show last [number] releases", type=int)
    args_parser.add_argument("-p", "--print_releases", help="prints online tags releases", action="store_true")
    args_parser.add_argument("-f", "--print_file", help="prints tags file", action="store_true")
    args_parser.add_argument("-x", "--update_tags", help="update tags file", action="store_true")
    args_parser.add_argument("-u", "--update_file_tags", help="update tags file", action="store_true")
    args = args_parser.parse_args()

    # file
    caf_file = CafReleasesFile(args)
    if args.print_file:
        caf_file.print_releases()
        exit

    # from now on, we need a CodeauroraReleaseParser instance
    else:
        caf_parser = CodeauroraReleaseParser()
        if args.print_releases:
            caf_parser.print_releases(args.soc, args.android_version, args.number)

        if args.update_file_tags:
            caf_file.update_file_tags(caf_parser)

        if args.update_tags:
            caf_file.update_tags(caf_parser, args.soc, args.android_version)
