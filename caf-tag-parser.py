from operator import attrgetter
import lxml.html as lh
import requests

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
        self.manifest_url = config['manifest_url'].replace("MANIFEST", manifest).replace("TAG", tag)
        self.android_version = android_version

    def as_dict(self):
        return {'tag': self.tag,
                'date': self.date,
                'soc': self.soc,
                'android_version': self.android_version,
                'manifest': self.manifest,
                'manifest_url': self.manifest_url,
                }

    def __str__(self):
        return "\n".join(["%s %s" % (key, value) for key, value in self.as_dict().items()])


class CodeauroraReleaseParser:

    def __init__(self):
        self.url = config.get('url')
        self.releases = self.get_releases()

    def get_releases(self):
        print("=== Downloading CAF releases from %s ..." % self.url)
        html = requests.get(self.url)
        print("=== Parsing CAF releases")
        releases = []
        doc = lh.fromstring(html.content)
        tr_elements = doc.xpath('//tr')
        for row in tr_elements[1:]:
            date = row[0].text_content().strip()
            tag = row[1].text_content().strip()
            soc = row[2].text_content().strip()
            manifest = row[2].text_content().strip()
            android_version = row[4].text_content().strip()
            # WORKAROUND : bad android version 09.01.00
            if android_version == "09.01.00":
                android_version = "09.00.00"

            # print("%s - %s : %s (%s)"%(soc, android_version, tag, date))
            releases.append(CafRelease(date, tag, soc, manifest, android_version))

        return releases

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
                                     if release.android_version == android_version]
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

        print("%s - Android %s - %s" % (soc, android_version, current_tag))
        if latest_release:
            if latest_release.tag != current_tag:
                print(Style.BRIGHT + "  => UPDATED TAG : %s" % latest_release.tag + Style.RESET_ALL)
                self.write_tag(soc, android_version, latest_release.tag)

    def update_tags(self, parser, soc=None, android_version=None):
        latest_releases = parser.get_latest_releases(soc, android_version)

        # sort releases list
        if soc and not android_version:
            latest_releases.sort(key=attrgetter('android_version'))
        elif not soc and android_version:
            latest_releases.sort(key=attrgetter('soc'))
        elif soc and android_version:
            latest_releases.sort(key=attrgetter('soc', 'android_version'))

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
