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

    Log('Starting up the CBC channel')


####################################################################################################
@handler('/video/cbc', 'CBC', art=ART, thumb=ICON)
def MainMenu():

    Log('Displaying CBC Main Menu')

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
    Log('Show Title: ' + title)

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
            Log('Adding a show to the container')

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
                Log('Adding a season to the container')
                item_obj = SeasonObject(
                    key = Callback(DisplayShowItems, link=url, title=video_title),
                    rating_key = guid,
                    title = video_title,
                    summary = summary,
                    thumb = Resource.ContentsOfURLWithFallback(url=thumbs)
                )

        # Video item, possibly episode in season, or seasonless video
        else:
            Log('Adding a final video to the container')
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
    Log('Entering CBC.ca player category. Category: ' + (category or '') + ' Link: ' + (link or ''))

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
    Log("Entering CBC.ca player shows menu. URL: " + link)

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
    Log("Entering CBC.ca player Featured method. Category: " + category)

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