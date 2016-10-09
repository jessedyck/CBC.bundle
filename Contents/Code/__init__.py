####################################################################################################
#CBC.CA Video Plugin
#Written by mysciencefriend
#Overhauled and updated by Mikedm139
#Use at your own risk, etc. etc.

import urlparse
from pprint import pprint

ART  = 'art-default.jpg'
ICON = 'icon-default.jpg'

MORE_SHOWS = '1329813962'

'''SHOWS_LIST  = 'http://cbc.feeds.theplatform.com/ps/JSON/PortalService/2.2/getCategoryList?PID=_DyE_l_gC9yXF9BvDQ4XNfcCVLS4PQij&field=ID&field=title&field=parentID&field=description&customField=MaxClips&customField=ClipType&query=ParentIDs|%s'''
SHOWS_LIST  = 'https://api-cbc.cloud.clearleap.com/cloffice/client/web/browse/babb23ae-fe47-40a0-b3ed-cdc91e31f3d6'
AUTH_URL = 'https://api-cbc.cloud.clearleap.com/cloffice/client/device/register'
AUTH_DATA = '<device><type>web</type></device>'
DEVICE_ID = ''
DEVICE_TOKEN = ''
HEADERS = {}
RESULTS_PER_PAGE = 30
'''VIDEOS_LIST = 'http://cbc.feeds.theplatform.com/ps/JSON/PortalService/2.2/getReleaseList?PID=_DyE_l_gC9yXF9BvDQ4XNfcCVLS4PQij&query=CategoryIDs|%s&sortDescending=true&endIndex=500'
BASE_URL    = 'http://www.cbc.ca'
PLAYER_URL  = BASE_URL + '/player/%s'
VIDEO_URL   = PLAYER_URL % 'play/'
LIVE_SPORTS = PLAYER_URL % 'sports/Live'
NHL_URL     = BASE_URL + '/sports/hockey/nhl'
JSON_URL    = BASE_URL + '/json/cmlink/%s'''

RE_THUMB_URL=   Regex('background-image: url\(\'(?P<url>http://.+?jpg)\'\)')

CATEGORIES  = ['TV', 'News', 'Kids', 'Sports', 'Radio']

def Start():
    # Setup the default breadcrumb title for the plugin
    ObjectContainer.title1 = 'CBC'

    Log('Initting CBC')

    GetAuthTokens()



def GetAuthTokens():
    Log('Starting auth')
    global DEVICE_TOKEN
    global DEVICE_ID
    global HEADERS

    # Get the auth tokens that we need for the API
    # TODO: Cache auth tokens somewhere
    try:
        auth = XML.ElementFromURL(AUTH_URL, values={'data': AUTH_DATA})

        '''
        EXAMPLE RESPONSE:

        <result version='2.0' xmlns:media='http://search.yahoo.com/mrss/' xmlns:dcterms='http://purl.org/dc/terms/' xmlns:clearleap='http://www.clearleap.com/namespace/clearleap/1.0/'>
          <systemMessage>Device registered - deviceId:6a3cc941-f5df-47b1-a4cb-c609a87be207 type:null</systemMessage>
          <userMessage>Device has been successfully registered.</userMessage>
          <status>Success</status>
          <deviceId>6a3cc941-f5df-47b1-a4cb-c609a87be207</deviceId>
          <deviceToken>bEFzWk9EUENFQjVxRGhIb3hVRUtHYnZXcGxpRnZZQ0ZwWDFmYXE4dzJsTT0=</deviceToken>
        </result>
        '''

        DEVICE_ID = auth.xpath('//deviceId')[0].text
        DEVICE_TOKEN = auth.xpath('//deviceToken')[0].text
        HEADERS = {'X-Clearleap-DeviceToken': DEVICE_TOKEN, 'X-Clearleap-DeviceId': DEVICE_ID}
    except Ex.HTTPError, e:
        Log.Error ('Error authing. Response from server: ' + str(e.code))

        return ObjectContainer(header="Sorry", message="The request was denied. Please try again.")



####################################################################################################
@handler('/video/cbc', 'CBC', art=ART, thumb=ICON)
def MainMenu():

    Log('Displaying Main Menu')

    oc = ObjectContainer()
    '''oc.add(DirectoryObject(key=Callback(HockeyNightInCanada), title='Hockey Night In Canada'))
    oc.add(DirectoryObject(key=Callback(LiveSports), title='Live Sports'))'''
    oc.add(DirectoryObject(key=Callback(Shows), title='Shows'))

    '''for category in CATEGORIES:

        oc.add(DirectoryObject(
            key = Callback(Category, category=category),
            title = category
        ))'''

    oc.add(SearchDirectoryObject(
        identifier = 'com.plexapp.plugins.cbcnewsnetwork',
        title = 'Search',
        summary = 'Search CBC videos',
        prompt = 'Search for...'
    ))

    return oc

