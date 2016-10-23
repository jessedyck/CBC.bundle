####################################################################################################
#CBC.CA Video Plugin
#Written by mysciencefriend
#Overhauled and updated by Mikedm139
#Overhauled and updated again by jessedyck
#Use at your own risk, etc. etc.
#
### TODO: Re-add Radio category - this has moved to cbc.ca/listen/


#### General globals
ART  = 'art-default.jpg'
ICON = 'icon-default.jpg'

#### Watch.cbc.ca globals
SHOWS_LIST          = 'https://api-cbc.cloud.clearleap.com/cloffice/client/web/browse/babb23ae-fe47-40a0-b3ed-cdc91e31f3d6'
DOCS_LIST           = 'https://api-cbc.cloud.clearleap.com/cloffice/client/web/browse/d1c2427d-988b-4111-a63a-fffad4406ac7'
KIDS_LIST           = 'https://api-cbc.cloud.clearleap.com/cloffice/client/web/browse/d322ffe3-d8fc-40f0-a80a-a93239de3876'
RESULTS_PER_PAGE    = 30
NAMESPACES          = {'media': 'http://search.yahoo.com/mrss/', 'clearleap': 'http://www.clearleap.com/namespace/clearleap/1.0/'}
SHOW_TYPES          = ['season', 'series', 'seasonless_show']

#### Radio Globals
RADIO_FE_BASE = 'http://www.cbc.ca/listen/'
RADIO_FE_CATS = RADIO_FE_BASE + 'categories/'
RADIO_FE_SHOWS = RADIO_FE_BASE + 'shows/'
RADIO_BASE = 'https://api-gw.radio-canada.ca/audio/v1/'
RADIO_CATS = RADIO_BASE + 'categories/'
RADIO_SHOWS = RADIO_BASE + 'shows/'
RADIO_CLIPS = RADIO_BASE + 'clips/'
RADIO_LIVE_URL = 'http://tpfeed.cbc.ca/f/ExhSPC/cbc-live-radio'
RADIO_LIVE_STATIONS = {
    'radioone': [],
    'radiotwo': []
}

### Old cbc.ca player globals
CBC_CA_BASE        = 'http://www.cbc.ca'
PLAYER_URL          = CBC_CA_BASE + '/player/%s'
VIDEO_URL           = PLAYER_URL % 'play/'
LIVE_SPORTS         = PLAYER_URL % 'sports/Live'
NHL_URL             = CBC_CA_BASE  + '/sports/hockey/nhl'
JSON_URL            = CBC_CA_BASE  + '/json/cmlink/%s'
RE_THUMB_URL=   Regex('background-image: url\(\'(?P<url>http://.+?jpg)\'\)')
CATEGORIES  = ['News', 'Sports']



####################################################################################################
def Start():
    # Setup the default breadcrumb title for the plugin
    ObjectContainer.title1 = 'CBC'

    Log.Debug('Starting up the CBC channel')


