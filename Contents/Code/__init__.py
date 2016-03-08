NAME = 'Lifetime'
PREFIX = '/video/lifetime'

LT_URL = 'http://www.mylifetime.com'
SHOWS = 'http://wombatapi.aetv.com/shows2/mlt'
SIGNATURE_URL = 'http://servicesaetn-a.akamaihd.net/jservice/video/components/get-signed-signature?url=%s'
SMIL_NS = {"a":"http://www.w3.org/2005/SMIL21/Language"}
MOVIE_JSON  = LT_URL + '/gv/lazy-load-latest-lt/0/999?format=json'

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
    oc.add(DirectoryObject(key=Callback(VideoJSON, title="Movies", url=MOVIE_JSON), title="Movies"))
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
        
        url = item['siteUrl']
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
# This function produces a list of movies from json
@route(PREFIX + '/videojson')
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
        oc.add(VideoClipObject(
            duration = duration,
            url = video_url,
            title = video['video_title'],
            originally_available_at = Datetime.ParseDate(video['air_date']),
            summary = video['short_desc'],
            thumb = Resource.ContentsOfURLWithFallback(url=video['video_thumb'])
        ))

    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are no unlocked videos to list.")
    else:
        return oc
