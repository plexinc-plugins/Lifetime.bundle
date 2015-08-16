NAME = 'Lifetime'
ICON = 'icon-default.jpg'
ART = 'art-default.jpg'
LT_BASE = '/video/lifetime'

LT_URL = 'http://www.mylifetime.com'
LT_SHOWS = LT_URL + '/shows/'
LMN = LT_URL + '/movies/lifetime-movie-network'
LT_VIDEOS = LT_URL + '/video'
LT_MOVIES = 'http://www.mylifetime.com/watch-full-movies-online'

SHOW_JSON  = LT_URL + '/gv/lazy-load-shows-all/0/999?format=json'
MOVIE_JSON  = LT_URL + '/gv/lazy-load-latest-lt/0/999?format=json'
FULLEP_GV  = '/gv/lazy-load-full-eps-all/'
# BELOW ARE OTHER VIDEO PULL LISTS BUT NOT USING BECAUSE THEY ARE EMPTY OR ALREADY IN ANOTHER LIST
#LMN_MOVIE_JSON  = LT_URL + '/gv/lazy-load-latest-lmn/0/999?format=json'
#LMN_FULLEP_JSON  = LT_URL + '/gv/lazy-load-custom-list/1801/0/999?format=json'

RE_JSON  = Regex('jQuery.extend\(Drupal.settings, (.+?)\);')
RE_SEASON  = Regex('Season (\d{1,3})')
RE_EP  = Regex('Episode (\d{1,3})')
####################################################################################################
def Start():

    ObjectContainer.art = R(ART)
    ObjectContainer.title1 = NAME
    DirectoryObject.thumb = R(ICON)
    DirectoryObject.art = R(ART)

    HTTP.CacheTime = CACHE_1HOUR
    HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.124 Safari/537.36'

####################################################################################################
@handler(LT_BASE, NAME, art=ART, thumb=ICON)
def MainMenu():

    oc = ObjectContainer()
    oc.add(DirectoryObject(key=Callback(PopularShows, title="Popular Lifetime Shows"), title="Popular Lifetime Shows"))
    oc.add(DirectoryObject(key=Callback(VideoJSON, title="Movies", url=MOVIE_JSON), title="Movies"))
    oc.add(DirectoryObject(key=Callback(ShowListJSON, title="Full Episodes", json_url=SHOW_JSON, gv_json=FULLEP_GV), title="Full Episodes"))
    oc.add(DirectoryObject(key=Callback(Shows, title="All Lifetime Shows", url=LT_SHOWS), title="All Lifetime Shows"))
    oc.add(DirectoryObject(key=Callback(Shows, title="LMN Shows", url=LMN), title="LMN Shows"))
    return oc

####################################################################################################
# This function produces a list of TV shows from the lifetime show page
@route(LT_BASE + '/popularshows')
def PopularShows(title):

    oc = ObjectContainer(title2=title)
    html = HTML.ElementFromURL(LT_SHOWS)

    for shows in html.xpath('//div[@class="sl-image-block"]'):
        thumb = shows.xpath('./div/a/img/@data-img-src')[0]
        url = shows.xpath('./div/a/@href')[0]
        title = url.split('shows/')[1].replace('-', ' ').title()
        try: summary = shows.xpath('./span/text()')[0]
        except: summary = ''

        oc.add(DirectoryObject(key = Callback(Sections, title=title, url=url, thumb=thumb), title=title, thumb=Resource.ContentsOfURLWithFallback(url=thumb, fallback=ICON), summary=summary))

    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are no shows to list.")
    else:
        return oc

####################################################################################################
# This function produces a list of TV shows from the lifetime show page
@route(LT_BASE + '/shows')
def Shows(title, url):

    oc = ObjectContainer(title2=title)
    html = HTML.ElementFromURL(url)
    if 'LMN' in title:
        xpath = 'shows-entry'
    else:
        xpath = 'all-shows-list'

    for shows in html.xpath('//*[@class="%s"]//li/a' %xpath):
        show = shows.xpath('.//text()')[0]
        url = shows.xpath('./@href')[0]
        if not url.startswith('http://'):
            url = LT_URL + url

        oc.add(DirectoryObject(key = Callback(Sections, title=show, url=url), title=show))

    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are no shows to list.")
    else:
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
        return ObjectContainer(header="Empty", message="There are no shows to list.")
    else:
        return oc

