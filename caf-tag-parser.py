import urllib.request
import urllib.response

from bs4 import BeautifulSoup


class CodeauroraReleaseParser:
    user_agent = ("Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) "
                  "AppleWebKit/525.13 (KHTML,     like Gecko)"
                  "Chrome/0.2.149.29 Safari/525.13")
    __releases = []

    def __init__(self, url):
        response = None

        request = urllib.request.Request(url)
        request.add_header("User-Agent", self.user_agent)
        # noinspection PyBroadException
        try:
            response = urllib.request.urlopen(request)
        except:
            print("Error: Invalid URL. Exiting.")
            exit()
        html_content = response.read().decode("utf8")
        self.__parse_content(html_content)

    @property
    def releases(self):
        return self.__releases

    def __parse_content(self, html):
        soup = BeautifulSoup(html)
        table = soup.find("table")
        for row in table.findAll('tr')[1:]:
            col = row.findAll('td')
            date = col[0].get_text(strip=True)
            tag = col[1].get_text(strip=True)
            chipset = col[2].get_text(strip=True)
            manifest = col[3].get_text(strip=True)
            version = col[4].get_text(strip=True)

            self.releases.append((date, chipset, version, tag, manifest))


if __name__ == '__main__':
    url = 'https://www.codeaurora.org/xwiki/bin/QAEP/release'
    soc = 'msm8974'
    android_version = '04.04.04'

    parser = CodeauroraReleaseParser(url)
    releases = parser.releases

    def filter_soc(l, chipset):
        return [e for e in l if e[1] == chipset]

    def filter_version(l, version):
        return [e for e in l if e[2] == version]

    def filter_date(l, date_str):
        return [e for e in l if e[0] == date_str]

    rels = filter_version(filter_soc(releases, soc), android_version)

    print(rels[0])
