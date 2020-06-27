import aiohttp
import asyncio
import uvloop
from collections import Counter
import humanize
import datetime
import math
import traceback
import os
import requests

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
 
### WARNING: SHIT CODE

async def x():
    cs = aiohttp.ClientSession()
    tasks = []
    curpage, maxpage = 1, max(1, math.ceil(lastfm_get_tracks() / 1000))
    print(maxpage)
    # Initial feeding
    while curpage <= maxpage:
        sem = asyncio.Semaphore(40)
        tasks.append(lastfm_fetch_user(sem=sem, page=curpage, cs=cs))
        curpage += 1
    
    counters = {'artist': Counter(), 'track': Counter()}
    artist2track = {}
    artist2name = {}
    track2artist = {}
    for tracks in await asyncio.gather(*tasks):
        for track in tracks:
            artist, artist_str, track = track['artist'], track['artist_str'], track['track']

            counters['artist'][artist] += 1
            counters['track'][track] += 1

            if artist not in artist2name:
                artist2name[artist] = artist_str

            if artist not in artist2track:
                artist2track[artist] = set()

            artist2track[artist].add(track)
            track2artist[track] = artist

    tasks = []
    track2duration = {}
    sem = asyncio.Semaphore(200)
    for track in counters['track'].keys():
        tasks.append(lastfm_get_track_duration(sem, track, cs))
    for mbid, duration in await asyncio.gather(*tasks):
        track2duration[mbid] = duration
    
    artist2duration = Counter()
    for track, repeated in counters['track'].items():
        artist, duration = track2artist[track], track2duration[track]
        artist2duration[artist] += duration*repeated
    
    for artist, duration in artist2duration.items():
        human = human_time(seconds=duration)
        artist_str = artist2name[artist]
        print(f'{duration} {human} {artist_str}')
    cs.close()

def human_time(*args, **kwargs):
    secs  = float(datetime.timedelta(*args, **kwargs).total_seconds())
    units = [("day", 86400), ("hour", 3600), ("minute", 60), ("second", 1)]
    parts = []
    for unit, mul in units:
        if secs / mul >= 1 or mul == 1:
            if mul > 1:
                n = int(math.floor(secs / mul))
                secs -= n * mul
            else:
                n = secs if secs != int(secs) else int(secs)
            parts.append("%s %s%s" % (n, unit, "" if n == 1 else "s"))
    return ", ".join(parts)

async def lastfm_fetch_user(sem, page, cs=None):
    async with sem:
        if not cs:
            cs = aiohttp.ClientSession()
        params = {
            'method': 'user.getrecenttracks',
            'limit': 1000,
            'user': os.getenv('NICK', 'chauffer9001'),
            'api_key': 'x',
            'format': 'json',
            'page': page,
        }
        ret = []
        async with cs.get('https://ws.audioscrobbler.com/2.0/', params=params) as res:
            tracks = await res.json()
            tracks = tracks['recenttracks']['track']
            for track in tracks:
                ret.append(dict(
                    artist=track['artist']['mbid'],
                    artist_str=track['artist']['#text'],
                    track=track['mbid'],
                ))
        return ret

def lastfm_get_tracks():
    params = {
        'method': 'user.getrecenttracks',
        'limit': 1,
        'user': os.getenv('NICK', 'chauffer9001'),
        'api_key': 'x',
        'format': 'json',
    }
    r = requests.get('https://ws.audioscrobbler.com/2.0/', params=params).json()
    return int(r['recenttracks']['@attr']['total'])

async def lastfm_get_track_duration(sem, mbid, cs=None):
    try:
        async with sem:
            if not cs:
                cs = aiohttp.ClientSession()
            params = {
                'method': 'track.getInfo',
                'api_key': 'x',
                'mbid': mbid,
                'format': 'json'
            }
            async with cs.get('https://ws.audioscrobbler.com/2.0/', params=params, timeout=10) as res:
                track = await res.json()
                print('Fetched track')
                return mbid, int(int(track['track']['duration']) / 1000)
    except:
        print('ERROR with track...', mbid)
        traceback.print_exc()
        return mbid, 0


asyncio.get_event_loop().run_until_complete(x())
