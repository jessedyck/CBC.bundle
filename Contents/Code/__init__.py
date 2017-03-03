import sys, traceback

####################################################################################################
#CBC.CA Video Plugin
#Written by mysciencefriend
#Overhauled and updated by Mikedm139
#Overhauled and updated again by jessedyck
#Use at your own risk, etc. etc.
#

#### General globals
ART                 = 'art-default.jpg'
ICON                = 'icon-default.jpg'
RADIO_ICON          = 'cbc-radio.jpg'
CACHE_TIME          = CACHE_1HOUR

#### Watch.cbc.ca globals
SHOWS_LIST          = 'https://api-cbc.cloud.clearleap.com/cloffice/client/web/browse/babb23ae-fe47-40a0-b3ed-cdc91e31f3d6'
DOCS_LIST           = 'https://api-cbc.cloud.clearleap.com/cloffice/client/web/browse/d1c2427d-988b-4111-a63a-fffad4406ac7'
KIDS_LIST           = 'https://api-cbc.cloud.clearleap.com/cloffice/client/web/browse/d322ffe3-d8fc-40f0-a80a-a93239de3876'
RESULTS_PER_PAGE    = 30
NAMESPACES          = {'media': 'http://search.yahoo.com/mrss/', 'clearleap': 'http://www.clearleap.com/namespace/clearleap/1.0/'}
SHOW_TYPES          = ['season', 'series', 'seasonless_show']

#### Radio Globals
RADIO_FE_BASE       = 'http://www.cbc.ca/listen/'
RADIO_FE_CATS       = RADIO_FE_BASE + 'categories/'
RADIO_FE_SHOWS      = RADIO_FE_BASE + 'shows/'
RADIO_BASE          = 'https://api-gw.radio-canada.ca/audio/v1/'
RADIO_CATS          = RADIO_BASE + 'categories/'
RADIO_SHOWS         = RADIO_BASE + 'shows/'
RADIO_CLIPS         = RADIO_BASE + 'clips/'
RADIO_LIVE_URL      = 'http://tpfeed.cbc.ca/f/ExhSPC/cbc-live-radio'
RADIO_LIVE_STATIONS = {
    'radioone': [],
    'radiotwo': []
}

### Old cbc.ca player globals
CBC_CA_BASE         = 'http://www.cbc.ca'
PLAYER_URL          = CBC_CA_BASE + '/player/%s'
VIDEO_URL           = PLAYER_URL % 'play/'
LIVE_SPORTS         = PLAYER_URL % 'sports/Live'
NHL_URL             = CBC_CA_BASE  + '/sports/hockey/nhl'
JSON_URL            = CBC_CA_BASE  + '/json/cmlink/%s'
RE_THUMB_URL        = Regex('background-image: url\(\'(?P<url>http://.+?jpg)\'\)')
CATEGORIES          = ['News', 'Sports']



####################################################################################################
def Start():

    # Setup the default breadcrumb title for the plugin
    ObjectContainer.title1 = 'CBC'

    Logger('Starting up the CBC channel')
    Logger('*' * 80)
    Logger('Platform.OS            = {}'.format(Platform.OS))
    Logger('Platform.OSVersion     = {}'.format(Platform.OSVersion))
    Logger('Platform.CPU           = {}'.format(Platform.CPU))
    Logger('Platform.ServerVersion = {}'.format(Platform.ServerVersion))
    Logger('*' * 80)

    HTTP.ClearCache()


