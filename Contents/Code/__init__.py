####################################################################################################
#CBC.CA Video Plugin
#Written by mysciencefriend
#Overhauled and updated by Mikedm139
#Use at your own risk, etc. etc.

ART  = 'art-default.jpg'
ICON = 'icon-default.jpg'

MORE_SHOWS = '1329813962'

SHOWS_LIST  = 'http://cbc.feeds.theplatform.com/ps/JSON/PortalService/2.2/getCategoryList?PID=_DyE_l_gC9yXF9BvDQ4XNfcCVLS4PQij&field=ID&field=title&field=parentID&field=description&customField=MaxClips&customField=ClipType&query=ParentIDs|%s'
VIDEOS_LIST = 'http://cbc.feeds.theplatform.com/ps/JSON/PortalService/2.2/getReleaseList?PID=_DyE_l_gC9yXF9BvDQ4XNfcCVLS4PQij&query=CategoryIDs|%s&sortDescending=true&endIndex=500'
BASE_URL    = 'http://www.cbc.ca'
PLAYER_URL  = BASE_URL + '/player/%s'
VIDEO_URL   = PLAYER_URL % 'play/'
LIVE_SPORTS = PLAYER_URL % 'sports/Live'
NHL_URL     = BASE_URL + '/sports/hockey/nhl'
JSON_URL    = BASE_URL + '/json/cmlink/%s'

RE_THUMB_URL=   Regex('background-image: url\(\'(?P<url>http://.+?jpg)\'\)')

CATEGORIES  = ['TV', 'News', 'Kids', 'Sports', 'Radio']

####################################################################################################
@handler('/video/cbc', 'CBC', art=ART, thumb=ICON)
def MainMenu():

    oc = ObjectContainer()
    oc.add(DirectoryObject(key=Callback(HockeyNightInCanada), title='Hockey Night In Canada'))
    oc.add(DirectoryObject(key=Callback(LiveSports), title='Sports'))
    
    for category in CATEGORIES:

        oc.add(DirectoryObject(
            key = Callback(Category, category=category),
            title = category
        ))

    oc.add(SearchDirectoryObject(
        identifier = 'com.plexapp.plugins.cbcnewsnetwork',
        title = 'Search',
        summary = 'Search CBC videos',
        prompt = 'Search for...'
    ))

    return oc

####################################################################################################
@route('/video/cbc/hnic')
def HockeyNightInCanada():
    oc = ObjectContainer(title2='Hockey Night In Canada')
    page = HTML.ElementFromURL(NHL_URL)
    try:
        live_url    = page.xpath('//li[@class="ticker-item live "]//a')[0].get('href')
        gid         = RE_GID.search(live_url).group('gid')
        data        = JSON.ObjectFromURL(JSON_URL % gid)['leadmedia']
        
        title   = data['title']
        summary = data['description']
        thumb   = data['headlineimage']['url']
        vid     = data['releaseid']
        url     = VIDEO_URL + vid
        oc.add(
            VideoClipObject(
                url     = url,
                title   = title,
                summary = summary,
                thumb   = thumb
            )
        )
    except:
        return ObjectContainer(header="No Live Games Now", message="Please try again another time.")
    

####################################################################################################
@route('/video/cbc/sports')
def LiveSports():
  oc = ObjectContainer()
  page = HTML.ElementFromURL(LIVE_SPORTS)
  for item in page.xpath('//section[@class="category-content full"]//li[@class="medialist-item"]'):
    link = item.xpath('./a')[0].get('href')
    thumb = item.xpath('.//img')[0].get('src')
    date = item.xpath('.//span[@class="medialist-date"]')[0].text
    title = item.xpath('.//div[@class="medialist-title"]')[0].text
    oc.add(
      VideoClipObject(
        url = link,
        title = title,
        originally_available_at = Datetime.ParseDate(date).date(),
        thumb = Resource.ContentsOfURLWithFallback(url=thumb)
        )
    )
  return oc

####################################################################################################
@route('/video/cbc/category')
def Category(category=None, link=None):

    oc = ObjectContainer(title2=category)
    if link:
        page = HTML.ElementFromURL(link)
    else:
        page = HTML.ElementFromURL(PLAYER_URL % category.lower())
        oc.add(DirectoryObject(key=Callback(Featured, category=category), title="Featured"))
    
    for item in page.xpath('.//ul[@class="longlist-list"]//a'):
        title   = item.text
        link    = item.get('href')

        oc.add(
            DirectoryObject(
                key = Callback(ShowsMenu, title=title, link=link),
                title = title
            )
        )

    return oc

####################################################################################################
@route('/video/cbc/show')
def ShowsMenu(title, link):

    oc = ObjectContainer(title2=title)

    page = HTML.ElementFromURL(link)
    
    ''' If the page includes a list of seasons or other sub-divisions, use the Category() function to parse them '''
    try:
        seasons = page.xpath('//div[@class="longlist"]//a')
        if len(seasons) > 0:
            return Category(category=title, link=link)
    except:
        pass
    
    for item in page.xpath('//li[@class="medialist-item"]'):
        url     = item.xpath('./a')[0].get('href')
        if BASE_URL not in url:
            url = BASE_URL + url
        thumb   = item.xpath('.//img')[0].get('src')
        date    = Datetime.ParseDate(item.xpath('.//span[@class="medialist-date"]')[0].text).date()
        duration= Datetime.MillisecondsFromString(item.xpath('.//span[@class="medialist-duration"]')[0].text)
        title   = item.xpath('.//div[@class="medialist-title"]')[0].text
        
        oc.add(
            VideoClipObject(
            url = url,
            title = title,
            duration = duration,
            originally_available_at = date,
            thumb = Resource.ContentsOfURLWithFallback(url=thumb, fallback=ICON)
            )
        )
    
    return oc

####################################################################################################
@route('/video/cbc/featured')
def Featured(category=None):
    
    oc = ObjectContainer(title2=category)
    
    page = HTML.ElementFromURL(PLAYER_URL % category.lower())
    
    for item in page.xpath('//div[@class="featured-container"]'):
        url     = item.xpath('./a')[0].get('href')
        if BASE_URL not in url:
            url = BASE_URL + url
        thumb   = RE_THUMB_URL.search(item.xpath('.//div[@class="featured-content"]')[0].get('style')).group('url')
        title   = item.xpath('.//p[@class="featured-title"]')[0].text
        date    = Datetime.ParseDate(item.xpath('.//p[@class="featured-date"]')[0].text).date()
        duration= Datetime.MillisecondsFromString(item.xpath('.//p[@class="featured-duration"]')[0].text)
        summary = item.xpath('.//p[@class="featured-description"]')[0].text
        
        oc.add(
            VideoClipObject(
            url = url,
            title = title,
            duration = duration,
            originally_available_at = date,
            summary = summary,
            thumb = Resource.ContentsOfURLWithFallback(url=thumb, fallback=ICON)
            )
        )

    return oc