####################################################################################################
@handler('/video/cbc', 'CBC', art=ART, thumb=ICON)
def MainMenu():

    Log.Debug('Displaying CBC Main Menu')

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
    oc.add(DirectoryObject(key=Callback(RadioCategories, url=RADIO_CATS), title='Radio Categories', thumb=R('cbc-radio.jpg')))
    oc.add(DirectoryObject(key=Callback(RadioShows, url=RADIO_SHOWS), title='Radio Shows', thumb=R('cbc-radio.jpg')))
    oc.add(DirectoryObject(key=Callback(RadioLive, radio='one'), title='Radio One', thumb=R('cbc-radio.jpg')))
    oc.add(DirectoryObject(key=Callback(RadioLive, radio='two'), title='Radio Two', thumb=R('cbc-radio.jpg')))

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
def Shows(link=SHOWS_LIST, offset=0):
    offset = int(offset)

    page = XML.ElementFromURL(link + '?offset=' + str(offset))

    try:
        num_items = int(page.xpath('//clearleap:totalResults/text()', namespaces=NAMESPACES)[0])
    except:
        return ObjectContainer(header="Sorry", message="There are no shows currently available.")


    page_title = page.xpath('//category/text()')[0].split('/')[0]
    shows = page.xpath('//item')

    oc = ObjectContainer(title2=page_title)
    

    for show in shows:
        title = show.xpath('.//title')[0].text

        # Link to the show episode/series list
        show_link = show.xpath('.//link')[0].text

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
    Log.Debug('Show Title: ' + title)

    page = XML.ElementFromURL(link + '?offset=' + str(offset))

    num_items = int(page.xpath('//clearleap:totalResults', namespaces=NAMESPACES)[0].text)


    items = page.xpath('//item')
    parent_url = page.xpath('//clearleap:parentFolderUri/text()', namespaces=NAMESPACES)

    for item in items:
        video_title = item.xpath('.//title/text()')

        # If there's less than 1 title returned, bail
        # otherwise, we can assume the rest of the properties exist too
        if len(video_title) < 1:
            raise Ex.MediaNotAvailable

        video_title = video_title[0]
        url = item.xpath('.//link/text()')[0]
        summary = item.xpath('.//description/text()')[0]
        guid = item.xpath('.//guid/text()')[0]

        # THUMBNAIL size exists on episodes, but not on seasons
        # If BANNER size fails as well, let the callback in the metadata object handle the fallback
        thumbs = GetThumbsFromElement(item.xpath('.//media:thumbnail', namespaces=NAMESPACES))


        # Keywords are used on first-level media containers, or second-level season containers
        # to group a seasoned show, series or season-less show. On an actual media item,
        # keyword contains the actual show-type, eg: Drama, Documentary
        # 
        # Routing values are stored in SHOW_TYPES

        keywords = item.xpath('.//media:keywords/text()', namespaces=NAMESPACES)
        item_type = item.xpath('.//clearleap:itemType/text()', namespaces=NAMESPACES)
        


        # First level navigation (eg: list of seasons)
        if (keywords[0] in SHOW_TYPES and not parent_url):
            Log.Debug('Adding a show to the container')

            item_obj = TVShowObject(
                key = Callback(DisplayShowItems, link=url, title=video_title),
                rating_key = guid,
                title = video_title,
                summary = summary,
                thumb = Resource.ContentsOfURLWithFallback(url=thumbs) 
            )

        # Second level navigation (eg: seasons episodes list)
        elif (keywords[0] in SHOW_TYPES and parent_url):

            # Getting list of seasons
            if ('season' in keywords):
                Log.Debug('Adding a season to the container')
                item_obj = SeasonObject(
                    key = Callback(DisplayShowItems, link=url, title=video_title),
                    rating_key = guid,
                    title = video_title,
                    summary = summary,
                    thumb = Resource.ContentsOfURLWithFallback(url=thumbs)
                )

        # Video item, possibly episode in season, or seasonless video
        else:
            Log.Debug('Adding a final video to the container')
            item_obj = VideoClipObject(
                url = url,
                title = video_title,
                summary = summary,
                thumb = Resource.ContentsOfURLWithFallback(url=thumbs)
            )

        oc.add(item_obj)

    if (offset + RESULTS_PER_PAGE < num_items):
        oc.add(DirectoryObject(
            key = Callback(Shows, link=link, offset=offset+RESULTS_PER_PAGE),
            title = 'More...'
        ))

    if len(oc) < 1:
        return ObjectContainer(header="Sorry", message="There aren't any videos currently available for this show.")
    else:
        return oc

####################################################################################################
## Function used for CBC Radio
@route('/video/cbc/radiocategories')
def RadioCategories(url):

    oc = ObjectContainer(title2='CBC Radio Categories')

    try:
        cats = JSON.ObjectFromURL(url)

        if (len(cats) < 1):
            Log.Debug('No Radio categories found at URL: ' + url)
            raise Ex.MediaNotAvailable
    except:
        return ObjectContainer(header="No Categories", message="Sorry, no categories were found.")

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

    # There does not seem to be a way to override this in the API
    pagesize = 10;

    url_new = url + '/clips/?page=' + str(pageoffset)
    Log.Debug('Loading radio items at URL: ' + url_new)

    items = JSON.ObjectFromURL(url_new)

    if len(items) < 1:
        return ObjectContainer(header="No Items", message="Sorry, no items were found.")

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
            thumb=R('cbc-radio.jpg')
        ))
    else:
        Log.Debug('No more items found at URL: ' + url)

    return oc