####################################################################################################
@route('/video/cbc/shows')
def Shows(category=None, link=None, offset=0):
    oc = ObjectContainer(title2="All Shows")

    offset = int(offset)

    # TODO: Error handling
    page = XML.ElementFromURL(SHOWS_LIST + '?offset=' + str(offset))

    num_shows = int(page.xpath('//clearleap:totalResults', namespaces={'media': 'http://search.yahoo.com/mrss/', 'clearleap': 'http://www.clearleap.com/namespace/clearleap/1.0/'})[0].text)
    shows = page.xpath('//item')

    for show in shows:
        title = show.xpath('.//title')[0].text

        # Link to the show episode/series list
        link = show.xpath('.//link')[0].text

        oc.add(DirectoryObject(
            key = Callback(DisplayShowItems, title=title, link=link),
            title = title
        ))

    if (offset + RESULTS_PER_PAGE < num_shows):
        oc.add(DirectoryObject(
            key = Callback(Shows, link=link, offset=offset+RESULTS_PER_PAGE),
            title = 'More Shows...'
        ))

    if len(oc) < 1:
        return ObjectContainer(header="Sorry", message="There aren't any shows currently available.")
    else:
        return oc

# media_scope:  
@route('/video/cbc/showepisodes')
def DisplayShowItems(title=None, link=None, media_scope=None):
    oc = ObjectContainer (title2=title)
    Log('Show Title: ' + title)
    Log('Media scope: ' + str(media_scope))

    page = XML.ElementFromURL(link)

    videos = page.xpath('//item')

    for video in videos:
        video_title = video.xpath('.//title')[0].text

        url = video.xpath('.//link')[0].text

        description = video.xpath('.//description')[0].text

        # Might be preferred to get a specific thumbnail size, eg: [contains(@profile,"CBC-THUMBNAIL")]
        thumb = video.xpath('.//media:thumbnail', namespaces={'media': 'http://search.yahoo.com/mrss/', 'clearleap': 'http://www.clearleap.com/namespace/clearleap/1.0/'})
        
        if (len(thumb) > 0):
            thumb = thumb[0].get('url')
        else:
            thumb = ''

        '''
        SHOW TYPES (so far):
            season
            series
            seasonless_show
            Documentary
            Reality
        '''
        if (not media_scope):
            media_scope = video.xpath('.//media:keywords', namespaces={'media': 'http://search.yahoo.com/mrss/', 'clearleap': 'http://www.clearleap.com/namespace/clearleap/1.0/'})[0].text
            Log('Retreived media scope: ' + media_scope)
        
        # List of seasons in show
        if (media_scope == 'season'):
            Log('Adding a season to the container')

            video_obj = SeasonObject(
                key = Callback(DisplayShowItems, title=title, link=url, media_scope='season_episodes'),
                rating_key = title + ' ' + video_title,
                title = video_title,
                summary = description,
                thumb = thumb
            )
        elif (media_scope == 'season_episodes'):
            Log('Adding a season episode to the container')

            video_obj = VideoClipObject(
                key = Callback(ShowEpisodeDetails, title=title, link=url), #, media_scope='episode'
                rating_key = title + ' ' + video_title,
                title = video_title,
                summary = description,
                thumb = thumb
            )


            # Attach a bunch of metadata
            season_id = video.xpath('.//clearleap:season', namespaces={'media': 'http://search.yahoo.com/mrss/', 'clearleap': 'http://www.clearleap.com/namespace/clearleap/1.0/'})
            # episode_id = video.xpath('.//clearleap:episodeInSeason', namespaces={'media': 'http://search.yahoo.com/mrss/', 'clearleap': 'http://www.clearleap.com/namespace/clearleap/1.0/'})
            release_date = video.xpath('.//media:credit[contains(@role, "releaseDate")]', namespaces={'media': 'http://search.yahoo.com/mrss/', 'clearleap': 'http://www.clearleap.com/namespace/clearleap/1.0/'})

            # if (season_id):
            #     video_obj.season = int(season_id[0].text)
                
            # if (episode_id):
            #     video_obj.episode = int(episode_id[0].text)

            if (release_date):
                video_obj.originally_available_at = Datetime.ParseDate(release_date[0].text)
            
        # List of episodes in seasonless show, or episodes in a season
        elif (media_scope == 'episode'):
            Log('Adding a final episode video to the container')
            
            #pprint (vars(your_object))
            video_obj = VideoClipObject(
                key = Callback(ShowEpisodeDetails, title=title, link=url),
                rating_key = title + ' ' + video_title,
                title = video_title,
                summary = description,
                thumb = thumb
            )
        else:
            Log('Adding a generic video to the container')

            video_obj = VideoClipObject(
                key = Callback(ShowEpisodeDetails, title=title, link=url),
                rating_key = title + ' ' + video_title,
                title = video_title,
                summary = description,
                thumb = thumb
            )


        oc.add(video_obj)

    if len(oc) < 1:
        return ObjectContainer(header="Sorry", message="There aren't any videos currently available for this show.")
    else:
        return oc



