NAME = 'Lifetime'
ICON = 'icon-default.png'
ART = 'art-default.jpg'
LT_BASE = '/video/lifetime'

LT_URL = 'http://www.mylifetime.com'
LT_SHOWS = LT_URL + '/shows/'
LT_VIDEOS = LT_URL + '/video'
LT_MOVIES = 'http://www.mylifetime.com/watch-full-movies-online'

RE_JSON  = Regex('jQuery.extend\(Drupal.settings, (.+?)}}\);')

RE_SEASON  = Regex('Season (\d{1,3})')
RE_EP  = Regex('Episode (\d{1,3})')
####################################################################################################
def Start():

    ObjectContainer.art = R(ART)
    ObjectContainer.title1 = NAME
    DirectoryObject.thumb = R(ICON)
    DirectoryObject.art = R(ART)

    HTTP.CacheTime = CACHE_1HOUR
    HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:18.0) Gecko/20100101 Firefox/18.0'

####################################################################################################
@handler(LT_BASE, NAME, art=ART, thumb=ICON)
def MainMenu():

    oc = ObjectContainer()
    oc.add(DirectoryObject(key=Callback(Shows, title="Lifetime Shows", show_type='Shows'), title="Lifetime Shows"))
    oc.add(DirectoryObject(key=Callback(Shows, title="LMN Shows", show_type='LMN'), title="LMN Shows"))
    oc.add(DirectoryObject(key=Callback(Movies, title="Movies"), title="Movies"))
    return oc
    
####################################################################################################
# This function produces a list of TV shows from the lifetime show page
@route(LT_BASE + '/shows')
def Shows(title, show_type):
    
    oc = ObjectContainer(title2=title)
    html = HTML.ElementFromURL(LT_SHOWS)
    
    for shows in html.xpath('//*[text()="%s"]/following::ul[contains(@class,"menu list-3")][1]//li/a' %show_type):
        show = shows.xpath('.//text()')[0]
        url = shows.xpath('./@href')[0]

        oc.add(DirectoryObject(key = Callback(Sections, title=show, url=url), title=show))
            
    return oc
    
####################################################################################################
# This function checks a show for a video and/or full episode page
@route(LT_BASE + '/sections')
def Sections(title, url):
    
    oc = ObjectContainer(title2=title)
    html = HTML.ElementFromURL(url)
    # Check for a video and/or full episode link in navigation bar
    video_types = html.xpath('//div[(contains(@class, "show-") and contains(@class, "-menu")) or contains(@class, "content-header")]//li/a/text()')
    if "Full Episodes" in video_types: 
        oc.add(DirectoryObject(key=Callback(Videos, url=url + '/video/full-episodes', title="Full Episodes"), title="Full Episodes"))
    if "Video" in video_types: 
        oc.add(DirectoryObject(key=Callback(Videos, url=url + '/video', title="All Videos"), title="All Videos"))

    #Since we are picking up the list of all shows, some may not have videos, so give message here if no videos are found
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
    json_data = json_data + '}}'
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
                thumb = Resource.ContentsOfURLWithFallback(url=thumb)
            ))
        else:
            oc.add(VideoClipObject(
                url = vid_url,
                title = vid_title,
                summary = description,
                originally_available_at = vid_date,
                thumb = Resource.ContentsOfURLWithFallback(url=thumb)
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
        return ObjectContainer(header="Empty", message="There are no unlocked full episodes listed for this show.")
    else:
        return oc
    
####################################################################################################
# This function produces a list of movies from the lifetime movies watch online page
# The json pull does not work on this page
@route(LT_BASE + '/movies')
def Movies(title):
    
    oc = ObjectContainer(title2=title)
    html = HTML.ElementFromURL(LT_MOVIES)
    
    for movies in html.xpath('//div[@class="movie-details"]'):
        premium_list = movies.xpath('./a/div/@class')
        if 'premium-new' in premium_list:
            continue
        title = movies.xpath('./a/@title')[0]
        url = movies.xpath('./a/@href')[0]
        thumb = movies.xpath('./a/@style')[0]
        thumb = thumb.split('"')[1].split('"')[0]

        oc.add(VideoClipObject(
            url = url,
            title = title,
            thumb = Resource.ContentsOfURLWithFallback(url=thumb)
        ))
            
    return oc
    
