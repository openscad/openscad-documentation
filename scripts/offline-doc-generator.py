'''
This is the code for `Generator for offline documentation`, more
about which can be read at https://github.com/opencax/GSoC/issues/6
and the GSOC project details for the same can be checked out at
https://summerofcode.withgoogle.com/projects/#6746958066089984

'''
import urllib.request, urllib.parse, os, yaml
from bs4 import BeautifulSoup as bs,Comment, Doctype
import shutil
import pdfkit
import platform
if platform.system() == 'Linux': import cairosvg

with open(os.path.join( os.path.dirname(__file__),'config.yml'),'r') as file:
    config = yaml.safe_load(file)

#Update the global variables with the data from config.yml
globals().update(config)

dir_docs = 'openscad_docs'
dir_imgs =  os.path.join( dir_docs, 'imgs')
dir_maths =  os.path.join( dir_docs, 'imgs','maths')
dir_styles = os.path.join( dir_docs, 'styles')

#Create the directories to save the documentation
if not os.path.exists(dir_docs): os.makedirs(dir_docs)
if not os.path.exists(dir_imgs): os.makedirs(dir_imgs)
if not os.path.exists(dir_maths): os.makedirs(dir_maths)	
if not os.path.exists(dir_styles): os.makedirs(dir_styles)

dir_pdfs = 'openscad_docs_pdf'
if not os.path.exists(dir_pdfs): os.makedirs(dir_pdfs)
dir_docpdfs = 'docs_pdf'
if not os.path.exists(dir_docpdfs): os.makedirs(dir_docpdfs)
dir_pdfimgs =  os.path.join( dir_pdfs, 'imgs')
if not os.path.exists(dir_pdfimgs): os.makedirs(dir_pdfimgs)
dir_pdfmaths =  os.path.join( dir_pdfs, 'imgs', 'maths')
if not os.path.exists(dir_pdfmaths): os.makedirs(dir_pdfmaths)

pages =[]
pages += pages_for_exclusion
imgs  =[]
maths =[]

def getParsedUrl(url):
    '''
    This function generates a parsed url after accepting the url from the src inside the <a> tags
    e.g. /wiki/OpenSCAD_User_Manual gets converted to https://en.wikibooks.org/wiki/OpenSCAD_User_Manual

    '''
    if url.startswith('//'):
        url = 'https:'+url
    elif not url.startswith( url_wiki ):
        url = urllib.parse.urljoin( url_wiki, url[0]=="/" and url[1:] or url)
    return urllib.parse.urlparse(url)

def getTags(soup,pdf):
    '''
    This function handles the different tags present in the HTML document
    e.x. updating the <a> tags with the new links, or handling the <img> tags

    '''
    for a in soup.find_all('a'):
        href= a.get('href')
        if href:
            if href[0] != '#':
                hrefparse = getParsedUrl(href)
                hrefurl=hrefparse.geturl()
                if pdf:
                    a['href']= hrefurl
                elif hrefparse.path.startswith('/wiki/OpenSCAD_User_Manual'):
                    newhref = (hrefurl.replace('#', '.html#') if hrefparse.query else hrefurl+'.html').split('/')[-1]
                    
                    if 'Print_version.html' not in newhref:
                        getPages(url=hrefurl)
                        a['href']= newhref

            if a.img :
                getImages( a,pdf )

def getMaths(soup,pdf):
    '''
    This function downloads the SVG files for the Math Formulas
    that are being used on various pages, for example at
    https://en.wikibooks.org/wiki/OpenSCAD_User_Manual/Mathematical_Operators
    and saves them to the directory /openscad_docs/imgs/maths

    '''
    for img in soup.find_all('img'):
        try:
            for cls in img['class']:
                if('math' in cls):
                    mathname = img['src'].split("/")[-1].split("\\")[-1] + '.svg'
                    savepath = os.path.join( dir_maths, mathname) if not pdf else os.path.join( dir_pdfmaths, mathname)
                    savepath_png = savepath.replace('.svg','.png')
                    if (not mathname in maths) or pdf:
                        opener = urllib.request.build_opener()
                        opener.addheaders = [('User-Agent',user_agent_val)]
                        urllib.request.install_opener(opener)
                        urllib.request.urlretrieve( img['src'] , savepath )
                        if pdf and platform.system() == 'Linux':
                            '''
                            This part of the code converts the SVGs to PNGs if the program is being run on Linux,
                            to overcome the issue where WebKit Engine renders the SVG images at incorrrect sizing
                            '''
                            cairosvg.svg2png(url=savepath, write_to=savepath_png)
                            os.remove(savepath)
                        maths.append( mathname )
                    if pdf and platform.system() == 'Linux':
                        linkurl = os.path.join('.','imgs/maths',mathname).replace('\\','/').replace('.svg','.png')
                    else:
                        linkurl = os.path.join('.','imgs/maths',mathname).replace('\\','/')
                    img['src'] = linkurl
                    
        except:
            pass

