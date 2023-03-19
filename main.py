# main.py

# Running this main.py script: assumes that it is not yet bundled into
# a PYZ file. Assuming that Python is installed and .py and .pyz files are recognized for 
# starting the CEC Python interpreter, you can type the script name (main.py) at a command 
# prompt (it might also work to double-click on the stript's name in Windows File Explorer, 
# I've (Phil) not tried this).

# Noe that when running from weithin a PYZ file, the "__main__.pyz" edntrp point is used.

# If executed at a command prompt, the DP/DL behavior may be selected by choosing 
# one  of the following forms:
#	main.py
#		- start DP
#   main.py ?   (or any text starting with a character other than "@")
#       - return pretty-printed usage syntax
#       - if  a "?" is immediately followed by a string such as
#           ?getStatus
#         then the string is treated as a JSON request name and the request & response schemas for 
#         the request are displayed.
#	main.py @x01.txt
#		- read DL input from x01.txt 
#	main.py @ < x01.txt
#		- read file x01.txt via STDIN 
#	type x01.txt | main.py @
#		- read piped-in (i.e., stdin) text from x01.txt
#   main.py `<JSON request string>
#       - intended for internal test script invocation

import json
import logging
import os
import sys
import time

import config
from dlcore import dispatch
from dlcore.usage import Usage
from runmode import RunMode
import template_logger
from template_logger import tlogger
import utilities.initializer

runmode = RunMode.UNDEFINED


def getMode(argv):
    # Determine start-up mode.
    # Usage: (runmode, errormessage) = getMode(argv)
    # The "errormessage" is nonn-false if library initialization failed.
    # Do libraries require initialization?
    errormessage = False
    try:
        from osgeo import ogr, osr, gdal
        installLibrariesViaInternet = config.get("installLibrariesViaInternet")
        for libraryName in installLibrariesViaInternet:
            exec(f'import {libraryName}')
    except Exception as ex:
        return (RunMode.LIBRARY_INITIALIZATION, f'Unable to import libraries, {format(ex)}')

    # If there are no command-line arguments this is a SSURGO Portal UI startup    
    if len(argv) == 1:
        return (RunMode.SSURGO_PORTAL_UI, errormessage)

    # A "@" command line signifies a Data Loader request
    elif '@' == argv[1][0:1]:
        # Retrieve the request
        return (RunMode.DATA_LOADER, errormessage)

    # A "`" command line signifies a request string. 
    # Only valid for external main() invocation.
    elif '`' == argv[1][0:1]:
        # Retrieve the request
        return (RunMode.DATA_LOADER, errormessage)


    # All other command-line input is managed as a getUsage request.
    else:
        return (RunMode.GET_USAGE, errormessage)

def initializeLogging(runmode):
    # Where is the script running? We need the path head.
    pathHead = os.path.split(sys.argv[0])[0]
    # If in a <script>.PYZ file put log in same folder as the pyz file,
    # otherwise go up one folder level.
    isPyz=sys.argv[0].endswith('.pyz')
    if not isPyz:
        logHead = os.path.split(pathHead)[0]
    else:
        logHead = pathHead

    # For now use a hard-coded name plus run mode.
    # FUTURE: if the file is unavailable, retry N times and add in a 
    # new filename fragment (such as the increment counter 1..)
    modeFragment = format(runmode)
    logFilename = f'{__name__}_{modeFragment}.log'
    filename = os.path.join(logHead, logFilename)
    template_logger.initializeLogger(filename, logging.DEBUG)
    versionInfo = config.static_config["versionInformation"]
    tlogger.info(f'Log {filename} started. ApplicationVersion: {versionInfo["ApplicationVersion"]}; SQLiteSSURGOTemplateVersion: {versionInfo["SQLiteSSURGOTemplateVersion"]}; SSURGOVersion: {versionInfo["SSURGOVersion"]}')

