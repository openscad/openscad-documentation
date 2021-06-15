'''
This is the program for Generator for offline documentation
more about which can be found out at https://github.com/opencax/GSoC/issues/6
and the GSOC project details for the same are present at
https://summerofcode.withgoogle.com/projects/#6746958066089984

'''
import urllib.request, urllib.parse, urllib.error, urllib.request, urllib.error, urllib.parse, os
from bs4 import BeautifulSoup as bs,Comment

pages_for_exclusion = ['https://en.wikibooks.org/wiki/OpenSCAD_User_Manual/Example/Strandbeest']

user_agent_val ='Generator-for-Offline-Documentation (https://github.com/abshk-jr ; https://github.com/opencax/GSoC/issues/6 ; https://summerofcode.withgoogle.com/projects/#6746958066089984) urllib/3.9.0 [BeautifulSoup/4.9.0]'

url = 'https://en.wikibooks.org/wiki/OpenSCAD_User_Manual'
url_css = 'https://en.wikipedia.org/w/load.php?debug=false&lang=en&modules=mediawiki.legacy.commonPrint,shared|skins.vector.styles&only=styles&skin=vector&*'
url_wiki = 'https://en.wikibooks.org'
url_api = 'https://en.wikibooks.org/w/api.php?action=parse&format=xml&prop=text&page='

dir_docs = 'openscad_docs'
dir_imgs =  os.path.join( dir_docs, 'imgs')
dir_maths =  os.path.join( dir_docs, 'imgs','maths')
dir_styles = os.path.join( dir_docs, 'styles')

#Create the directories to save the doc if they don't exist
if not os.path.exists(dir_docs): os.makedirs(dir_docs)
if not os.path.exists(dir_imgs): os.makedirs(dir_imgs)
if not os.path.exists(dir_maths): os.makedirs(dir_maths)	
if not os.path.exists(dir_styles): os.makedirs(dir_styles)

pages =[]
pages += pages_for_exclusion
imgs  =[]
maths =[]

def getUrl(url):
	'''
	This function generates the complete url after getting urls form src
	/wiki/OpenSCAD_User_Manual get converted to https://en.wikibooks.org/wiki/OpenSCAD_User_Manual

	'''
	if url.startswith('//'):
		url = 'https:'+url
	elif not url.startswith( url_wiki ):
		url = urllib.parse.urljoin( url_wiki, url[0]=="/" and url[1:] or url)
	return url

def getTags(soup):
	'''
	This function handles the different tags present in the HTML document
	for example the image tags

	'''
	for a in soup.find_all('a'):
		href= a.get('href')
		if href:
			if href[0] != '#':
				href = getUrl(href)
			if (href.startswith('/wiki/OpenSCAD_User_Manual') or href.startswith(url_wiki + '/wiki/OpenSCAD_User_Manual')):
				newhref = (href.replace('#', '.html#') if '#' in href else href+'.html').split('/')[-1]
				
				if 'Print_version.html' not in newhref:
					getPages(url=href)
					a['href']= newhref

			if a.img :
				getImages( a )

def getMaths(soup):
	'''
	This function generates the image version of the math formulas
	to be displayed in various HTML files, for example
	https://en.wikibooks.org/wiki/OpenSCAD_User_Manual/Mathematical_Operators
	and saves them to the directory /openscad_docs/imgs/maths

	'''
	for img in soup.find_all('img'):
		try:
			for cls in img['class']:
				if('math' in cls):
					mathname = img['src'].split("/")[-1].split("\\")[-1] + '.svg'
					savepath = os.path.join( dir_maths, mathname)
					if (not mathname in maths):
						opener = urllib.request.build_opener()
						opener.addheaders = [('User-Agent',user_agent_val)]
						urllib.request.install_opener(opener)
						urllib.request.urlretrieve( img['src'] , savepath )
						maths.append( mathname )
					linkurl = os.path.join('.','imgs\maths',mathname)
					img['src'] = linkurl
					
		except:
			pass

def getImages(tag):
	'''
	This function generates the images present the in HTML documents
	and saves them to the directory /openscad_docs/imgs

	'''
	src = getUrl( tag.img['src'] )
	imgname = src.split("/")[-1]
	imgname = imgname.replace('%','_')
	imgpath = os.path.join( dir_imgs, imgname)

	#The following is to download the image if it hasn't alrady been downloaded
	if not imgpath in imgs:
		opener = urllib.request.build_opener()
		opener.addheaders = [('User-Agent',user_agent_val)]
		urllib.request.install_opener(opener)
		urllib.request.urlretrieve(src , imgpath)
		imgs.append(imgpath)

	del tag.img['srcset']
	imgpath = os.path.join('.', 'imgs', imgname)
	tag.img['src'] = imgpath
	tag['href']= imgpath