####################################################################################################
@handler('/video/cbc', 'CBC', art=ART, thumb=ICON)
def MainMenu():

    Logger('Displaying CBC Main Menu')

    oc = ObjectContainer()

    # Add watch.cbc.ca sources
    oc.add(DirectoryObject(key=Callback(Shows, link=SHOWS_LIST),
        title='Shows',
        thumb = R(ICON)
    ))

    oc.add(DirectoryObject(key=Callback(Shows, link=DOCS_LIST),
        title='Docs',
        thumb = R(ICON)
    ))

    oc.add(DirectoryObject(key=Callback(Shows, link=KIDS_LIST),
        title='Kids',
        thumb = R(ICON)
    ))

    # Add cbc.ca player sources
    oc.add(DirectoryObject(key=Callback(HockeyNightInCanada), title='Hockey Night In Canada'))
    oc.add(DirectoryObject(key=Callback(LiveSports), title='Live Sports'))

    for category in CATEGORIES:
        oc.add(DirectoryObject(
            key = Callback(Category, category=category),
            title = category
        ))


    # Add Radio items
    oc.add(DirectoryObject(key=Callback(RadioCategories, url=RADIO_CATS), title='Radio Categories', thumb=R(RADIO_ICON)))
    oc.add(DirectoryObject(key=Callback(RadioShows, url=RADIO_SHOWS), title='Radio Shows', thumb=R(RADIO_ICON)))
    oc.add(DirectoryObject(key=Callback(RadioLive, radio='one'), title='Radio One', thumb=R(RADIO_ICON)))
    oc.add(DirectoryObject(key=Callback(RadioLive, radio='two'), title='Radio Two', thumb=R(RADIO_ICON)))

    oc.add(
        PrefsObject(
            title='Preferences'
        )
    )

    # oc.add(SearchDirectoryObject(
    #     identifier = 'com.plexapp.plugins.cbcnewsnetwork',
    #     title = 'Search',
    #     summary = 'Search CBC videos',
    #     prompt = 'Search for...'
    # ))

    return oc

####################################################################################################
## Function used for watch.cbc.ca
@route('/video/cbc/shows')
def Shows(link, offset=0):
    offset = int(offset)
    link = StripHTTPS(link)

    Logger('Loading content from {}'.format(link), 'info')
    Logger('Content offset: {}'.format(offset))

    try:
        page = XML.ElementFromURL(link + '?offset=' + str(offset), cacheTime=CACHE_TIME)

        num_items = int(page.xpath('//clearleap:totalResults/text()', namespaces=NAMESPACES)[0])

    except:
        return handleHTTPException(sys.exc_info())

    page_title = page.xpath('//category/text()')[0].split('/')[0]
    shows = page.xpath('//item')

    oc = ObjectContainer(title2=page_title)
    

    for show in shows:
        title = show.xpath('.//title')[0].text

        # Link to the show episode/series list
        show_link = StripHTTPS(show.xpath('.//link')[0].text)

        thumbs = GetThumbsFromElement(show.xpath('.//media:thumbnail', namespaces=NAMESPACES))


        oc.add(DirectoryObject(
            key = Callback(DisplayShowItems, title=title, link=show_link),
            thumb = Resource.ContentsOfURLWithFallback(url=thumbs),
            title = title
        ))

    if (offset + RESULTS_PER_PAGE < num_items):
        oc.add(DirectoryObject(
            key = Callback(Shows, link=link, offset=offset+RESULTS_PER_PAGE),
            title = 'More...'
        ))

    if len(oc) < 1:
        return ObjectContainer(header="Sorry", message="There are no shows currently available.")
    else:
        return oc

