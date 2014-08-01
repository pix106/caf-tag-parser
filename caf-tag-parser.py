import urllib.request
import urllib.response

from xml.dom.minidom import parseString


class CodeauroraReleaseParser:
    user_agent = ("Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) "
                  "AppleWebKit/525.13 (KHTML,     like Gecko)"
                  "Chrome/0.2.149.29 Safari/525.13")
    __releases = []

    def __init__(self, url, soc, version_tag):
        self.__url = url
        self.__soc = soc
        self.__version_tag = version_tag

        # Request the html.
        request = urllib.request.Request(url)
        request.add_header("User-Agent", self.user_agent)
        try:
            response = urllib.request.urlopen(request)
        except:
            print("Error: Invalid URL. Exiting.")
            exit()

        htmlContent = response.read().decode("utf8")
        self.__parseContent(htmlContent)

    @property
    def url(self):
        return self.__url

    @property
    def soc(self):
        return self.__soc

    @property
    def version_tag(self):
        return self.__version_tag

    @property
    def releases(self):
        return self.__releases

    def __parseContent(self, html):
        dom = parseString(html)
        rows = dom.getElementsByTagName("tr")
        # parse rows for release tags and skip table header
        for row in rows[1:]:
            for col in row.childNodes:
                print(col)


if __name__ == '__main__':

    url = 'https://www.codeaurora.org/xwiki/bin/QAEP/release'
    soc = 'msm8974'
    version = '04.04.04'

    parser = CodeauroraReleaseParser(url, soc, version)
    for r in parser.releases:
        print(r)