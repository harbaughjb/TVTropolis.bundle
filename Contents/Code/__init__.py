TITLE = "TVTropolis"
ART = 'art-default.jpg'
ICON = 'icon-default.png'
TVTROPOLIS_PARAMS = ["3i9zvO0c6HSlP7Fz848a0DvzBM0jUWcC", "z/TVTropolis%20Player%20-%20Video%20Center"]
FEED_LIST = "http://feeds.theplatform.com/ps/JSON/PortalService/2.2/getCategoryList?PID=%s&startIndex=1&endIndex=500&query=hasReleases&query=CustomText|PlayerTag|%s&field=airdate&field=fullTitle&field=author&field=description&field=PID&field=thumbnailURL&field=title&contentCustomField=title&field=ID&field=parent"
FEEDS_LIST = "http://feeds.theplatform.com/ps/JSON/PortalService/2.2/getReleaseList?PID=%s&startIndex=1&endIndex=500&query=categoryIDs|%s&query=BitrateEqualOrGreaterThan|400000&query=BitrateLessThan|601000&sortField=airdate&sortDescending=true&field=airdate&field=author&field=description&field=length&field=PID&field=thumbnailURL&field=title&contentCustomField=title&contentCustomField=Episode&contentCustomField=Season"
DIRECT_FEED = "http://release.theplatform.com/content.select?format=SMIL&pid=%s&UserName=Unknown&Embedded=True&TrackBrowser=True&Tracking=True&TrackLocation=True"
LOADCATS = { 
	'shows':['/']
	}
NOLOADCATS = {
	'featured':['Featured']
}
VIDEO_URL = 'http://www.tvtropolis.ca/video/?releasePID=%s'

####################################################################################################

def Start():
	Plugin.AddPrefixHandler("/video/tvtropolis", MainMenu, TITLE, ICON, ART)

	Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
	Plugin.AddViewGroup("List", viewMode="List", mediaType="items")

	# Setup the default attributes for the ObjectContainer
	ObjectContainer.title1 = TITLE
	ObjectContainer.view_group = 'List'
	ObjectContainer.art = R(ART)
	
	# Setup the default attributes for the other objects
	DirectoryObject.thumb = R(ICON)
	DirectoryObject.art = R(ART)
	EpisodeObject.thumb = R(ICON)
	EpisodeObject.art = R(ART)

	HTTP.CacheTime = CACHE_1HOUR

####################################################################################################

def MainMenu():
   	return LoadShowList(cats='shows',nocats='featured')


####################################################################################################
def LoadShowList(cats, nocats):

 	oc = ObjectContainer ( view_group="List")
 	
 	network = TVTROPOLIS_PARAMS
	content = JSON.ObjectFromURL(FEED_LIST % (network[0], network[1]))
	showList = {}
	showCount = 0
	Log(content)
	
	items = content['items']

	for item in items:

		if WantedCats(item['fullTitle'],cats) and UnWantedCats(item['fullTitle'],nocats):
			title = item['fullTitle'].split('/')[1]
			
			iid = item['ID']
			thumb_url = item['thumbnailURL']
			if not(title in showList):
				showList[title]=""
				oc.add(
					DirectoryObject(
						key = Callback(SeasonsPage, cats=cats, nocats=nocats, network=network, showtitle=title),
						title = title, 
						thumb = Resource.ContentsOfURLWithFallback(url=thumb_url, fallback=ICON)
					)
				)
	# sort here
	oc.objects.sort(key = lambda obj: obj.title)

 	return oc


####################################################################################################

def VideosPage(pid, iid, show):
	
	oc = ObjectContainer(
		view_group = 'InfoList'
	)
	pageURL = FEEDS_LIST % (pid, iid)
	feeds = JSON.ObjectFromURL(pageURL)

	showList = {}
	
	for item in feeds['items']:
		title = item['title']
		try:
			# show exists, skip adding multiples
			if showList[title]:
				continue
		except:
			# show doesn't exist, add it
			Log(item)
			showList[title]=""
			pid = item['PID']

			summary =  item['description']
			duration = item['length']
			thumb_url = item['thumbnailURL']
			airdate = int(item['airdate'])/1000
			originally_available_at = Datetime.FromTimestamp(airdate).date()
			
			try:
				# try to set the seasons and episode info
				# NB: episode is set with 'index' (not in framework docs)!
				season = item['contentCustomData'][1]['value']
				seasonint = int(float(season))
				episode = item['contentCustomData'][0]['value']
				episodeint = int(float(episode))

				oc.add(
					EpisodeObject(
						url = VIDEO_URL % pid,
						title = title,
						summary=summary,
						duration=duration,
						thumb = Resource.ContentsOfURLWithFallback(url=thumb_url, fallback=ICON),
						originally_available_at = originally_available_at,
		 				season = seasonint,
		 				index = episodeint
					)
				)
	
			except:
				# if we don't get the season/episode info then don't set it
				oc.add(
					EpisodeObject(
						url = VIDEO_URL % pid,
						title = title,
						summary=summary,
						duration=duration,
						thumb = Resource.ContentsOfURLWithFallback(url=thumb_url, fallback=ICON),
						originally_available_at = originally_available_at
					)
				)

	return oc

####################################################################################################

def SeasonsPage(cats, nocats, network, showtitle):

	oc = ObjectContainer()
	
	pageURL = FEED_LIST % (network[0], network[1])

	content = JSON.ObjectFromURL(pageURL)
	season_list = []
	
	for item in content['items']:
		if UnWantedCats(item['parent'], nocats) and showtitle in item['fullTitle']:

			title = item['fullTitle'].split('/')[2]

			if showtitle in title:
				continue
			
			if title not in season_list:
				if title=="":
					# bad data from provider, this is a corner case and happens often
					# enough that it's worth adding these in as uncategorized if they
					# made it to the Seasons list (it means they have child elements to view)
					title="Uncategorized Items"
				season_list.append(title)
				iid = item['ID']

				thumb_url = item['thumbnailURL']
				oc.add(
					DirectoryObject(
						key = Callback(VideosPage, pid=network[0], iid=iid, show=showtitle),
						title = title,
						thumb = Resource.ContentsOfURLWithFallback(url=thumb_url, fallback=ICON)
					)
				)
	oc.objects.sort(key = lambda obj: obj.title)
	return oc

####################################################################################################
def WantedCats(thisShow,cats):
	
	for show in LOADCATS[cats]:
		if show in thisShow:
			return 1				
	return 0

def UnWantedCats(thisShow,nocats):
	
	for show in NOLOADCATS[nocats]:
		if not(show in thisShow):
			return 1				
	return 0