####################################################################################################
## Function used for watch.cbc.ca
@route('/video/cbc/showepisodes')
def DisplayShowItems(title=None, link=None, offset=0):
    oc = ObjectContainer (title2=title)
    Logger('Loading content from {}'.format(link), 'info')
    Logger('Show: {}'.format(title))
    Logger('Offset: {}'.format(offset))
    
    link = StripHTTPS(link)

    try:
        page = XML.ElementFromURL(link + '?offset=' + str(offset), cacheTime=CACHE_TIME)

    except:
        return handleHTTPException(sys.exc_info())

    num_items = int(page.xpath('//clearleap:totalResults', namespaces=NAMESPACES)[0].text)


    items = page.xpath('//item')
    parent_url = page.xpath('//clearleap:parentFolderUri/text()', namespaces=NAMESPACES)

    for item in items:
        video_title = item.xpath('.//title/text()')

        # If there's less than 1 title returned, bail
        # otherwise, we can assume the rest of the properties exist too
        if len(video_title) < 1:
            Logger('No episode titles returned from {}'.format(link), 'error')
            raise Ex.MediaNotAvailable

        video_title = video_title[0]
        url = StripHTTPS(item.xpath('.//link/text()')[0])
        guid = item.xpath('.//guid/text()')[0]
        summary = item.xpath('.//description/text()')
        summary = summary[0] if len(summary) > 0 else None

        # Get thumbnails; if none exist, let the framework deal with fallback
        # Note that HTTPS is stripped in GetThumbsFromElement
        thumbs = GetThumbsFromElement(item.xpath('.//media:thumbnail', namespaces=NAMESPACES))
        Logger('Got thumbnails: {}'.format('; '.join(thumbs)))

        # Keywords are used on first-level media containers, or second-level season containers
        # to group a seasoned show, series or season-less show. On an actual media item,
        # keyword contains the actual show-type, eg: Drama, Documentary
        # 
        # Routing values are stored in SHOW_TYPES

        keywords = item.xpath('.//media:keywords/text()', namespaces=NAMESPACES)
        item_type = item.xpath('.//clearleap:itemType/text()', namespaces=NAMESPACES)
        
        # Some additional metadata for use on various containers
        season_num = item.xpath('.//clearleap:season/text()', namespaces=NAMESPACES)
        season_num = int(season_num[0]) if len(season_num) > 0 else None
        episode_num = item.xpath('.//clearleap:episodeInSeason/text()', namespaces=NAMESPACES)
        episode_num = int(episode_num[0]) if len(episode_num) > 0 else None

        Logger ('Season: {}'.format(season_num))
        Logger ('Episode: {}'.format(episode_num))
        Logger ('Item title: {}'.format(video_title))


        # TOP LEVEL SHOW LISTING
        # Will always be one of either 'series' or 'seasonless_show'
        if ('series' == keywords[0] or 'seasonless_show' == keywords[0]):
            Logger('Adding a show to the container')

            item_obj = TVShowObject(
                key = Callback(DisplayShowItems, link=url, title=video_title),
                rating_key = guid,
                title = video_title,
                summary = summary,
                thumb = Resource.ContentsOfURLWithFallback(url=thumbs) 
            )

        
        elif 'season' == keywords[0]:
            # LISTING OF SEASONS IN SHOW

            # Getting list of seasons
            Logger('Adding a season to the container')
            item_obj = SeasonObject(
                key = Callback(DisplayShowItems, link=url, title=video_title),
                rating_key = guid,
                title = video_title,
                summary = summary,
                thumb = Resource.ContentsOfURLWithFallback(url=thumbs)
            )
            
        else:
            # VIDEO ITEM
            # Possibly episode in season, or seasonless video

            Logger('Adding a final video to the container')

            if (season_num):
                item_obj = EpisodeObject()
                item_obj.index = episode_num
                item_obj.season = season_num
            else:
                item_obj = VideoClipObject()

            item_obj.url = url
            item_obj.title = video_title
            item_obj.summary = summary
            item_obj.thumb = Resource.ContentsOfURLWithFallback(url=thumbs)

        oc.add(item_obj)
    # END forloop

    if (offset + RESULTS_PER_PAGE < num_items):
        oc.add(DirectoryObject(
            key = Callback(Shows, link=link, offset=offset+RESULTS_PER_PAGE),
            title = 'More...'
        ))

    if len(oc) < 1:
        Logger('No videos found at {}'.format(link), 'error')
        return ObjectContainer(header="Sorry", message="There are no videos currently available for this show.")
    else:
        return oc

####################################################################################################
## Function used for CBC Radio
@route('/video/cbc/radiocategories')
def RadioCategories(url):

    oc = ObjectContainer(title2='CBC Radio Categories')

    if not Prefs['enable_https']:
        Logger('CBC Radio API requires HTTPS', 'info')

    try:
        cats = JSON.ObjectFromURL(url, cacheTime=CACHE_TIME)

        if (len(cats) < 1):
            Logger('No Radio categories found at URL: {}', 'error')
            raise Ex.MediaNotAvailable
    except:
        return handleHTTPException(sys.exc_info())

    # Response is an array of objects. EG:
    #   "id": 1,
    #   "name": "News",
    #   "image": "http://www.cbc.ca/radio/includes/apps/images/category/category-news.jpg",
    #   "slugName": "news"

    for cat in cats:
        oc.add(DirectoryObject(
            key = Callback(RadioItems, url=RADIO_CATS + cat['slugName'], title=cat['name']),
            title = cat['name'],
            thumb = Resource.ContentsOfURLWithFallback(cat['image'])
        ))

    if len(oc) < 1:
        Logger('No radio categories found at {}'.format(url), 'error')
        return ObjectContainer(header="No Categories", message="Sorry, no categories were found.")
    else:
        return oc