def readStdin(arg):
    # Return the std text or the named file content as a Request instance
    # If a good JSON request, returns (True, requestInstance, None)
    # otherwise returns (False, None, errormessage)
    # usage: (status, request, errormessage) = readStdin(arg)

    # Since the jsonschema library is unavailable until after initialization 
    # we user a try/except block pair to allow initial referencing to 
    # fail quietly.
    parseRequestFunction = None
    try:
        import dlcore.requestschema
        parseRequestFunction = dlcore.requestschema.parseRequest
    except:
        # This is a dummy action to keep library scanning happy at start-up.
        return (False, None, "Initialization is required.")

    # Grab stdin content.
    try:
        if arg =='@':
            errormessage = 'Error reading stdin'
            json_data = ' '.join(sys.stdin.readlines())
            tlogger.info("Read stdin via pipe")
            return parseRequestFunction(json_data)
        elif arg[0] == '`':
            # Special redirection: the text after the "`" is 
            # treated as a JSON string.
            errormessage = 'Error reading "`" text'
            json_data = arg[1:]  # .replace(r'\\\\', r'\\')
            tlogger.info('Read stdin via "`" string')
            return parseRequestFunction(json_data)
        else:
            filename = arg[1:]
            errormessage = f'Error reading stdin file "{filename}"'
            with open(filename) as f:
                json_data = ' '.join(f.readlines())
            tlogger.info(f"Read stdin via file {filename}")
            return parseRequestFunction(json_data)
    except Exception as err:
        errormessage = f'{errormessage}: {format(err)}'
        tlogger.error(errormessage)
        return (False, None, errormessage)

def jsonPrettyPrint(theObject):
    return json.dumps(theObject, indent=2).replace('\\n', '\r\n')

def criticalError(message, errormessage):
    tlogger.critical(errormessage,stack_info=True)
    return {"status": False, "message": message, "errormessage": errormessage}

def main(argv):
    # HACK POINT for debugging: assign argv here to alter normal behavior when debugging.
    # The second element in the list could be input of a JSON file, for example:
    # argv = ['dummy', r'@c:\notes\2022\10\GAIA-2484\requests\importcandidates_al_or.json']

    response = None

    # What mode are we in?
    global runmode
    (runmode, errormessage) = getMode(argv)

    config.set("runmode", runmode)

    # Connect to the logger
    initializeLogging(runmode)

    # If initialization is required we'll pass the buck and then exit when finished.
    if RunMode.LIBRARY_INITIALIZATION == runmode:
        showVerboseMessage = True
        utilities.initializer.performInitialization(showVerboseMessage)
        response = False

    elif RunMode.GET_USAGE == runmode:
        # Provide usage information
        request = Usage.generalUsageRequest
        if 1 < len(argv[1]):
            request["inquireabout"] = argv[1][1:]
        response = dispatch.Dispatch.dispatch(request)
        # We are printing to STDOUT to show the payload and then exiting.
        print(response["payload"])
        response = False

    elif RunMode.SSURGO_PORTAL_UI == runmode:
        # Note that Bottle, which is required for webpage, 
        # will only be available after the environment is initialized.
        # That occurs before the SSURGO_PORTAL_UI environment is declared.
        # We can test and ignore failure at this point.
        try:
            from dphost import webpage
            if config.osType == "nt":
                from ctypes import windll
                #change the title of the bottle server on a windows machine
                windll.kernel32.SetConsoleTitleW("SSURGO Portal - DO NOT CLOSE")
            
            print(
                "This command line interface is an integral part of the SSURGO Portal application. " +
                "When the webpage is closed this interface will self terminate. If closed while the application is in use, " +
                "the application will break and will have to be relaunched."
            )
            webpage.runServer()
        except:
            pass

    elif RunMode.DATA_LOADER == runmode:
        # read from stdin, check schema, get request object, handle failures
        (status, request, errormessage) = readStdin(argv[1])
        if not status:
            response = {"status":False, 
                "message": "Data Loader input error", "errormessage": errormessage}
        else:
            # dispatch with request object
            start_time = time.time()
            response = dispatch.Dispatch.dispatch(request)
            end_time = time.time()
            time_elapsed = (end_time - start_time)
            response["elapsedseconds"] = round(time_elapsed)

    # We need a legitimate mode
    else:
        response = criticalError("Critical error", f"Runmode {runmode} is undefined")

    if response:      
        print(jsonPrettyPrint(response))        
    
    if tlogger:
        tlogger.info("Application stopping.")
        logging.shutdown()

if __name__ == "__main__":
    main(sys.argv)
    sys.exit()

