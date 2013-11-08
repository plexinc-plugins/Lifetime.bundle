import re

NAME = 'Lifetime'
ICON = 'icon-default.png'
ART = 'art-default.jpg'

LT_BASE = '/video/lifetime'

LT_URL = 'http://www.mylifetime.com'
LT_VIDEO = LT_URL + '/video'
LT_SHOWS = LT_URL + '/shows'
LT_MOVIES = LT_URL + '/movies'
LT_MOVIES_NEW = 'http://www.mylifetime.com/watch-full-movies-online'
LT_SHOW_PREFIX = LT_SHOWS + '/'
LT_MOVIE_PREFIX = LT_MOVIES + '/'
LT_VIDEO_POSTFIX = '/video'
LT_SECTIONS = '%s?field_length_value_many_to_one=%s&media_type=shows'

RE_SEASON  = Regex('Season (\d{1,2})')
RE_EPISODE  = Regex('Episode (\d{1,3}).+')

MILLISECONDS_IN_A_MINUTE = 60000
URL_EXTENSIONS = ["-splash-page", "-0", "_ep", "-test"]

####################################################################################################
def Start():

    ObjectContainer.art = R(ART)
    ObjectContainer.title1 = NAME
    DirectoryObject.thumb = R(ICON)
    NextPageObject.thumb = R(ICON)
    EpisodeObject.thumb = R(ICON)
    VideoClipObject.thumb = R(ICON)

    #HTTP.CacheTime = CACHE_1HOUR
    HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:18.0) Gecko/20100101 Firefox/18.0'

####################################################################################################
@handler(LT_BASE, NAME, art=ART, thumb=ICON)
def MainMenu():

    oc = ObjectContainer()

    html = HTML.ElementFromURL(LT_VIDEO)
    
    for header in html.xpath('//div[@id="accordion"]/h3'):
        title = header.xpath('./a/text()')[0]
        if 'Movie' in title:
            continue
        else:
            oc.add(DirectoryObject(key=Callback(Shows, title=title), title=title))
            
    oc.add(DirectoryObject(key=Callback(Movie, title="Movies"), title="Movies"))

    return oc
    
####################################################################################################
@route(LT_BASE + '/shows')
def Shows(title):
    
    oc = ObjectContainer(title2=title)
    html = HTML.ElementFromURL(LT_VIDEO)
    
    for show_element in html.xpath('//h3/a[text()="' + title + '"]/../following-sibling::div[1]//span[@class="views-field-title"]//a'):
        show = show_element.xpath('./text()')[0]
        original_url = show_element.xpath('./@href')[0]
        Log('the value of original_url is %s' %original_url)
        # By trial and error, any original URL containing 'test', 'page', or a number at the end needs to be corrected.
        # Check for extra backslash in show name of url and then compare to list of errors that may be at the end of urls
        section_url = original_url.split('shows/')[1]
        if '/' in section_url:
            section_url = section_url.split('/')[0]
            original_url = LT_SHOW_PREFIX + section_url
        for ending in URL_EXTENSIONS:
            if original_url.endswith(ending):
                original_url = original_url.split(ending)[0]

        url = original_url + LT_VIDEO_POSTFIX
        oc.add(DirectoryObject(key = Callback(Sections, title=show, url=url), title = show))
            
    return oc
    
####################################################################################################
def Movie(title):

    oc = ObjectContainer(title2=title)
    html = HTML.ElementFromURL(LT_MOVIES_NEW)
    for video in html.xpath('//div[contains(@class,"shcedule-item")]'):
        movie_type = video.xpath('.//@class')[0]
        url = video.xpath('./div/a//@href')[0]
        title = video.xpath('./div[@class="movie-details"]/a//@title')[0]
        thumb = video.xpath('./div[@class="movie-details"]/a//@style')[0]
        thumb = thumb.split('background: url("')[1].split('")')
        if 'premium' not in movie_type:
            oc.add(VideoClipObject(
                url = url,
                title = title,
                thumb = Resource.ContentsOfURLWithFallback(url=thumb)
            ))

    if len(oc) < 1:
        return ObjectContainer(header="Empty", message="There are no movies available.")
    else:
        return oc
####################################################################################################
@route(LT_BASE + '/sections')
def Sections(title, url):
    
    oc = ObjectContainer(title2=title)
    html = HTML.ElementFromURL(url)
    video_types = html.xpath('//select[@name="field_length_value_many_to_one"]/option//@value')
    Log('the value of video_types is %s' %video_types)
    if 'FullEp' in video_types:
        oc.add(DirectoryObject(key=Callback(Videos, url=url, vid_type='FullEp', title="Full Episodes"), title="Full Episodes"))
    if 'Clip' in video_types:
        oc.add(DirectoryObject(key=Callback(Videos, url=url, vid_type='Clip', title="Clips"), title="Clips"))
    #oc.add(DirectoryObject(key=Callback(Videos, url=url, vid_type='FullEp', title="Full Episodes"), title="Full Episodes"))
    #oc.add(DirectoryObject(key=Callback(Videos, url=url, vid_type='Clip', title="Clips"), title="Clips"))
            
    return oc
####################################################################################################
@route(LT_BASE + '/videos')
def Videos(title, url, vid_type):

    oc = ObjectContainer(title2=title)
    if not '?' in url:
        local_url = LT_SECTIONS %(url, vid_type)
    else:
        local_url = url
    html = HTML.ElementFromURL(local_url)

    for video in html.xpath('//div[@class="video-rollover-container-middle-content"]/div[contains(@class, "views-row")]'):
        show = video.xpath('.//div[@class="video-rollover-container-middle-player-text"]/b/text()')[0].rstrip(":")
        new_url = video.xpath('.//a/@href')[0]
        description = video.xpath('.//a/@title')[0]
        summary = re.sub(r'<.*?>', '', description)
        new_thumb = video.xpath('.//img/@src')[0]
        air_date = video.xpath('.//div[@class="video-rollover-container-player-timer-text"]/text()')[0].strip()
        originally_available_at = Datetime.ParseDate(air_date).date()
        new_title = video.xpath('.//img/@title')[0]
        premium = video.xpath('.//div[@class="video-play-symbol is-premium"]')
        if len(premium) > 0:
            #new_title = 'Premium - ' + new_title
            continue
        try:
            index = int(RE_EPISODE.search(new_title).group(1))
        except:
            index = 0
        season_match = new_url.split('/season-')[1].split('/')[0]
        season = int(season_match)
        oc.add(EpisodeObject(
            show = show,
            season = season,
            index = index,
            url = new_url,
            title = new_title,
            summary = summary,
            thumb = new_thumb,
            originally_available_at = originally_available_at
        ))
    
    oc.objects.sort(key = lambda obj: obj.originally_available_at, reverse=True)
    try:
        next_page = html.xpath('//li[contains(@class,"video-rollover-container-navigation-right")]/a//@href')[0]
        oc.add(NextPageObject(key=Callback(Videos, title=title, url=next_page, vid_type=vid_type), title = L("Next Page ...")))
    except:
        pass

    if len(oc) < 1:
        return ObjectContainer(header="Empty", message="This show does not have any unlocked videos available.")
    else:
        return oc