####################################################################################################
## Function used for CBC Radio
# 
# Start pageoffset at 1 since the first run-thru gets us the first page of results
@route('/video/cbc/radioitems')
def RadioItems(url, title=None, pageoffset=1):
    oc = ObjectContainer(title2=title or 'CBC Radio')

    if not Prefs['enable_https']:
        Logger('CBC Radio API requires HTTPS', 'info')


    # There does not seem to be a way to override this in the API
    pagesize = 10;

    url_new = url + '/clips/?page=' + str(pageoffset)
    Logger('Loading radio items at URL: {}'.format(url_new))

    try:
        items = JSON.ObjectFromURL(url_new, cacheTime=CACHE_TIME)

        if len(items) < 1:
            Logger('No radio items found for {}'.format(title))
            raise Ex.MediaNotAvailable
    except:
        return handleHTTPException(sys.exc_info())

    # EXAMPLE ITEM IN RESPONSE
    # {
    #     "id": 159140,
    #     "showId": 7,
    #     "title": "CBC News: Hourly Edition for 2016/10/17 at 22:00 EDT",
    #     "description": "The latest national and international news, updated every hour",
    #     "duration": 270,
    #     "durationPretty": "00:04:30",
    #     "url": "http://podcast.cbc.ca/mp3/hourlynews.mp3",
    #     "clipType": "Segment",
    #     "releasedAt": 1476756000000,
    #     "releasedAtPretty": "2016-10-18 02:00 AM GMT",
    #     "categories": [{
    #         "id": 1,
    #         "name": "News",
    #         "image": "http://www.cbc.ca/radio/includes/apps/images/category/category-news.jpg",
    #         "slugName": "news"
    #     }],
    #     "airdates": [1410118677644],
    #     "podcastable": false,
    #     "geoTarget": "Global"
    # }

    for item in items:
        oc.add(TrackObject(
            url = RADIO_CLIPS + str(item['id']),
            title = item['title'],
            summary = item['description'],
            duration = int(item['duration']) * 1000,
            originally_available_at = Datetime.ParseDate(item['releasedAtPretty']).date()
        ))

    if not len(items) < pagesize:
        oc.add(DirectoryObject(
            key = Callback(RadioItems, url=url, pageoffset=int(pageoffset) + 1),
            title = 'More...',
            thumb=R(RADIO_ICON)
        ))
    else:
        Logger('No more items found at URL: ' + url)

    return oc

