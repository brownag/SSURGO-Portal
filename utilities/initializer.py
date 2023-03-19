# utilities\initializer.py

from os import path, remove
import platform
import shutil
import sys
import traceback
import zipfile

import config
from .runchild import RunChild
from template_logger import tlogger

# Perform one-time initialization.
# The user will be prompted to quit or continue.
# If continuing then the libraries will be installed.

def askToProceed():
    # Let user know they've a choice.
    # Returns False if quitting, True if proceeding.
    print('''
The Python library needs to be initialized (this is normally a one-time 
operation). You must be connected to the Internet for this operation to 
succeed.''')
    print()
    response = input('Enter "p" to proceed, anything else to quit: ')
    if response and len(response) >= 1:
        tlogger.info('askToProceed: response == "p"')
        return 'p' == response[0].lower()
    else:
        tlogger.info('askToProceed: response != "p"')
        return False

def notifyCompletion(status, message, showVerboseMessage):
    tlogger.info(f'notifyCompletion: status={status}, message={message}')
    if not status:
        print('An error occurred during initialization:')
        print(message)
    else:
        print('The initialization completed without error')
        if showVerboseMessage:
            print(message)

    print()
    response = input('Press the "Enter" key to finish the initialization: ')
    tlogger.info(f'Initialization completed with status={status}')

    return

def getPythonVersion():
    # Determine current Python version (major.minor).
    # Used for identifying required GDAL library wheel.
    # Returns tuple (versionString, errorMessage)
    versionTuple = platform.python_version_tuple()
    if versionTuple[0] == '3' and versionTuple[1] == '9':
        return ('3.9', False)
    elif versionTuple[0] == '3' and versionTuple[1] == '10':
        return ('3.10', False)
    else:
        return (False, f'Invalid Python version found: {sys.version}')

def installGdal(showVerboseMessage):
    # Install GDAL wheel if needed
    # Usage: (status, message) = installGdal(True/False)

    # If import works then we do not need to install the GDAL wheel.
    try:
        from osgeo import ogr, osr, gdal
        return (True, "")
    except:   
        # GDAL not installed. 
        # Base Wheel selection on Python version.
        (versionString, versionErrorMessage) = getPythonVersion()

        if not versionString:
            return (False, versionErrorMessage)

        # Identify the Wheel file
        # We assume that the config.py definition uses "/" folder separators for the Whl path.
        whl = (config.get("gdalWheel"))[versionString]
        if config.isPyzFile == True:
            # Case: IN a PYZ, extract the file
            try:
                wfn = whl.split('/').pop()
                tail = 'utilities\\initialize.pyc'
                zippath = __file__[0:(len(__file__) - len(tail)) - 1]
                fileLocation = zippath.split('\\')
                fileLocation.pop()
                fileLocation = '\\'.join(fileLocation)
                fileLocation = path.join(fileLocation, wfn)  
                extractMsg = f'installGdal(): extracting GDAL from whl={whl} at zippath={zippath} to fileLocation={fileLocation}'
                tlogger.info(extractMsg) 
                if showVerboseMessage: print(extractMsg)
                with zipfile.ZipFile(zippath, mode='r') as archive:
                    with archive.open(whl) as whlObject:
                        with open(fileLocation, 'wb') as outfile:
                            shutil.copyfileobj(whlObject, outfile)
            except Exception as e:
                tlogger.critical('Failed to extract GDAL Wheel: ' + str(e))
                tlogger.critical(traceback.format_exc())
                return (False, 'Failed to open GDAL Wheel: ' + str(e))
            cmd = ["pip", "install", fileLocation]
        else:
            # Case: Not in a PYZ, find the file in its expected location
            scriptLocation = sys.argv[0].split('\\')
            scriptLocation.pop()
            scriptLocation = '\\'.join(scriptLocation)  
            whl = path.join(scriptLocation, whl.replace('/', '\\'))
            if not path.isfile(whl):
                errormessage = f'Whl file ({whl}) does not exist'
                tlogger.critical(errormessage,stack_info=True)
                return (False, errormessage)
            cmd = ["pip", "install", whl]

        # Perform the installation
        try:
            runsubStartMsg = f'Performing runsub with cmd={cmd}'
            tlogger.info(runsubStartMsg) 
            if showVerboseMessage: print(runsubStartMsg)
            (status, childMessage) = RunChild.runSub(cmd, showVerboseMessage)
            if status:
                errormessage = "OSGeo (GDAL/OGR) libraries not found, will install for current user" + childMessage
            else:
                errormessage = "Failure installing OSGeo (GDAL/OGR) libraries" + childMessage
                tlogger.critical(errormessage,stack_info=True)
                return (False, errormessage)
        except Exception as e:
            tlogger.critical('Runchild failure: ' + str(e))
            tlogger.critical(traceback.format_exc())
            return (False, 'Runchild failure:  ' + str(e))

        # try listing installation
        try:
            cmd = ["pip", "freeze"]
            runsubPipFreezeMsg = f'Performing runsub with cmd={cmd}'
            tlogger.info(runsubStartMsg)
            if showVerboseMessage: print(runsubPipFreezeMsg)
            (status, childMessage) = RunChild.runSub(cmd, showVerboseMessage)
            if status:
                message = "OSGeo (GDAL/OGR) libraries installed" + childMessage
                if config.isPyzFile == True:
                    if path.isfile(fileLocation):
                        try:
                            remove(fileLocation)
                            return (True, message)
                        except Exception as e:
                            errormessage = 'Unexpected error during PYZ GDAL file deletion of {fileLocation}.' + str(e)
                            tlogger.critical(errormessage)
                            tlogger.critical(traceback.format_exc())
                            return (False, errormessage)                                
                    else:
                        errormessage = f'Failure deleting unzipped wheel f{whl}'
                        return (False, errormessage)
                else:
                    return (True, message)
            else:
                errormessage = 'Unexpected error during OSGeo (GDAL/OGR) installation.' + childMessage
                tlogger.critical(errormessage,stack_info=True)
                return (False, errormessage)
        except Exception as e:
            tlogger.critical('pip freeze failure: ' + str(e))
            tlogger.critical(traceback.format_exc())
            return (False, 'pip freeze failure:  ' + str(e))                

