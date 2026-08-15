#!/usr/bin/env python3
"""
Rebuild Kings_One_EPG_MASTER.xml.gz from the user's Open-EPG feed.

The channel mapping below translates Open-EPG channel IDs into the Kings IDs/names
that were tested successfully in TiviMate. The Open-EPG URL is supplied through
the OPEN_EPG_URL environment variable so it does not need to be stored publicly.
"""

import os
import io
import gzip
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

OPEN_EPG_URL = os.environ["OPEN_EPG_URL"]
OUTPUT = Path("Kings_One_EPG_MASTER.xml.gz")

CHANNEL_MAP = {
    'ABC.us': 'NY | New York | ABC (WABC)',
    'AMC.us': 'amc.us',
    'Action MAX.us': 'actionmaxpacific.us',
    'BET Her.us': 'bether.us',
    'Big Ten Network.us': 'bigtennetwork.us',
    'Boomerang.us': 'boomerang.us',
    'Bravo.us': 'bravo.us',
    'CBS.us': 'NY | New York | CBS (WCBS)',
    'CMT.us': 'cmt.us',
    'CNBC.us': 'cnbc.us',
    'CNN.us': 'cnn.us',
    'Cartoon Network.us': 'cartoonnetwork.us',
    'Comedy Central.us': 'comedycentral.us',
    'Cooking Channel.us': 'cookingchannel.us',
    'Disney Channel.us': 'disneychannel.us',
    'Disney Junior.us': 'disneyjunior.us',
    'ESPN.us': 'espn.us',
    'ESPNU.us': 'espnu.us',
    'FOX.us': 'foxwnyw.us',
    'FX.us': 'fx.us',
    'FXX.us': 'fxx.us',
    'Food Network.us': 'foodnetwork.us',
    'Fox Business.us': 'foxbusiness.us',
    'Fox News.us': 'foxnews.us',
    'Fox Sports 1.us': 'foxsports1.us',
    'Fox Sports 2.us': 'foxsports2.us',
    'Freeform.us': 'freeform.us',
    'Fuse HDTV (East).us': 'fusetv.us',
    'GAC Family.us': 'gacfamily.us',
    'Game Show Network.us': 'gameshownetwork.us',
    'Golf Channel.us': 'golfchannel.us',
    'Grit.us': 'grit.us',
    'HBO Family.us': 'hbofamily.us',
    'HBO Signature.us': 'hbosignature.us',
    'HBO Zone.us': 'hbozone.us',
    'HBO2.us': 'hbo2.us',
    'HDNet Movies.us': 'hdnetmovies.us',
    'HGTV.us': 'hgtv.us',
    'Hallmark Channel.us': 'hallmark.us',
    'Hallmark Family.us': 'hallmarkfamily.us',
    'Hallmark Mystery.us': 'hallmarkmoviesmysteries.us',
    'IFC HDTV (East).us': 'independentfilmchannel.us',
    'MGM+ HD.us': 'epix.us',
    'MGM+ Hits HD.us': 'epixhits.us',
    'MGM+ Marquee HD.us': 'epix2.us',
    'More MAX.us': 'moremax.us',
    'MoviePlex.us': 'movieplex.us',
    'NBC.us': 'NY | New York | NBC (WNBC)',
    'NFL RedZone HD.us': 'USA: NFL REDZONE',
    'NewsNation.us': 'newsnation.us',
    'Oxygen.us': 'oxygen.us',
    'Paramount Network HDTV (East).us': 'paramountnetwork.us',
    'Pop TV.us': 'poptv.us',
    'Reelz.us': 'reelzchannel.us',
    'SEC Network.us': 'secnetwork.us',
    'Showtime 2.us': 'showtime2.us',
    'Showtime Extreme.us': 'showtimeextreme.us',
    'Showtime FamilyZone.us': 'showtimefamilyzone.us',
    'Showtime Next - Pacific (76).us': 'showtimenext.us',
    'Showtime Women - Pacific (78).us': 'showtimewomen.us',
    'Showtime.us': 'showtime.us',
    'Starz Cinema.us': 'starzcinema.us',
    'Starz Edge.us': 'starzedge.us',
    'Starz Encore Black.us': 'starzencoreblack.us',
    'Starz Encore Westerns.us': 'starzencorewesterns.us',
    'Starz In Black.us': 'starzinblack.us',
    'TBS.us': 'tbs.us',
    'TNT.us': 'tntpacific.us',
    'TV Land.us': 'tvlandeast.us',
    'The Weather Channel.us': 'weatherchannel.us',
    'UPtv.us': 'uptv.us',
    'USA Network.us': 'usanetwork.us',
    'VH1.us': 'vh1.us',
    'truTV.us': 'trutv.us'
}

def download(url: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Kings-EPG-Updater/1.0"}
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read()

def decode_epg(data: bytes) -> bytes:
    # Open-EPG normally returns .xml.gz. This also tolerates plain XML.
    if data[:2] == b"\x1f\x8b":
        return gzip.decompress(data)
    return data

def main() -> None:
    xml_bytes = decode_epg(download(OPEN_EPG_URL))
    src_root = ET.fromstring(xml_bytes)

    channels = {c.attrib.get("id"): c for c in src_root.findall("channel")}
    programmes = src_root.findall("programme")

    out_root = ET.Element("tv", src_root.attrib)
    used_targets = set()
    active_map = {}

    for source_id, target_id in CHANNEL_MAP.items():
        ch = channels.get(source_id)
        if ch is None or target_id in used_targets:
            continue
        used_targets.add(target_id)
        active_map[source_id] = target_id

        # Copy the channel and replace only its XMLTV ID with the Kings-compatible ID.
        new_ch = ET.fromstring(ET.tostring(ch, encoding="utf-8"))
        new_ch.attrib["id"] = target_id
        out_root.append(new_ch)

    for programme in programmes:
        source_id = programme.attrib.get("channel")
        target_id = active_map.get(source_id)
        if not target_id:
            continue
        new_programme = ET.fromstring(ET.tostring(programme, encoding="utf-8"))
        new_programme.attrib["channel"] = target_id
        out_root.append(new_programme)

    buf = io.BytesIO()
    ET.ElementTree(out_root).write(buf, encoding="utf-8", xml_declaration=True)

    with gzip.open(OUTPUT, "wb", compresslevel=9) as gz:
        gz.write(buf.getvalue())

    print(f"Mapped {len(active_map)} channels and wrote {OUTPUT}")

if __name__ == "__main__":
    main()