####################################################################################################
## Function used for CBC Radio
# 
@route('/video/cbc/radioshows')
def RadioShows(url, pageoffset=1):
    oc = ObjectContainer(title2='CBC Radio Shows')

    # url = StripHTTPS(url)

    if not Prefs['enable_https']:
        Logger('CBC Radio API requires HTTPS', 'info')

    try:
        shows = JSON.ObjectFromURL(url + '?pageSize=' + str(RESULTS_PER_PAGE) + '&page=' + str(pageoffset), cacheTime=CACHE_TIME)

        if len(shows) < 1:
            Logger('No radio shows found for {} with offset {}'.format(url, offset))
            raise Ex.MediaNotAvailable
    except:
        return handleHTTPException(sys.exc_info())

    # {
    #     "id": 10,
    #     "title": "CBC News: World Report",
    #     "description": "World Report is news that has broken overnight with a look ahead to the day's expected events. The program features the latest international news, as well as the top domestic stories. It is also an outlet for CBC journalists to break original stories. ",
    #     "network": "Radio One",
    #     "thumbnail": "http://www.cbc.ca/radio/podcasts/images/320x320/worldreport-podcast-template.jpg",
    #     "image": "http://www.cbc.ca/radio/podcasts/images/950x950/worldreport-podcast-template.jpg",
    #     "coverImage": "http://www.cbc.ca/radio/includes/apps/images/coverimage/worldreport-header.jpg",
    #     "webUrl": "http://www.cbc.ca/worldreport//",
    #     "backgroundImage": "http://www.cbc.ca/radio/includes/apps/images/showgradientbg/worldreport-gradient-bg.jpg",
    #     "clipCount": 1,
    #     "sortTitle": "CBC News: World Report",
    #     "slugTitle": "cbc-news-world-report",
    #     "downloadPermitted": true,
    #     "hostImage": "http://www.cbc.ca/radio/podcasts/images/hosts/World-Report-circle.png",
    #     "hosts": [{
    #         "id": 10, 
    #         "name": "First Last"
    #     }, {
    #         "id": 141,
    #         "name": "First Last"
    #     }]
    # }

    for show in shows:
        oc.add(DirectoryObject(
            key=Callback(RadioItems, url=RADIO_SHOWS + show['slugTitle'], title=show['title']),
            title=show['title'],
            thumb = Resource.ContentsOfURLWithFallback(url=show['thumbnail'], fallback=RADIO_ICON),
            art=Resource.ContentsOfURLWithFallback(show['backgroundImage'])
        ))

    # As long as the number of shows returned is not less than the page size, 
    # assume we have more pages
    if not len(shows) < RESULTS_PER_PAGE:
        oc.add(DirectoryObject(
            key = Callback(RadioShows, url=url, pageoffset=int(pageoffset) + 1),
            title = 'More...',
            thumb=R(RADIO_ICON)
        ))

    return oc


####################################################################################################
## Function used for CBC Radio
# 
@route('/video/cbc/radiolive')
def RadioLive (radio='one'):
    oc = ObjectContainer(title2='CBC Radio ' + radio.title())

    # Can't get live streams? Bail
    if not PopulateRadioLiveStations():
        return ObjectContainer(header="No Items", message="Sorry, no items were found.")

    for stream in RADIO_LIVE_STATIONS['radio' + radio]:
        Logger('Got station: ' + stream['title'])

        # thumbs = []

        # if (stream['thumbnails'] and not ENABLE_HTTPS):
        #     for thumb in stream['thumbnails']:
        #         thumbs.append(StripHTTPS(thumb))


        to = TrackObject(
            url = RADIO_LIVE_URL + '/' + str(stream['guid']),
            title = stream['cbc$name'],
            album = stream['cbc$name'],
            artist = stream['cbc$network'],
            thumb = Resource.ContentsOfURLWithFallback(url=stream['thumbnails'], fallback=RADIO_ICON) if stream['thumbnails'] else R(RADIO_ICON)
        )

        # Get the name of the current live program and tack it on to the object
        #
        # TODO: This is commented because it makes an HTTP request for each station and takes 
        # a long time to complete. Need a more performant solution
        # metadata_url = GetLiveMetadataURL(stream['content'])

        # if (metadata_url):
        #     program_name = GetLiveProgramName(metadata_url)

        #     if program_name:
        #         to.title = program_name

        oc.add(to)

    return oc


####################################################################################################
## Function used for cbc.ca player
@route('/video/cbc/hnic')
def HockeyNightInCanada():

    oc = ObjectContainer(title2='Hockey Night In Canada')
    page = HTML.ElementFromURL(NHL_URL, cacheTime=CACHE_TIME)

    try:
        live_url = page.xpath('//li[@class="ticker-item live "]//a')[0].get('href')
        gid = RE_GID.search(live_url).group('gid')
        data = JSON.ObjectFromURL(JSON_URL % gid)['leadmedia']

        title = data['title']
        summary = data['description']
        thumb = data['headlineimage']['url']
        vid = data['releaseid']
        url = VIDEO_URL + vid

        oc.add(VideoClipObject(
            url = url,
            title = title,
            summary = summary,
            thumb = thumb
        ))

    except:
        return ObjectContainer(header="No Live Games Now", message="No live games found. Please try again another time.")

