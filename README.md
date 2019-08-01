# CAF wiki tag parser

Parse Qualcomm wiki page for android release tags and manifests.
Can update a json file for every soc and android_version

## Configuration
see settings.py

## Examples :

* Update tags file with latest android 9.0 release for sdm660_64
  __python caf-tag-parser.py -s sdm660_64 -a 09.00.00 -u__
* Print tags file
  __python caf-tag-parser.py -f__
* Print 4 last android 9.0 releases for sdm660_64
  __python caf-tag-parser.py -s sdm660_64 -a 09.00.00 -n4 -p__