def getImages(tag,pdf):
    '''
    This function downloads the images present in the HTML files
    and saves them to the directory - /openscad_docs/imgs

    '''
    srcparse = getParsedUrl( tag.img['src'] )
    imgname = srcparse.path.split("/")[-1]
    imgname = imgname.replace('%','_')
    imgpath = os.path.join( dir_imgs, imgname) if not pdf else os.path.join( dir_pdfimgs, imgname)

    #The following is to download the image if it hasn't alrady been downloaded
    if not imgpath in imgs:
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-Agent',user_agent_val)]
        urllib.request.install_opener(opener)
        urllib.request.urlretrieve(srcparse.geturl() , imgpath)
        imgs.append(imgpath)

    del tag.img['srcset']
    imgpath = os.path.join('.', 'imgs', imgname).replace('\\','/')
    tag.img['src'] = imgpath
    tag['href']= imgpath

def cleanSoup(soup,pdf):
    '''
    This function cleans the HTML by removing the redundant tags
    and the sections which are not necessary for the User Manual
    '''

    #The following deletes the Tags which aren't required in the User Manual
    red_dict = {'div' : ["printfooter","catlinks","noprint","magnify"], 'table' : ['noprint'], 'input' : ['toctogglecheckbox']}
    for tag,cls_list in red_dict.items():
        for cls in cls_list: 
            for tag in soup.findAll(tag,{'class':cls}):
                tag.decompose()

    for tag in soup.findAll('table',{'class':'ambox'}):
        tag.decompose()

    for tag in soup.findAll('style'):
        tag.decompose()

    #The following removes the comments present in the HTML document
    comments = soup.findAll(text=lambda text: isinstance(text, Comment))
    [comment.extract() for comment in comments]

    #The following replaces the redundant div Tags with the content present inside of them
    rep_div_cls = ["mw-highlight"]
    for kls in rep_div_cls:
            for tag in soup.findAll('div',kls):
                tag.replaceWithChildren()
    
    #The following removes the non-contributing classes in li tags
    for _ in range(0,7):
        for tag in soup.findAll('li',{'class':f'toclevel-{_}'}):
            del tag['class']
    
    #The following is for the removal/cleaning of some redundant span tags
    for tag in soup.findAll('span'):
        try:
            if(len(tag.text)==0):
                tag.decompose()
            for cls in tag['class']:
                if(len(cls) <= 2):
                    tag.replaceWithChildren()
                elif cls in ['toctext'] or (pdf and cls in ['tocnumber']):
                    tag.replaceWithChildren()
                elif cls in ['mw-headline']:
                    del tag['class']
                elif 'mathml' in cls or cls in ['mw-editsection','toctogglespan','noprint']:
                    tag.decompose()

        except:
            pass

    #The following is to replace the tabs in the code blocks with spaces
    for txt in soup.findAll('pre'):
        txt.string = txt.text.replace('\t','    ')
        if pdf:
            if platform.system() == 'Linux':
                for _ in soup.findAll('pre'):
                    _['style']="font-family:'Liberation Mono'"
    
    #The following unwraps the tables in the pdfs for a better formatting
    if pdf:
        for table in soup.findAll('table'):
            for row in table.findAll('tr'):
                for col in row.findAll('td'):
                    col.unwrap()
                row.unwrap()
            table.unwrap()

    for tag in soup.findAll('ul'):
        tag['style'] = 'list-style-image:none'