####################################################################################################
## Function used for CBC Radio
# 
@route('/video/cbc/radioshows')
def RadioShows(url, pageoffset=1):
    oc = ObjectContainer(title2='CBC Radio Shows')

    pagesize = 30;

    shows = JSON.ObjectFromURL(url + '?pageSize=' + str(pagesize) + '&page=' + str(pageoffset))

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
    #         "name": "David Common"
    #     }, {
    #         "id": 141,
    #         "name": "Marcia Young"
    #     }]
    # }

    if len(shows) < 1:
        return ObjectContainer(header="No Items", message="Sorry, no items were found.")

    for show in shows:
        oc.add(DirectoryObject(
            key=Callback(RadioItems, url=RADIO_SHOWS + show['slugTitle'], title=show['title']),
            title=show['title'],
            thumb = Resource.ContentsOfURLWithFallback(url=show['thumbnail'], fallback=R('cbc-radio.jpg')),
            art=Resource.ContentsOfURLWithFallback(show['backgroundImage'])
        ))

    # As long as the number of shows returned is not less than the page size, 
    # assume we have more pages
    if not len(shows) < pagesize:
        oc.add(DirectoryObject(
            key = Callback(RadioShows, url=url, pageoffset=int(pageoffset) + 1),
            title = 'More...',
            thumb=R('cbc-radio.jpg')
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
        Log.Debug('Got station: ' + stream['title'])

        oc.add(TrackObject(
            url = RADIO_LIVE_URL + '/' + str(stream['guid']),
            title = stream['cbc$name'],
            thumb = Resource.ContentsOfURLWithFallback(url=stream['thumbnails'], fallback=R('cbc-radio.jpg')) if stream['thumbnails'] else R('cbc-radio.jpg')
        ))

    return oc


####################################################################################################
## Function used for cbc.ca player
@route('/video/cbc/hnic')
def HockeyNightInCanada():

    oc = ObjectContainer(title2='Hockey Night In Canada')
    page = HTML.ElementFromURL(NHL_URL)

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
    page = HTML.ElementFromURL(LIVE_SPORTS)

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
    Log.Debug('Entering CBC.ca player category. Category: ' + (category or '') + ' Link: ' + (link or ''))

    oc = ObjectContainer(title2=category)

    if link:
        page = HTML.ElementFromURL(link)
    else:
        page = HTML.ElementFromURL(PLAYER_URL % category.lower())
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
    Log.Debug("Entering CBC.ca player shows menu. URL: " + link)

    oc = ObjectContainer(title2=title)
    page = HTML.ElementFromURL(link)

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
    Log.Debug("Entering CBC.ca player Featured method. Category: " + category)

    oc = ObjectContainer(title2=category)
    page = HTML.ElementFromURL(PLAYER_URL % category.lower())

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
def GetThumbsFromElement(elm):

    thumbs = []

    # Generate a list of image dicts
    i = 0;
    while i < len(elm):
        if elm[i].get('url') and elm[i].get('width') and elm[i].get('height'):
            thumbs.append ({
                'url': elm[i].get('url'),
                'profile': elm[i].get('profile'),
                'width': int(elm[i].get('width')),
                'height': int(elm[i].get('height')),
                'resolution': int(elm[i].get('height')) * int(elm[i].get('width'))
            })
        i += 1

    thumbs = sorted(thumbs, key=GetThumbsSortKey)

    i = 0;
    while i < len(thumbs):
        thumbs[i] = thumbs[i]['url']
        i += 1

    # Sort with smallest first
    return thumbs

####################################################################################################
def GetThumbsSortKey (item):
    return item['resolution']

####################################################################################################
def PopulateRadioLiveStations ():
    global RADIO_LIVE_STATIONS

    # if our 'cache' is already primed, bail early
    if (len(RADIO_LIVE_STATIONS['radioone']) > 0):
        return True

    streams_json = JSON.ObjectFromURL(RADIO_LIVE_URL)

    try:
        streams = streams_json['entries']

    except:
        Log.Debug('Error getting CBC Radio streams')
        return False

    for stream in streams:
        if (stream['cbc$network'] == 'Radio One'):
            RADIO_LIVE_STATIONS['radioone'].append(stream)
        else:
            RADIO_LIVE_STATIONS['radiotwo'].append(stream)

    return True