####################################################################################################
# This function checks a show for a video and/or full episode page
@route(LT_BASE + '/sections')
def Sections(title, url, thumb=''):

    oc = ObjectContainer(title2=title)
    html = HTML.ElementFromURL(url)
    section_url = url + '/video'
    if not thumb:
        thumb = html.xpath('//meta[@name="thumbnail" or @property="og:image"]/@content')[0]
    # Since there are more than two sections, we just check for Video and Full Episodes 
    video_types = html.xpath('//div[(contains(@class, "show-") and contains(@class, "-menu")) or contains(@class, "content-header")]//li/a/text()')
    if "Full Episodes" in video_types: 
        oc.add(DirectoryObject(key=Callback(Videos, url=section_url + '/full-episodes', title="Full Episodes"), title="Full Episodes", thumb=Resource.ContentsOfURLWithFallback(url=thumb, fallback=ICON)))
    if "Video" in video_types: 
        oc.add(DirectoryObject(key=Callback(Videos, url=section_url, title="All Videos"), title="All Videos", thumb=Resource.ContentsOfURLWithFallback(url=thumb, fallback=ICON)))

    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are no videos for this show.")
    else:
        return oc

####################################################################################################
# This function uses the json in each page to process videos on that page
# This can process the new style of videos
@route(LT_BASE + '/videos')
def Videos(title, url=''):

    oc = ObjectContainer(title2=title)
    content = HTTP.Request(url).content
    json_data = RE_JSON.search(content).group(1)
    #Log('the value of json_data is %s' %json_data)
    json = JSON.ObjectFromString(json_data)

    for video in json['video']['videos']:
        vid_title = video['title']
        try: unlocked = video['video_behind_wall']
        except: unlocked = video['is_premium']
        if unlocked=='yes' or unlocked=='1':
            continue
        vid_title = video['title']
        thumb = video['thumbnail']
        vid_url = LT_URL + '/' + video['path']
        # This keeps the first video from reproducing for each page
        if url.startswith(vid_url):
            continue
        try: vid_date = Datetime.ParseDate(video['original_air_date']).date()
        except: vid_date = None
        description = video['short_description']
        # Seems a few are missing the duration so try/except
        try: duration = int(video['duration']) * 1000
        except: duration = 0
        try: show_title = video['series_name']
        except: show_title = title
        # Some season are not producing, so if there is not a season get that info from the description
        try: season = int(season = video['season'])
        except:
            try: season = int(RE_SEASON.search(description).group(1))
            except: season = 0
        try: episode = int(video['episode'])
        except:  episode = 0
        if episode!=0:
            oc.add(EpisodeObject(
                show = show_title,
                season = season,
                index = episode,
                duration = duration,
                url = vid_url,
                title = vid_title,
                originally_available_at = vid_date,
                summary = description,
                thumb = Resource.ContentsOfURLWithFallback(url=thumb, fallback=ICON)
            ))
        else:
            oc.add(VideoClipObject(
                url = vid_url,
                title = vid_title,
                summary = description,
                originally_available_at = vid_date,
                thumb = Resource.ContentsOfURLWithFallback(url=thumb, fallback=ICON)
            ))

    try:
        html = HTML.ElementFromString(content)
        next_url = html.xpath('//ul[contains(@class,"pager")]/li[contains(@class,"next") or contains(@class,"-right")]/a/@href')[0]
        if not next_url.startswith('http://'):
            next_url = '%s%s' %(LT_URL, next_url)
        oc.add(NextPageObject(key=Callback(Videos, title=title, url=next_url), title = L("Next Page ...")))
    except:
        pass

    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are no unlocked videos for this show.")
    else:
        return oc