def getFooter( url, name ):
    '''
    This function generates the Footer containing the necessary license attribution

    '''
    footer = (f'''<footer class='mw-body' style="font-size:13px;color:darkgray;text-align:center;margin-bottom:-1px">
    From the WikiBooks article <a style="color:black" href="{url}">{name}</a> 
    (provided under <a style="color:black" href="https://creativecommons.org/licenses/by-sa/3.0/">
    CC-BY-SA-3.0</a>)</footer>''')

    return bs(footer,'html.parser')

def getStyled(soup,title):
    tag = Doctype('html')
    soup.insert(0, tag)
    soup.html['lang']='en'
    meta_tag =  soup.new_tag('meta')
    meta_tag['charset'] = 'UTF-8'
    soup.head.insert(0,meta_tag)
    css_tag = bs('<link rel="stylesheet" href="./styles/style.css">','html.parser')
    soup.head.append(css_tag)
    soup.body['class'] = 'mw-body'
    soup.body['style']=['height:auto;background-color:#ffffff']
    del soup.body.div['class']
    soup.body.div['id']='bodyContent'
    h1_tag = bs(f'<h1 class="firstHeading" id="firstHeading">{title}</h1>','html.parser')
    soup.body.insert(0,h1_tag)

def getPages( url=url,folder=dir_docs,pdf=False ):
    '''
    This is the main function of the program
    which downloads the webpage at the given url
    and calls different functions to generate the Offline
    version of the page and save it under the directory /openscad_docs
    
    '''
    if url.split("#")[0] not in pages or pdf:
        pages.append( url.split("#")[0] )							#adds the url to the `pages` list so that the page doesn't get downloaded again
        wiki_url = url
        url = url.replace(url_wiki+'/wiki/', "")
        url = url_api + url

        request = urllib.request.Request(url)
        request.add_header('User-Agent',user_agent_val)
        response = urllib.request.urlopen(request)
        xml = response.read()
        soup = bs(xml, 'html.parser')
        soup = soup.text
        soup = bs(soup,'html5lib')

        name = url.split("=")[-1]
        name = name.split("/")[-1].split('#')[0]					#converts OpenSCAD_User_Manual/String_Functions#str to String_Functions

        if pdf==True: name = 'OpenSCAD_User_Manual' if (name == 'Print_version') else name

        title = soup.new_tag("title")								#adds title to the pages
        title.string = name.replace("_" , " ")
        soup.html.head.append(title)

        name = name + ".html"
        filepath = os.path.join( folder, name)

        print("Saving: ", filepath)

        getStyled(soup,title.string)
        cleanSoup(soup,pdf)
        getMaths(soup,pdf)
        getTags(soup,pdf)

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

def getPdf():
    for link in url_print:
        getPages(link,folder=dir_pdfs,pdf=True)
    if os.path.exists(f'{os.path.join( os.getcwd(), dir_pdfs)}/styles'):shutil.rmtree(f'{os.path.join( os.getcwd(), dir_pdfs)}/styles')
    shutil.copytree(f'{os.path.join( os.getcwd(), dir_docs)}/styles', f'{os.path.join( os.getcwd(), dir_pdfs)}/styles')


    
if(__name__ == '__main__'):
    print(f'Started Offline Generator.py\nNow downloading the User-Manual from {url}')
    getPages(url)
    getCSS()
    print("Total number of pages generated is \t:\t", len(pages)-len(pages_for_exclusion))
    print("Total number of images generated is \t:\t", len(imgs))
    print("Total number of math-images generated is:\t", len(maths))
    shutil.make_archive('Generated-Offline-Manual', 'zip', dir_docs)

    getPdf()
    files=os.listdir(os.path.join( os.getcwd(), dir_pdfs))
    for file in files:
        if ".html" in file:
            file_pdf = file.replace('.html','.pdf')
            pdfkit.from_file(f'{os.path.join( os.getcwd(), dir_pdfs)}/{file}', f'{os.path.join( os.getcwd(), dir_docpdfs)}/{file_pdf}' , options=options)

    shutil.make_archive('PDF-Offline-Manual', 'zip', dir_docpdfs)
    shutil.rmtree(dir_pdfs)
    shutil.rmtree(dir_docpdfs)