@route('/video/cbc/showepisode')
def ShowEpisodeDetails(title=None, link=None):
    oc = ObjectContainer (title2=title)

    Log('Video Title: ' + title)

    video_obj = GetEpisodeMetaObject(link=link, return_object='videoclip')

    oc.add(video_obj)

    if len(oc) < 1:
        return ObjectContainer(header="Sorry", message="There aren't any videos currently available for this show.")
    else:
        return oc

@route('/video/cbc/getepisodemetaobject')
def GetEpisodeMetaObject (link, return_object='episode'):
    Log('Getting episode meta from: ' + link)

    # If HEADERS are invalid, authenticate first
    if not HEADERS:
        GetAuthTokens()

    video_data = XML.ElementFromURL(link)

    # Get metadata for video
    title = video_data.xpath('.//title')[0].text
    description = video_data.xpath('.//description')[0].text
    thumb = video_data.xpath('.//media:thumbnail[contains(@profile,"CBC-THUMBNAIL-3X")]', namespaces={'media': 'http://search.yahoo.com/mrss/', 'clearleap': 'http://www.clearleap.com/namespace/clearleap/1.0/'})[0].get('url')
    content = video_data.xpath('.//media:content', namespaces={'media': 'http://search.yahoo.com/mrss/', 'clearleap': 'http://www.clearleap.com/namespace/clearleap/1.0/'})[0]
    duration = int(content.get('duration'))*1000 # ms

    # Extract the URL for the XML that will contain the final playlist URL
    # EXAMPLE RESULT:
    # https://api-cbc.cloud.clearleap.com/cloffice/client/web/play/?contentId=d158320f-cb3d-4bb7-91e9-8aee19f0d296&categoryId=38e815a-009d46e060f
    url = content.get('url')


    # Get the URL for the m3u8 playlist file, with auth headers
    # If the request fails, invalidate auth cache
    try:
        playlist_response = XML.ElementFromURL(url, headers=HEADERS)
    except HTTPError, e:
        Log('Invalidating headers')
        global HEADERS
        HEADERS = {}

        Log.Error ('Response from server: ' + str(e.code))
        return ObjectContainer(header="Sorry", message="There was a error connecting to the server. Please try again.")

    # Get the playlist URL
    # EXAMPLE RESULT: 
    # http://v.watch.cbc.ca/p//38e815a-00a02504379//CBC_NTL_ABORIGINAL_HIS_MO_WERE_STILL_HERE-v2-9145569/CBC_NTL_ABORIGINAL_HIS_MO_WERE_STILL_HERE-v2-9145569__desktop.m3u8?cbcott=st=1475461788~exp=1475548188~acl=/*~hmac=8fd64e3dd9b73caf1ce12198259990cccd223d98aef3c6220cbea80df68df0e7
    playlist_response = playlist_response.xpath('//url')

    if (not playlist_response or len(playlist_response) <= 0):
        Log.Error ('Could not find a playlist URL')
        return ObjectContainer(header="Sorry", message="There was a error locating the video. Please try again.")

    playlist_url = playlist_response[0].text
    Log('Playlist URL: ' + playlist_url)


    # Construct a list of streams available in the playlist
    streams = CreateStreamList(playlist_url, HEADERS)
    Log('Stream URL: ' + streams[0])

    if (return_object == 'episode'):
        video_obj = EpisodeObject(
            key = Callback(GetEpisodeMetaObject, link=link, return_object='episode'),
            rating_key = title, #TODO: Change to match ShowEpisodes format
            title = title,
            summary = description,
            duration = duration,
            thumb = thumb,
            items                   = [
                MediaObject(
                    optimized_for_streaming = True,
                    parts                   =   [
                        PartObject(
                            key             = HTTPLiveStreamURL(
                                url         = streams[0]
                            )
                        )
                    ]
                )
            ]
        )
    else:
        video_obj = VideoClipObject(
            key = Callback(GetEpisodeMetaObject, link=link, return_object='videoclip'),
            rating_key = title, #TODO: Change to match ShowEpisodes format
            title = title,
            summary = description,
            thumb = thumb,
            items                   = [
                MediaObject(
                    optimized_for_streaming = True,
                    parts                   =   [
                        PartObject(
                            key             = HTTPLiveStreamURL(
                                url         = streams[0]
                            )
                        )
                    ]
                )
            ]
        )

    return video_obj



# Thanks @kapeer - https://github.com/kapeer/Telewizjada.bundle/blob/master/Contents/Code/__init__.py#L185
def CreateStreamList(url, headers):
    root_url = url.split('?',1)[0]
    media_base = root_url.rsplit('/', 1)[0] + '/'
    playlist = HTTP.Request(url, headers=headers, cacheTime=0).content
    streams = []
    for line in playlist.splitlines():
        if line and not line.startswith('#'):
            streams.append(media_base + line)

    return streams