####################################################################################################
## Function used for cbc.ca player
@route('/video/cbc/sports')
def LiveSports():

    oc = ObjectContainer()
    page = HTML.ElementFromURL(LIVE_SPORTS, cacheTime=CACHE_TIME)

    for item in page.xpath('//section[@class="category-content full"]//li[@class="medialist-item"]'):

        link = item.xpath('./a')[0].get('href')
        if CBC_CA_BASE not in link:
            link = CBC_CA_BASE + link
        thumb = item.xpath('.//img')[0].get('src')
        date = item.xpath('.//span[@class="medialist-date"]')[0].text
        title = item.xpath('.//div[@class="medialist-title"]')[0].text

        oc.add(VideoClipObject(
            url = link,
            title = title,
            originally_available_at = Datetime.ParseDate(date).date(),
            thumb = Resource.ContentsOfURLWithFallback(url=thumb)
        ))

    if (len(oc) < 1):
        return ObjectContainer(header="No Live Sports Now", message="No live sports found. Please try again another time.")

    return oc

####################################################################################################
## Function used for cbc.ca player
@route('/video/cbc/category')
def Category(category=None, link=None):
    Logger('Entering CBC.ca player category. Category: ' + (category or '') + ' Link: ' + (link or ''))

    oc = ObjectContainer(title2=category)

    if link:
        page = HTML.ElementFromURL(link, cacheTime=CACHE_TIME)
    else:
        page = HTML.ElementFromURL(PLAYER_URL % category.lower(), cacheTime=CACHE_TIME)
        oc.add(DirectoryObject(key=Callback(Featured, category=category), title="Featured"))

    for item in page.xpath('.//ul[@class="longlist-list"]//a'):

        title = item.text
        link = item.get('href')
        if CBC_CA_BASE not in link:
            link = CBC_CA_BASE + link
        oc.add(DirectoryObject(
            key = Callback(ShowsMenu, title=title, link=link),
            title = title
        ))

    for item in page.xpath('//li[contains(@class,"medialist-item")]'):

        url = item.xpath('.//a')[0].get('href')
        if not "watch.cbc.ca" in url:
            if CBC_CA_BASE not in url:
                url = CBC_CA_BASE + url

            thumb = item.xpath('.//img')[0].get('src')
            date = Datetime.ParseDate(item.xpath('.//span[@class="medialist-date"]')[0].text).date()

            try:
                duration = Datetime.MillisecondsFromString(item.xpath('.//span[@class="medialist-duration"]')[0].text)
            except:
                duration = 0

            title= item.xpath('.//div[@class="medialist-title"]')[0].text

            oc.add(VideoClipObject(
                url = url,
                title = title,
                duration = duration,
                originally_available_at = date,
                thumb = Resource.ContentsOfURLWithFallback(url=thumb, fallback=ICON)
            ))
    
    return oc

####################################################################################################
## Function used for cbc.ca player
@route('/video/cbc/show')
def ShowsMenu(title, link):
    Logger("Entering CBC.ca player shows menu. URL: " + link)

    oc = ObjectContainer(title2=title)
    page = HTML.ElementFromURL(link, cacheTime=CACHE_TIME)

    ''' If the page includes a list of seasons or other sub-divisions, use the Category() function to parse them '''
    try:
        seasons = page.xpath('//div[@class="longlist"]//a')

        if len(seasons) > 0:
            return Category(category=title, link=link)
    except:
        pass

    for item in page.xpath('//li[contains(@class,"medialist-item")]'):

        url = item.xpath('.//a')[0].get('href')
        if not "watch.cbc.ca" in url:
            if CBC_CA_BASE not in url:
                url = CBC_CA_BASE + url

            thumb = item.xpath('.//img')[0].get('src')
            date = Datetime.ParseDate(item.xpath('.//span[@class="medialist-date"]')[0].text).date()

            try:
                duration = Datetime.MillisecondsFromString(item.xpath('.//span[@class="medialist-duration"]')[0].text)
            except:
                duration = 0

            title = item.xpath('.//div[@class="medialist-title"]')[0].text

            oc.add(VideoClipObject(
                url = url,
                title = title,
                duration = duration,
                originally_available_at = date,
                thumb = Resource.ContentsOfURLWithFallback(url=thumb, fallback=ICON)
            ))

    return oc


