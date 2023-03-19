from fileinput import close
from posixpath import splitext
import sqlite3, webbrowser, sys, json, os, shutil, io
from datetime import datetime, date
from json import JSONEncoder
import config 
from zipfile import ZipFile
from dlcore import dispatch
from dlcore import x06 as dataLoading 
from time import sleep

firstRun = True

if config.isPyzFile:
    ssurgo_portal_ui = 'resources/ssurgo_portal_UI.html' 
else:
    fullPath = sys.argv[0].split("\\")
    fullPath.pop()
    fullPath = "/".join(fullPath)
    ssurgo_portal_ui = fullPath + '/resources/ssurgo_portal_UI.html' 

try:
    from bottle import run, template, request, response, route, post, static_file, TEMPLATES, Bottle, redirect
except:
    pass

webpage = Bottle()
#logic to process template files from a PYZ file
if config.isPyzFile:
    #PYZ variables
    tail = '\\dphost\\webpage.py'
    zippath = __file__[0:(len(__file__) - len(tail))]
    def render_template(filePath):
        """Used to get templates from a PYZ file. Valid arguments for this method are plaintext and template"""
        with ZipFile(zippath) as dpzip:
            with io.TextIOWrapper(dpzip.open(filePath), encoding='utf-8') as templateResult:
                content = templateResult.readlines()
                plaintext = ''.join(content)
        dpzip.close()
        # Is there a difference between returning the plain text vs a template(plaintext) object? 
        """     Yes when doing template(plaintext) the python code is executed. This will cause parts of the template that rely
            on python variables not to load""" 
        try:
            return plaintext
        except:
            return print('error in render_template')

def defaultconverter(o):
    """Converts a date time into a more user friendly format"""
    if isinstance(o, datetime.date):
        return o.isoformat()
#-----------------------------------Bottle Route methods-------------------
@webpage.route('/startUp')
def getStartupInfo():
    checkVersionInfo()
    redirect('/SSURGOPortalUI')

#get request. Used on initial load. Imediately after initial load a post request is issued by ssurgo_portal_scripts.js to get the folder tree.
@webpage.route('/SSURGOPortalUI')
def display_SSURGOPortalUI():
    if config.isPyzFile == True:
        rendered_ssurgo_portal_ui = render_template(ssurgo_portal_ui)
        output = template(rendered_ssurgo_portal_ui)        
    else:
        output = template(ssurgo_portal_ui)        
    return output

#This can also be represented by @route('/start', method = 'post')
@webpage.post('/SSURGOPortalUI')
def ssurgoPortalUI_request():
    response = dispatch.Dispatch.dispatch(request.json)
    return response

@webpage.get('/logFile')
def getLogFile():
    if config.isPyzFile:
        return os.path.dirname(zippath)
    else: 
        return os.getcwd()

@webpage.post('/close')
def kill_server():
    if config.isPyzFile:
        sys.stderr.close()
    else:
        print("KILL SERVER COMMAND")

@webpage.post('/serverStatus')
def is_server_running():
    global firstRun
    if not firstRun:
        sleep(2)    
    firstRun = False
    return json.dumps({"running" : True})

#Checks if a file already exists & returns a boolean
@webpage.post('/fileExists')
def fileExists(): 
    if os.path.exists(request.json):
        return json.dumps(True)
    return json.dumps(False)    

#Returns static files like JS and CSS
@webpage.route('/static/<filename>')
def server_static(filename):
    if config.isPyzFile:
        with ZipFile(zippath) as dpzip:
            with io.TextIOWrapper(dpzip.open('resources/' + filename), encoding='utf-8') as templateResult:
                content = templateResult.readlines()
                plaintext = ''.join(content)        
            dpzip.close()
            return template(plaintext)
    else:
        return static_file(filename, fullPath + "/resources/") 

@webpage.route('/static/css/<filename>')
def get_css(filename):
    if config.isPyzFile:
            response.body = render_template('resources/css/' + filename)
            response.content_type = "text/css; charset=UTF-8"
            return response
    else:
        return static_file(filename, fullPath + "/resources/css/")

#Returns images. CAN ONLY ACCCEPT SVG FILES.
@webpage.route('/static/images/<filename>')
def get_image(filename):
    if config.isPyzFile:
        response.body = render_template('resources/images/' + filename)
        response.content_type = "image/svg+xml"
        return response
    else:
        return static_file(filename, fullPath + "/resources/images/", "image/svg+xml")

#Called from __main__.py.
def checkVersionInfo():    
    cookieVersion = request.get_cookie("ApplicationVersion")
    configVersion = config.static_config["versionInformation"]
    if cookieVersion == None or cookieVersion != configVersion:
        TEMPLATES.clear()
        webpage.reset()
        response.set_cookie("ApplicationVersion", configVersion["ApplicationVersion"])
        response.set_cookie("SQLiteSSURGOTemplateVersion", configVersion["SQLiteSSURGOTemplateVersion"])
        response.set_cookie("SSURGOVersion", configVersion["SSURGOVersion"])

def runServer():
    """Main method for running the bottle server"""
    webbrowser.open('http://localhost:8083/startUp', 1, True)
    if config.isPyzFile:
        run(webpage, host='localhost', port=8083)
    else:
        run(webpage, host='localhost', port=8083, debug=True)