# config.py

import sys
import os
from runmode import RunMode

# Run-time configuration values
# Defined as a plain old module.
if sys.argv[0].endswith('.pyz'):
    isPyzFile = True
else:
    isPyzFile = False

osType = os.name

static_config = {
    # Cache the logging mode here
    "runmode" : RunMode.UNDEFINED,

    # Should SSURGO Portal UI requests be checked for schema conformance?
    "checkDpRequestsAgainstSchema": True,

    # Required libraries are installed from stored "wheel" files or
    # across the internet. In this version the wheel is used only for GDAL.

    # Relative path to GDAL Wheel for one-time installation - Python version dependent
    # The following choices are only relevant for: (as reported by os.environ)
    #   PROCESSOR_ARCHITECTURE=AMD64
    #   OS=Windows_NT
    # The list can be expanded subject to Wheel availability and os detection.
    "gdalWheel": {
        '3.9': 'python_libraries/GDAL-3.3.3-cp39-cp39-win_amd64.whl',
        '3.10': 'python_libraries/GDAL-3.4.2-cp310-cp310-win_amd64.whl'
    },

    # Internet library names are presented in a list.
    "installLibrariesViaInternet": ['bottle', 'jsonschema'],
    
    # Relative path to empty database templates and appropriate suffix for new files.
    "emptyTemplates": {
        'SpatiaLite': 
            {"path": r'templates\spatialite.sqlite', "suffix": '.sqlite', "textTemplate": False},
        'GeoPackage': 
            {"path": r'templates\geopackage.gpkg', "suffix": '.gpkg', "textTemplate": False},
        'SpatiaLite (for SSURGO from NASIS or Staging)': 
            {"path": r'templates\spatialite_textkey.sqlite', "suffix": '.sqlite', "textTemplate": True},
        'GeoPackage (for SSURGO from NASIS or Staging)': 
            {"path": r'templates\geopackage_textkey.gpkg', "suffix": '.gpkg', "textTemplate": True}
    },

    "versionInformation": {
        'ApplicationVersion': '1.2.3.4', #This will be populated by the X build Job (To be created) & will be updated when we deploy. This value won't change in our repository. During local development, the version will always be 1.2.3.4.
        'SQLiteSSURGOTemplateVersion': '5.0', #Needs to be manually updated by a developer (doesn't change often). All templates will have the same version. This is the version number of the SQLiteSSURGOTemplate that's included in the Project.
        'SSURGOVersion': '2.3.3' #Needs to be manually updated by a developer (doesn't change often). This is the SSURGO database model version used to create the SSURGO template database schema. This value needs to match what we have in the 'systemtemplateinformation' table inside the template database. This version also aligns with the version.txt file inside Tabular folders. 
    }
}

dynamic_config = static_config

def reset():
    global static_config
    global dynamic_config
    dynamic_config = static_config

def get(key):
    global dynamic_config
    return dynamic_config[key]

def set(key, value):
    global dynamic_config
    dynamic_config[key] = value
