NAME = 'Lifetime'
PREFIX = '/video/lifetime'

LT_URL = 'http://www.mylifetime.com'
SHOWS = 'http://wombatapi.aetv.com/shows2/mlt'
MOVIE_URL  = LT_URL + '/videos/movies'

####################################################################################################
def Start():

    ObjectContainer.title1 = NAME
    HTTP.CacheTime = CACHE_1HOUR
    HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.124 Safari/537.36'

####################################################################################################
@handler(PREFIX, NAME)
def MainMenu():

    oc = ObjectContainer()
    oc.add(DirectoryObject(key=Callback(Shows, title="All Shows"), title="All Shows"))
    oc.add(DirectoryObject(key=Callback(Movies, title="Movies"), title="Movies"))
    return oc

####################################################################################################
@route(PREFIX + '/shows')
def Shows(title, showPosition=''):
    oc = ObjectContainer(title2=title)
    
    json_data = JSON.ObjectFromURL(SHOWS)
    
    for item in json_data:
        if showPosition and item['showPosition']=='Position Not Set':
            continue
            
        if not (item['hasNoVideo'] == 'false' or item['hasNoHDVideo'] == 'false'):
            continue
        
        oc.add(
            TVShowObject(
                key = Callback(
                    Seasons,
                    show_id = item['showID'],
                    show_title = item['detailTitle'],
                    episode_url = item['episodeFeedURL'],
                    clip_url = item['clipFeedURL'],
                    show_thumb = item['detailImageURL2x']
                ),
                rating_key = item['showID'],
                title = item['detailTitle'],
                summary = item['detailDescription'],
                thumb = item['detailImageURL2x'],
                studio = item['network']
            )
        )

    oc.objects.sort(key = lambda obj: obj.title)
    
    return oc

####################################################################################################
@route(PREFIX + '/seasons')
def Seasons(show_id, show_title, episode_url, clip_url, show_thumb):

    oc = ObjectContainer(title2=show_title)
    
    json_data = JSON.ObjectFromURL(episode_url + '&filter_by=isBehindWall&filter_value=false')
    
    seasons = {}
    for item in json_data['Items']:
        if 'season' in item:
            if not int(item['season']) in seasons:
                seasons[int(item['season'])] = 1
            else:
                seasons[int(item['season'])] = seasons[int(item['season'])] + 1
    
    for season in seasons:
        oc.add(
            SeasonObject(
                key = Callback(
                    Episodes,
                    show_title = show_title,
                    episode_url = episode_url,
                    clip_url = clip_url,
                    show_thumb = show_thumb,
                    season = season
                ),
                title = 'Season %s' % season,
                rating_key = show_id + str(season),
                index = int(season),
                episode_count = seasons[season],
                thumb = show_thumb
            )
        )
 
    if len(oc) < 1:
        return ObjectContainer(header='Empty', message='This show does not have any unlocked videos available.')
    else:
        oc.objects.sort(key = lambda obj: obj.index, reverse = True)
        return oc 
    

####################################################################################################
@route(PREFIX + '/episodes')
def Episodes(show_title, episode_url, clip_url, show_thumb, season):

    oc = ObjectContainer(title2=show_title)
    json_data = JSON.ObjectFromURL(episode_url + '&filter_by=isBehindWall&filter_value=false')
    
    for item in json_data['Items']:
        if 'season' in item:
            if not int(item['season']) == int(season):
                continue
        
        try: url = item['siteUrl']
        except: continue
        if url.startswith('//www.mylifetime.com'):
            url = 'http:' + url
        title = item['title']
        summary = item['description'] if 'description' in item else None
        
        if 'thumbnailImage2xURL' in item:
            thumb = item['thumbnailImage2xURL']
        elif 'stillImageURL' in item:
            thumb = item['stillImageURL']
        elif 'modalImageURL' in item:
            thumb = item['modalImageURL']
        else:
            thumb = show_thumb
            
        show = item['seriesName'] if 'seriesName' in item else show_title
        duration = int(item['totalVideoDuration']) if 'totalVideoDuration' in item else None
        originally_available_at = Datetime.ParseDate(item['originalAirDate'].split('T')[0]).date() if 'originalAirDate' in item else None
        index = int(item['episode']) if 'episode' in item else None
        season = int(item['season']) if 'season' in item else None
        
        oc.add(
            EpisodeObject(
                url = url,
                title = title,
                summary = summary,
                thumb = thumb,
                art = show_thumb,
                show = show,
                duration = duration,
                originally_available_at = originally_available_at,
                index = index,
                season = season
            )
        )
    
    oc.objects.sort(key = lambda obj: obj.index)
    
    return oc
####################################################################################################
# This function produces a list of movies from the 
@route(PREFIX + '/movies')
def Movies(title):

    oc = ObjectContainer(title2=title)
    html = HTML.ElementFromURL(MOVIE_URL)

    for video in html.xpath('//div[@class="content"]//li'):
        try: video_title = video.xpath('./@data-title')[0]
        except: continue
        unlocked = video.xpath('.//div[@class="circle-icon"]/span/@class')[0]
        if unlocked.endswith('key'):
            continue
        video_url = video.xpath('./a/@href')[0]
        if not video_url.startswith('http'):
            video_url = LT_URL + video_url
        thumb = video.xpath('.//img/@src')[0]
        oc.add(VideoClipObject(
            url = video_url,
            title = video_title,
            thumb = Resource.ContentsOfURLWithFallback(url=thumb)
        ))

    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are no unlocked videos to list.")
    else:
        return oc
