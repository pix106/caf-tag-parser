import urllib.request
import urllib.response
from bs4 import BeautifulSoup
import argparse
import json

from settings import config


class CafRelease:

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
                'android_version': self.android_version,
                'manifest': self.manifest,
                }

    def __str__(self):
        return "\n".join(["%s %s" % (key, value) for key, value in self.as_dict().items()])


class CodeauroraReleaseParser:
    __releases = []

    def __init__(self, args):

        if args.print_file:
            self.print_releases_file()
            exit()

        if not (args.soc and args.android_version):
            print("Missing soc and/or android_version")
            exit()

        # get releases
        self.get_releases()

        if args.print_releases:
            self.print_releases(args.soc, args.android_version, args.number)

        if args.update_file:
            self.update_releases_file(args.soc, args.android_version)

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

            self.__releases.append(CafRelease(date, tag, soc, manifest, android_version))

    def get_releases(self):
        print("=== Updating CAF releases...")

        request = urllib.request.Request(config.get('url'))
        request.add_header("User-Agent", config.get('user_agent'))
        try:
            response = urllib.request.urlopen(request)
        except:
            response = None
            print("Error: Invalid URL. Exiting.")
            exit()
        html_content = response.read().decode("utf8")
        self.__parse_content(html_content)

    def filter_releases(self, soc, android_version):
        print("=== Filtering : soc=%s android_version=%s" % (soc, android_version))
        return [release for release in self.releases if release.soc == soc and release.android_version == android_version]

    def print_releases(self, soc, android_version, number=None):
        releases = self.filter_releases(soc, android_version)
        if number:
            print("=== Last %s releases" % number)
            display_releases = releases[:number]
        else:
            display_releases = releases

        print("---------------------------------------")
        for release in display_releases:
            print(release)
            print("---------------------------------------")

    def get_latest_releases(self, soc, android_version):
        latest_releases = {}
        filtered_releases = self.filter_releases(soc, android_version)

        for release in filtered_releases:
            if release.soc not in latest_releases:
                latest_releases[release.soc] = {}
            if release.android_version not in latest_releases[release.soc]:
                latest_releases[release.soc][release.android_version] = release.tag

        return latest_releases

    @staticmethod
    def get_releases_from_file():
        releases = {}
        try:
            with open(config['releases_file_name'], 'r') as json_file:
                try:
                    releases = json.load(json_file)
                except ValueError:
                    print("Empty or invalid file")
        except FileNotFoundError:
            print("Error opening %s" % config['releases_file_name'])
        return releases

    @staticmethod
    def print_releases_file():
        print(json.dumps(CodeauroraReleaseParser.get_releases_from_file()))

    @staticmethod
    def write_releases_to_file(releases):
        with open(config['releases_file_name'], 'w') as json_file:
            json.dump(releases, json_file, indent=4, sort_keys=True)

    def update_releases_file(self, soc, android_version):
        file_releases = self.get_releases_from_file()
        latest_releases = self.get_latest_releases(soc, android_version)

        print("=== Updating latest releases in %s" % config['releases_file_name'])

        # update file with latest releases
        for soc, android_versions in latest_releases.items():
            if soc not in file_releases:
                print("Adding %s" % soc)
                file_releases[soc] = {}
            for android_version, tag in android_versions.items():
                if android_version not in file_releases[soc]:
                    file_releases[soc][android_version] = ""
                if tag != file_releases[soc][android_version]:
                    print("Updating %s : %s" % (soc, android_version))
                    file_releases[soc][android_version] = tag

        # write file
        self.write_releases_to_file(file_releases)


if __name__ == '__main__':
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument("-s", "--soc", help="soc to filter", type=str)
    args_parser.add_argument("-a", "--android_version", help="android version to filter", type=str)
    args_parser.add_argument("-n", "--number", help="show last [number] releases", type=int)
    args_parser.add_argument("-p", "--print_releases", help="prints online tags releases", action="store_true")
    args_parser.add_argument("-f", "--print_file", help="prints tags file", action="store_true")
    args_parser.add_argument("-u", "--update_file", help="update tags file", action="store_true")
    cli_args = args_parser.parse_args()

    caf_parser = CodeauroraReleaseParser(cli_args)