####################################################################################################
## Function used for cbc.ca player
@route('/video/cbc/featured')
def Featured(category=None):
    Logger("Entering CBC.ca player Featured method. Category: " + category)

    oc = ObjectContainer(title2=category)
    page = HTML.ElementFromURL(PLAYER_URL % category.lower(), cacheTime=CACHE_TIME)

    for item in page.xpath('//div[@class="featured-container"]'):

        url = item.xpath('./a')[0].get('href')

        if CBC_CA_BASE not in url:
            url = CBC_CA_BASE + url

        thumb = item.xpath('.//img')[0].get('src')
        title = item.xpath('.//p[@class="featured-title"]')[0].text
        date = Datetime.ParseDate(item.xpath('.//p[@class="featured-date"]')[0].text).date()

        try:
            duration = Datetime.MillisecondsFromString(item.xpath('.//p[@class="featured-duration"]')[0].text)
        except:
            duration = 0

        summary = item.xpath('.//p[@class="featured-description"]')[0].text

        oc.add(VideoClipObject(
            url = url,
            title = title,
            duration = duration,
            originally_available_at = date,
            summary = summary,
            thumb = Resource.ContentsOfURLWithFallback(url=thumb, fallback=ICON)
        ))

    return oc


####################################################################################################
# UTILITY FUNCTIONS - Not hooked up to routers
####################################################################################################

# Get all thumbs, sort by resolution, then return a list of URLs
#
# EXAMPLE dict used to sort
# [{'url': 'http://a.com', 'profile': 'test', 'width': 100, 'height': 100, 'resolution': 10000},{'url': 'http://g.com', 'profile': 'test', 'width': 100, 'height': 100, 'resolution': 543068},{'url': 'http://s.com', 'profile': 'test', 'width': 100, 'height': 100, 'resolution': 3520},{'url': 'http://b.com', 'profile': 'test', 'width': 100, 'height': 100, 'resolution': 59802572}]
def GetThumbsFromElement(elm):

    thumbs = []

    # Generate a list of image dicts
    i = 0;
    while i < len(elm):
        if elm[i].get('url') and elm[i].get('width') and elm[i].get('height'):
            thumbs.append ({
                'url': StripHTTPS(elm[i].get('url')),
                'profile': elm[i].get('profile'),
                'width': int(elm[i].get('width')),
                'height': int(elm[i].get('height')),
                'resolution': int(elm[i].get('height')) * int(elm[i].get('width'))
            })
        else:
            Logger('Excluding thumbnail: ' + elm[i].get('url'))

        i += 1

    # Sort thumbs by resolution, using the Pref to dictate high quality (sorted in reserve/desc)
    # or low quality first (sorted in asc order)
    thumbs = sorted(thumbs, key=lambda thumb:thumb.get('resolution'), reverse=Prefs['high_quality_thumbs'])

    # Generate a list of thumbnail URLs
    i = 0;
    while i < len(thumbs):
        thumbs[i] = thumbs[i]['url']
        i += 1
    
    return thumbs

####################################################################################################
def PopulateRadioLiveStations ():
    global RADIO_LIVE_STATIONS

    if not Prefs['enable_https']:
        Logger('CBC Radio API requires HTTPS')

    # if our 'cache' is already primed, bail early
    if (len(RADIO_LIVE_STATIONS['radioone']) > 0):
        return True

    try:
        streams_json = JSON.ObjectFromURL(RADIO_LIVE_URL, cacheTime=CACHE_TIME)
    except:
        return handleHTTPException(sys.exc_info())

    try:
        streams = streams_json['entries']

    except:
        Logger('Error getting CBC Radio streams' 'error')
        return False

    for stream in streams:
        if (stream['cbc$network'] == 'Radio One'):
            RADIO_LIVE_STATIONS['radioone'].append(stream)
        else:
            RADIO_LIVE_STATIONS['radiotwo'].append(stream)

    return True