def installLibrariesViaInternet(showVerboseMessage):
    installLibrariesViaInternet = config.get("installLibrariesViaInternet")
    if installLibrariesViaInternet:
        librariesToInstall = []
        tlogger.info('installLibrariesViaInternet(): checking for unavailable libraries')
        for libraryName in installLibrariesViaInternet:
            try:
                importStatement = f'import {libraryName}'
                exec(importStatement)
            except Exception as ex:
                librariesToInstall.append(libraryName)

        if librariesToInstall:
            cmd = ["pip", "install"] + librariesToInstall
            internetInstallStartMsg = f'Installing library(ies) via Internet using cmd={cmd}'
            tlogger.info(internetInstallStartMsg)
            print(internetInstallStartMsg)
            (status, childMessage) = RunChild.runSub(cmd, showVerboseMessage)
            tlogger.info(f"Library installation status: {status}, childMessage={childMessage}")
            if status and not showVerboseMessage:
                print("Libraries installed")
            elif status:
                print(f"Libraries installed, childMessage={childMessage}")
            else:
                errormessage = "Failure installing libraries via Internet" + childMessage
                tlogger.critical(errormessage,stack_info=True)
                return (False, errormessage)

            # try listing installation
            cmd = ["pip", "freeze"]
            if showVerboseMessage:
                print("Checking freeze list")
            (status, childMessage) = RunChild.runSub(cmd, showVerboseMessage)
            tlogger.info(f"Freeze list check, status={status}, childMessage={childMessage}")
            if status:
                message = f"Freeze list = {childMessage}"
                # Clean up after ourselves
                return (True, message)
            else:
                errormessage = f'Unexpected error during Internet library check, childMessage={childMessage}'
                tlogger.critical(errormessage,stack_info=True)
                return (False, errormessage)

        else:
            noInstallationRequiredMsg = '...no Internet Library installation(s) required'
            tlogger.info(noInstallationRequiredMsg)
            return (True, noInstallationRequiredMsg)

def performInitialization(showVerboseMessage):
    # Perform initialization
    # Usage: (status, message) = performInitialization

    # Proceed?
    if not askToProceed():
        return (False, "Canceled")

    # Initialize GDAL library from the stored wheel.
    (status, message) = installGdal(showVerboseMessage)

    # Initialize libraries from Internet
    if status:
        (status, message2) = installLibrariesViaInternet(showVerboseMessage)
        message = message + '\n' + message2

    notifyCompletion(status, message, showVerboseMessage)