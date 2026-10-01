#!/usr/bin/env python3
"""Refresh a podcast feed using ARD's published episode metadata."""
import json, os, re, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path

SOURCE = 'https://www.ardsounds.de/sendung/themen-des-tages/urn:ard:show:82cae2879831698e/'
SHOW = 'urn:ard:show:82cae2879831698e'
ROOT = Path(__file__).resolve().parent
DOCS = ROOT / 'docs'
ATOM = 'http://www.w3.org/2005/Atom'
ITUNES = 'http://www.itunes.com/dtds/podcast-1.0.dtd'
ET.register_namespace('atom', ATOM)
ET.register_namespace('itunes', ITUNES)

def request(url, method='GET'):
    return urllib.request.urlopen(urllib.request.Request(url, method=method, headers={'User-Agent': 'ThemenDesTagesRSS/1.0'}), timeout=5 if method == 'HEAD' else 40)

def main():
    with request(SOURCE) as response:
        html = response.read().decode('utf-8')
    match = re.search(r'<script\b[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if not match:
        raise RuntimeError('ARD page metadata missing; preserving existing feed')
    show = json.loads(match.group(1))['props']['pageProps']['initialData']['data']['result']
    if show['coreId'] != SHOW or show['title'] != 'Themen des Tages':
        raise RuntimeError('Unexpected show; preserving existing feed')
    nodes = show['items']['nodes']
    if not nodes:
        raise RuntimeError('No episodes returned; preserving existing feed')
    archive = ROOT / 'episodes.json'
    episodes = json.loads(archive.read_text()) if archive.exists() else {}
    for node in nodes:
        if node.get('programSet', {}).get('coreId') != SHOW:
            raise RuntimeError('Episode belongs to another show')
        audios = node.get('audios', [])
        audio = next((a for a in audios if a.get('allowDownload') and a.get('downloadUrl')), None)
        if not audio:
            audio = next((a for a in audios if a.get('url')), None)
        if not audio or not node.get('isPublished'):
            continue
        guid = node['coreId']
        url = audio.get('downloadUrl') or audio['url']
        old = episodes.get(guid, {})
        length = old.get('length', '0') if old.get('audio') == url else '0'
        if length == '0':
            try:
                with request(url, 'HEAD') as response:
                    length = response.headers.get('Content-Length', '0')
            except Exception:
                pass  # Unknown enclosure size is represented by zero.
        episodes[guid] = dict(title=node['title'], description=node.get('summary', ''),
            date=node['publishDate'], duration=node.get('duration', 0),
            link='https://www.ardsounds.de' + node['path'], audio=url, length=length)
    if not episodes:
        raise RuntimeError('No playable episodes; preserving existing feed')
    rss = ET.Element('rss', version='2.0')
    channel = ET.SubElement(rss, 'channel')
    def element(parent, name, value):
        ET.SubElement(parent, name).text = str(value)
    element(channel, 'title', show['title'])
    element(channel, 'link', SOURCE)
    element(channel, 'description', show['description'])
    element(channel, 'language', 'de-DE')
    element(channel, 'ttl', 60)
    element(channel, f'{{{ITUNES}}}author', 'NDR Info')
    element(channel, f'{{{ITUNES}}}explicit', 'false')
    cover = show['image']['url1X1'].replace('{width}', '1400')
    ET.SubElement(channel, f'{{{ITUNES}}}image', href=cover)
    if os.getenv('FEED_URL'):
        ET.SubElement(channel, f'{{{ATOM}}}link', href=os.environ['FEED_URL'], rel='self', type='application/rss+xml')
    ordered = sorted(episodes.items(), key=lambda kv: datetime.fromisoformat(kv[1]['date']), reverse=True)
    element(channel, 'lastBuildDate', format_datetime(datetime.fromisoformat(ordered[0][1]['date'])))
    for guid, episode in ordered:
        item = ET.SubElement(channel, 'item')
        for key in ('title', 'description', 'link'):
            element(item, key, episode[key])
        ET.SubElement(item, 'guid', isPermaLink='false').text = guid
        element(item, 'pubDate', format_datetime(datetime.fromisoformat(episode['date'])))
        ET.SubElement(item, 'enclosure', url=episode['audio'], length=str(episode['length']), type='audio/mpeg')
        element(item, f'{{{ITUNES}}}duration', episode['duration'])
    DOCS.mkdir(exist_ok=True)
    ET.indent(rss)
    xml = ET.tostring(rss, encoding='utf-8', xml_declaration=True)
    ET.fromstring(xml)
    # Replace only after successful extraction and serialization.
    temporary = DOCS / 'feed.xml.tmp'
    temporary.write_bytes(xml)
    temporary.replace(DOCS / 'feed.xml')
    archive.write_text(json.dumps(episodes, ensure_ascii=False, indent=2) + '\n')
    print(f'Refreshed {len(episodes)} episodes; newest: {ordered[0][1]["title"]}')

if __name__ == '__main__':
    main()
