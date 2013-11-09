NAME = 'Lifetime'
ICON = 'icon-default.png'
ART = 'art-default.jpg'
LT_BASE = '/video/lifetime'

LT_URL = 'http://www.mylifetime.com'
LT_SHOWS = LT_URL + '/shows/'
LT_MOVIES = 'http://www.mylifetime.com/video?field_length_value_many_to_one=FullMov'
LT_SECTIONS = '%s?field_length_value_many_to_one=%s&media_type=shows'

RE_EPISODE  = Regex('Episode (\d{1,3}).+')

####################################################################################################
def Start():

    ObjectContainer.art = R(ART)
    ObjectContainer.title1 = NAME
    DirectoryObject.thumb = R(ICON)
    EpisodeObject.thumb = R(ICON)
    VideoClipObject.thumb = R(ICON)

    HTTP.CacheTime = CACHE_1HOUR
    HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:18.0) Gecko/20100101 Firefox/18.0'

####################################################################################################
@handler(LT_BASE, NAME, art=ART, thumb=ICON)
def MainMenu():

    oc = ObjectContainer()
    oc.add(DirectoryObject(key=Callback(Shows, title="Current Shows", show_type='-middle'), title="Current Shows"))
    oc.add(DirectoryObject(key=Callback(Shows, title="Classic Shows", show_type=' classic-show'), title="Classic Shows"))
    oc.add(DirectoryObject(key=Callback(Videos, url=LT_MOVIES, vid_type='FullMov', title="Movies"), title="Movies"))
    return oc
    
####################################################################################################
# This function produces a list of TV shows from the lifetime show page
# Original plugin used video page. Using show page allows for images and fixes issue with show URLs errors due to added characters
@route(LT_BASE + '/shows')
def Shows(title, show_type):
    
    oc = ObjectContainer(title2=title)
    html = HTML.ElementFromURL(LT_SHOWS)
    
    for shows in html.xpath('//div[@class="show-item-wrapper%s"]/div/div[contains(@class,"show-item item-")]' %show_type):
        show = shows.xpath('./h3/a//text()')[0]
        url = shows.xpath('./h3/a//@href')[0]
        vid_url = url + '/video'
        if 'classic' in show_type:
            thumb = R(ICON)
        else:
            thumb = shows.xpath('./div/a/img//@src')[0]

        oc.add(DirectoryObject(key = Callback(Sections, title=show, url=vid_url, thumb=thumb), title=show, thumb=thumb))
            
    return oc
    
####################################################################################################
# This function checks a show's video page to see if it offers full episode
@route(LT_BASE + '/sections')
def Sections(title, url, thumb):
    
    oc = ObjectContainer(title2=title)
    html = HTML.ElementFromURL(url, cacheTime = CACHE_1DAY)
    video_types = html.xpath('//select[@name="field_length_value_many_to_one"]/option//@value')
    if 'FullEp' in video_types:
        oc.add(DirectoryObject(key=Callback(Videos, url=url, vid_type='FullEp', title="Full Episodes"), title="Full Episodes", thumb=thumb))
    if 'Clip' in video_types:
        oc.add(DirectoryObject(key=Callback(Videos, url=url, vid_type='Clip', title="Clips"), title="Clips", thumb=thumb))
            
    return oc
####################################################################################################
# This function produces a list of videos from the different pages for show full episodes and clips as well as full movies
# All videos are ordered by most recently added
@route(LT_BASE + '/videos')
def Videos(title, url, vid_type):

    oc = ObjectContainer(title2=title)
    if not '?' in url:
        local_url = LT_SECTIONS %(url, vid_type)
    else:
        local_url = url
    html = HTML.ElementFromURL(local_url)

    for video in html.xpath('//div[@class="video-rollover-container-middle-content"]/div'):
        show = video.xpath('./div[contains(@class,"player-text")]/b//text()')[0].rstrip(":")
        vid_url = video.xpath('.//a//@href')[0]
        description = video.xpath('.//a//@title')[0]
        # Some of the decsriptions could be split at the period to take out the actual title,
        # but what appears in the description varies so just keeping all the info that is there
        summary = description.replace('<div class=trimmed-text>', '').split('</div>')[0]
        try:
            exp_date = description.split('<div class=exp-date>')[1].split('</div>')[0]
        except:
            exp_date = ''
        if exp_date:
            summary = '%s - %s' %(summary, exp_date)
        thumb = video.xpath('.//img//@src')[0]
        air_date = video.xpath('.//div[contains(@class,"player-timer-text")]/text()')[0].strip()
        originally_available_at = Datetime.ParseDate(air_date).date()
        vid_title = video.xpath('.//img//@title')[0]
        premium = video.xpath('.//div[@class="video-play-symbol is-premium"]')
        if len(premium) > 0:
            continue
        if vid_type == 'FullEp':
            try:
                index = int(RE_EPISODE.search(vid_title).group(1))
            except:
                index = 0
            season_match = vid_url.split('/season-')[1].split('/')[0]
            season = int(season_match)
            oc.add(EpisodeObject(
                show = show,
                season = season,
                index = index,
                url = vid_url,
                title = vid_title,
                summary = summary,
                thumb = Resource.ContentsOfURLWithFallback(url=thumb),
                originally_available_at = originally_available_at
            ))
    
        else:
            oc.add(VideoClipObject(
                source_title = show,
                url = vid_url,
                title = vid_title,
                summary = summary,
                thumb = Resource.ContentsOfURLWithFallback(url=thumb),
                originally_available_at = originally_available_at
            ))
    oc.objects.sort(key = lambda obj: obj.originally_available_at, reverse=True)
    try:
        page_url = html.xpath('//li[contains(@class,"-navigation") and contains(@class,"-right")]/a//@href')[0]
        if '/d6/' in page_url:
            # the url for the main video page does not work unless you remove the d6 directory from the next page anchor
            page_url = page_url.replace('/d6', LT_URL)
        oc.add(NextPageObject(key=Callback(Videos, title=title, url=page_url, vid_type=vid_type), title = L("Next Page ...")))
    except:
        pass

    if len(oc) < 1:
        return ObjectContainer(header="Empty", message="This show does not have any unlocked videos available.")
    else:
        return oc
