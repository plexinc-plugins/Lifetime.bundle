NAME = 'Lifetime'
ICON = 'icon-default.jpg'
ART = 'art-default.jpg'
LT_BASE = '/video/lifetime'

LT_URL = 'http://www.mylifetime.com'
SHOW_JSON  = LT_URL + '/gv/lazy-load-shows-all/0/999?format=json'
POPULAR_JSON  = LT_URL + '/gv/lazy-load-shows/0/ ?format=json'
MOVIE_JSON  = LT_URL + '/gv/lazy-load-latest-lt/0/999?format=json'
FULLEP_GV  = '/gv/lazy-load-full-eps/'

####################################################################################################
def Start():

    ObjectContainer.title1 = NAME
    DirectoryObject.thumb = R(ICON)
    EpisodeObject.thumb = R(ICON)

    HTTP.CacheTime = CACHE_1HOUR
    HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.124 Safari/537.36'

####################################################################################################
@handler(LT_BASE, NAME, art=ART, thumb=ICON)
def MainMenu():

    oc = ObjectContainer()
    oc.add(DirectoryObject(key=Callback(ShowListJSON, title="Popular Shows", json_url=POPULAR_JSON, gv_json=FULLEP_GV), title="Popular Shows"))
    oc.add(DirectoryObject(key=Callback(ShowListJSON, title="All Shows", json_url=SHOW_JSON, gv_json=FULLEP_GV), title="All Shows"))
    oc.add(DirectoryObject(key=Callback(VideoJSON, title="Movies", url=MOVIE_JSON), title="Movies"))
    return oc

####################################################################################################
# This function produces a list of shows from the json  to build a fullep json url
@route(LT_BASE + '/showlistjson')
def ShowListJSON (title, json_url, gv_json):

    oc = ObjectContainer(title2=title)
    json = JSON.ObjectFromURL(json_url)

    for section in json['items']:
        show = section['title']
        url = section['url']
        show_code = String.Quote(section['show_code'], usePlus = False)
        total_videos = section['total_videos']
        section_url = LT_URL + '%s%s/0/%s?format=json' %(gv_json, show_code, total_videos)
        oc.add(DirectoryObject(key = Callback(VideoJSON, title=show, url=section_url), title=show))

    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are no videos to list.")
    else:
        return oc

####################################################################################################
# This function produces a list of full episodes from json
@route(LT_BASE + '/videojson')
def VideoJSON(title, url):

    oc = ObjectContainer(title2=title)
    json = JSON.ObjectFromURL(url)

    for video in json['items']:
        unlocked = video['behind_wall']
        if unlocked=='1':
            continue
        video_url = video['video_url']
        if '/just-added-full-episodes' in video_url:
            video_url = video_url.replace('/just-added-full-episodes', '')
        try: duration = int(video['duration']) * 1000
        except: duration = 0
        episode = video['episode']
        if episode:
            oc.add(EpisodeObject(
                show = video['series'],
                season = int(video['season']),
                index = int(episode),
                duration = duration,
                url = video_url,
                title = video['video_title'],
                originally_available_at = Datetime.ParseDate(video['air_date']),
                summary = video['short_desc'],
                thumb = Resource.ContentsOfURLWithFallback(url=video['video_thumb'], fallback=ICON)
            ))
        else:
            oc.add(VideoClipObject(
                duration = duration,
                url = video_url,
                title = video['video_title'],
                originally_available_at = Datetime.ParseDate(video['air_date']),
                summary = video['short_desc'],
                thumb = Resource.ContentsOfURLWithFallback(url=video['video_thumb'], fallback=ICON)
            ))

    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are no unlocked videos to list.")
    else:
        return oc
