####################################################################################################
#CBC.CA Video Plugin
#Written by mysciencefriend
#Overhauled and updated by Mikedm139
#Overhauled and updated again by jessedyck
#Use at your own risk, etc. etc.

ART  = 'art-default.jpg'
ICON = 'icon-default.jpg'

SHOWS_LIST  = 'https://api-cbc.cloud.clearleap.com/cloffice/client/web/browse/babb23ae-fe47-40a0-b3ed-cdc91e31f3d6'
DOCS_LIST = 'https://api-cbc.cloud.clearleap.com/cloffice/client/web/browse/d1c2427d-988b-4111-a63a-fffad4406ac7'
RESULTS_PER_PAGE = 30
NAMESPACES = {'media': 'http://search.yahoo.com/mrss/', 'clearleap': 'http://www.clearleap.com/namespace/clearleap/1.0/'}

SHOW_TYPES = ['season', 'series', 'seasonless_show']

def Start():
    # Setup the default breadcrumb title for the plugin
    ObjectContainer.title1 = 'CBC'

    Log('Starting up the CBC channel')



####################################################################################################
@handler('/video/cbc', 'CBC', art=ART, thumb=ICON)
def MainMenu():

    Log('Displaying CBC Main Menu')

    oc = ObjectContainer()

    oc.add(DirectoryObject(key=Callback(Shows, link=SHOWS_LIST),
        title='Shows',
        thumb = R(ICON)
    ))

    oc.add(DirectoryObject(key=Callback(Shows, link=DOCS_LIST),
        title='Docs',
        thumb = R(ICON)
    ))


    # oc.add(SearchDirectoryObject(
    #     identifier = 'com.plexapp.plugins.cbcnewsnetwork',
    #     title = 'Search',
    #     summary = 'Search CBC videos',
    #     prompt = 'Search for...'
    # ))

    return oc

####################################################################################################
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
        link = show.xpath('.//link')[0].text

        thumbs = GetThumbsFromElement(show.xpath('.//media:thumbnail', namespaces=NAMESPACES))


        oc.add(DirectoryObject(
            key = Callback(DisplayShowItems, title=title, link=link),
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

def GetThumbsSortKey (item):
    return item['resolution']