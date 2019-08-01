# CAF wiki tag parser

Parse Qualcomm wiki page for android release tags and manifests.
Can update a json file for every soc and android_version

## Configuration
In settings.py :
* url
* releases_file_name
* user_agent

## Examples :

* Update tags file with latest android 9.0 release for sdm660_64
  * _python caf-tag-parser.py -s sdm660_64 -a 09.00.00 -u_
* Print tags file
  * _python caf-tag-parser.py -f_
* Print 4 last android 9.0 releases for sdm660_64
  * _python caf-tag-parser.py -s sdm660_64 -a 09.00.00 -n4 -p_