def cleanSoup(soup):
	'''
	This function cleans the soup by removing the redundant HTML tags
	and the parts that are unrelated to the User Manual
	'''

	#The following deletes the Tags which aren't required in the User Manual
	red_div_cls  = ["printfooter","catlinks","noprint","magnify"]
	red_span_cls = ["mw-editsection","toctogglespan","noprint"]
	red_table_cls= ['noprint','ambox']
	red_input_cls= ['toctogglecheckbox']
	for cls in red_div_cls: 
		for tag in soup.findAll('div',{'class':cls}):
			tag.decompose()
	for cls in red_span_cls: 
		for tag in soup.findAll('span',{'class':cls}):
			tag.decompose()
	for cls in red_table_cls: 
		for tag in soup.findAll('table',{'class':cls}): 
			tag.decompose()
	for cls in red_input_cls: 
		for tag in soup.findAll('input',{'class':cls}):
			tag.decompose()
	for tag in soup.findAll('style'):
		tag.decompose()

	#The following removes the comments present in the HTML document
	comments = soup.findAll(text=lambda text: isinstance(text, Comment))
	[comment.extract() for comment in comments]

	#The following replaces the redundant Tags with the content present in inside of them
	rep_div_cls = ["mw-highlight"]
	rep_span_cls= ["toctext","mw-headline"]
	for kls in rep_div_cls:
			for tag in soup.findAll('div',kls):
				tag.replaceWithChildren()
	for kls in rep_span_cls:
			for tag in soup.findAll('span',kls):
				tag.replaceWithChildren()
	
	#The following is for the cleaning/removal of some redundant span tags
	for _ in range(0,7):
		for tag in soup.findAll('li',{'class':f'toclevel-{_}'}):
			del tag['class']
	
	for tag in soup.findAll('span'):
		try:
			if(len(tag.text)==0):
				tag.decompose()
			for _ in tag['class']:
				if(len(_) <= 2):
					tag.replaceWithChildren()
				if('mathml' in _):
					tag.decompose()
		except:
			pass

	for tag in soup.findAll('ul'):
		tag['style'] = 'list-style-image:none'


def getFooter( url, name ):
	'''
	This function generates the Footer with the license attribution for all the pages

	'''
	footer = (f'''<footer class='mw-body' style="font-size:13px;color:darkgray;text-align:center;margin-bottom:-1px">
	From the WikiBooks article <a style="color:black" href="{url}">{name}</a> 
	(provided under <a style="color:black" href="https://creativecommons.org/licenses/by-sa/3.0/">
	CC-BY-SA-3.0</a>)</footer>''')

	return bs(footer,'html.parser')

def getPages( url=url,folder=dir_docs ):
	'''
	This is the main function of the program
	which generates the HTML document from the given url
	and calls different functions to generate the Offline
	version of the page and save it under the directory /openscad_docs
	
	'''
	url = getUrl(url)
	if url.split("#")[0] not in pages:
		pages.append( url.split("#")[0] )							#add the url to the `pages` list so that they don't get downloaded again
		wiki_url = url
		url = url.replace(url_wiki+'/wiki/', "")
		url = url_api + url

		request = urllib.request.Request(url)
		request.add_header('User-Agent',user_agent_val)
		response = urllib.request.urlopen(request)
		xml = response.read()
		soup = bs(xml, 'lxml')
		soup = soup.text
		soup = bs(soup,'html5lib')

		css_tag = bs('<link rel="stylesheet" href="./styles/style.css">','html.parser')
		soup.head.append(css_tag)

		soup.body['class'] = 'mw-body'
		del soup.body.div['class']
		soup.body.div['id']='bodyContent'

		fname = url.split("=")[-1]
		fname = fname.replace("OpenSCAD_User_Manual/","")
		fname = fname.split('#')[0]									#for fnames like openscad_docs\FAQ#What_are_those_strange_flickering_artifacts_in_the_preview?.html
		fname = fname.split("/")[-1]

		title = soup.new_tag("title")								#to add title to the pages
		title.string = fname.replace("_" , " ")
		soup.html.head.append(title)

		h1_tag = bs(f'<h1 class="firstHeading" id="firstHeading">{title.string}</h1>','html.parser')
		soup.body.insert(0,h1_tag)
				
		fname = fname + ".html"
		filepath = os.path.join( folder, fname)

		print("Saving: ", filepath)

		cleanSoup(soup)
		getMaths(soup)
		getTags(soup)

		soup.body.append( getFooter( wiki_url, title.text ))

		open(filepath, "w", encoding="utf-8").write( str(soup) )


def getCSS():
	'''
	This function runs once after the HTML files have been downloaded
	and downloads the CSS given at https://www.mediawiki.org/wiki/API:Styling_content
	and saves it to openscad_docs/styles
	
	'''
	request = urllib.request.Request(url_css)
	request.add_header('User-Agent',user_agent_val)
	response = urllib.request.urlopen(request)
	css_soup = response.read()
	css = bs(css_soup, 'html5lib')
	csspath = os.path.join( dir_styles, 'style.css')
	open( csspath, "w" , encoding="utf-8").write(css.body.text)


	
if(__name__ == '__main__'):
	print(f'Started Offline Generator.py\nNow downloading the User-Manual from {url}')
	getPages(url)
	getCSS()
	print("Total number of pages generated is \t:\t", len(pages)-len(pages_for_exclusion))
	print("Total number of images generated is \t:\t", len(imgs))
	print("Total number of math-images generated is:\t", len(maths))