####################################################################################################
# Takes the stream['content'] array of media content from a live stream JSON entry, and 
# returns the url of the containing Metadata URL
def GetLiveMetadataURL (item):
    for i in item:
        if 'Metadata' in i['assetTypes']:
            return i['streamingUrl']

    return False

####################################################################################################
# Gets the name of the currently-playing program of a live radio station
# URL example: http://www.cbc.ca/programguide/live.do?output=xml&networkKey=cbc_radio_one&locationKey=inuvik
def GetLiveProgramName(url):
    # Don't cache metadata URL, since the currently-playing program
    # will constantly change
    metadata = XML.ElementFromURL(url=url, cacheTime=0)
    
    program_name = metadata.xpath('//name/text()')

    if (len(program_name) > 0):
        Logger('Current program: ' + program_name[0])
        return program_name[0]

    return False

####################################################################################################
# Depending on the global variable, strip the HTTPS and use HTTP connections only.
# This functionality is assuming that if the URL Service is passed an HTTP URL, 
# the following requests should be HTTP
def StripHTTPS (url):
    if not Prefs['enable_https']:
        Logger('Stripping HTTPS from ' + url)
        url = url.replace('https://', 'http://')

    return url

####################################################################################################
# Inspired by: https://github.com/Twoure/KissNetwork.bundle/blob/7230f39a02118b81b3b123512b3dde8ac0d6e5f4/Contents/Code/__init__.py#L1763
# Usage examples:
#             Logger('* ep_count = {}'.format(ep_count))
#             Logger('* new season list = {}'.format(nseason_list))

# @route('/video/cbc/logger', force=bool)
def Logger(message, kind=None, force=False):

    kind = kind.lower() if kind else None
    message = '* ' + message

    # If debug pref is enabled, log all debug messages as well as explict messages
    # If debug is not set, only log explicit messages unless forced
    if ((force or Prefs['debug']) and (kind == None or kind == 'debug')):
        Log.Debug(message)
    elif kind == 'info':
        Log.Info(message)
    elif kind == 'warn':
        Log.Warn(message)
    elif kind == 'error':
        Log.Error(message)
    elif kind == 'critical':
        Log.Critical(message)
    else:
        pass

    return

# Handle errors from HTTP requests and return an ObjectContainer
# with a meaningful error to the client
def handleHTTPException (e=None):
    if not e:
        Logger('Exception. No exception information caught.')
        return ObjectContainer(header='Sorry', message='Unknown exception.')

    etype = e[0]
    evalue = e[1]
    
    if (Prefs['debug']):
        etraceback = traceback.format_list(traceback.extract_tb(e[2]))
        Logger('Beginning exception trace:', 'info')
        Logger('*' * 80, 'info')

        for stack in etraceback:
            Logger(stack, 'error')
        Logger('*' * 80, 'info')
        Logger('End exception trace.', 'info')

    # Errors with an HTTP response code
    if (etype == 'HTTPError'):
        if (etype.code == 403):
            Logger('HTTP 403 - CBC GeoBlocked')
            return ObjectContainer(header='Region Locked', message='CBC is only accessible within Canada')
        elif (etype.code == 404):
            Logger('HTTP 404 - No content was found')
            return ObjectContainer(header='Sorry', message='Nothing was found here. Error 404.')
        else:
            Logger('HTTP Error: {}').format(etype.code)
            return ObjectContainer(header='Sorry', message='Could not contact CBC to get the show list. Try again. Error: {}'.format(etype.code))
    
    #Errors initiating the request, eg: no internet connection
    elif (etype == 'URLError'):
        Logger('URL Error: {}'.format(etype.reason), error)
        return ObjectContainer(header='Sorry', message='Could not contact CBC to get the show list. Try again. Unknown error.')
    else:
        Logger('Exception {}: {}'.format(etype, evalue), 'error')
        return ObjectContainer(header='Sorry', message='Could not find a show list.')
