# dlcore\requestschema.py

# References:
#	https://python-jsonschema.readthedocs.io/en/stable/
#	http://donofden.com/blog/2020/03/15/How-to-Validate-JSON-Schema-using-Python
#   http://json-schema.org/
#   https://json-schema.org/understanding-json-schema/reference/type.html
#   https://www.tutorialspoint.com/json/json_schema.htm
#   https://json-schema.org/understanding-json-schema/structuring.html

# Programmer notes: 
#   1. The Schemas are permissive - new properties may mostly be added that are 
#     not defined in the schemas. Application code should adhere to the 
#     schema-defined properties and ignore all other properties.
#     Future versions of this module will be increasingly more restrictive.
#   2. Dictionaries can be merged with "newDict = dict1 | dict2" (Python 3.9 and newer)

import json
from jsonschema import exceptions, validate
import sys
from template_logger import tlogger
import traceback

# Common request properties (for boilerplate inclusion)
commonRequestProperties = {
        "request":{
            "description":"The type of request",
            "type":"string"
        },
        "comment":{
            "description":"Optional comment.",
            "type":"string"		
        },
        "verbose":{
            "description":"Should the request be echoed in the response and response schema checked? Optional, defaults to false.",
            "type":"boolean"
        }
}

# Common response properties
commonResponseProperties = {
    "request": commonRequestProperties,
    "comment":{
        "description":"Optional comment.",
        "type":"string"		
    },
    "status":{
        "description":"Successful?",
        "type":"boolean"
    },
    "message": {
        "description":"Optional message",
        "type":"string"			
    },
    "errormessage": {
        "description":"Optional error message",
        "type":"string"			
    },
    "elapsedseconds": {
        "description":"Number of seconds elapsed while servicing the request. Rounded to the nearest second, automatically generated.",
        "type":"integer"
    }
}

# Dictionary of all request+response schemas
# Note that all property names are lower case.
schemaDictionary = {}

# Utility requests
requestName = "getstatus"
schemaDictionary[requestName] = {}
schemaDictionary[requestName]["request"] = {
    "$schema":"http://json-schema.org/draft-04/schema#",
    "title":f"request: {requestName}",
    "comment":f"Quick check for application responsiveness.",
    "description":f"Schema for a {requestName} request",
    "type":"object",
    "properties": commonRequestProperties,
    "required":["request"]
}
schemaDictionary[requestName]["response"] = {
    "$schema":"http://json-schema.org/draft-04/schema#",
    "title":f"request: {requestName}",
    "description":f"Schema for a {requestName} response",
    "type":"object",
    "properties": commonResponseProperties,
    "required":["status"]
}

requestName = "getusage"
schemaDictionary[requestName] = {}
schemaDictionary[requestName]["request"] = {
    "$schema":"http://json-schema.org/draft-04/schema#",
    "title":f"request: {requestName}",
    "description":f"Schema for a {requestName} request",
    "comment":f"Return usage information in payload.",
    "type":"object",
    "properties": (commonRequestProperties | {"inquireabout": {
        "description":"Return schema for this request, omit if list is to be presented",
        "type":"string"			
    }}),
    "required":["request"]
}
schemaDictionary[requestName]["response"] = {
    "$schema":"http://json-schema.org/draft-04/schema#",
    "title":f"request: {requestName}",
    "description":f"Schema for a {requestName} response",
    "type":"object",
    "properties": (commonResponseProperties | {"payload": {
        "description":"Display contents",
        "type":"string"			
    }}),
    "required":["status", "payload"]
}

requestName = "getwindowsdriveletters"
schemaDictionary[requestName] = {}
schemaDictionary[requestName]["request"] = {
    "$schema":"http://json-schema.org/draft-04/schema#",
    "title":f"request: {requestName}",
    "description":f"Schema for a {requestName} request",
    "comment":f"Return all drive letters (only valid for Microsoft Windows)",
    "type":"object",
    "properties": commonRequestProperties,
    "required":["request"]
}
schemaDictionary[requestName]["response"] = {
    "$schema":"http://json-schema.org/draft-04/schema#",
    "title":f"request: {requestName}",
    "description":f"Schema for a {requestName} response",
    "type":"object",
    "properties": (commonResponseProperties | {"drives": {
        "description":"List of drive letters.",
        "type":"string"
    }}),
    "required":["status", "drives"]
}

requestName = "getfoldertree"
schemaDictionary[requestName] = {}
requestProperties_getfoldertree = (commonRequestProperties | {
        "path":{
            "description":"Arbitrary starting path for search.",
            "type":"string"		
        },
        "folderpattern":{
            "description":"Regex pattern for folder name selection, no filtering if a zero-length string.",
            "type":"string"		
        },
        "filepattern":{
            "description":"Regex pattern for file name selection, no filtering if a zero-length string.",
            "type":"string"		
        },
        "ignorefoldercase":{
            "description":"If using matchpattern, should a case-blind matching be performed?",
            "type":"boolean"		
        },
        "ignorefilecase":{
            "description":"If using matchpattern, should a case-blind matching be performed?",
            "type":"boolean"		
        },
        "showfiles":{
            "description":"If false, do not show any files.",
            "type":"boolean"		
        },
        "maxdepth":{
            "description":"Maximum recursion depth, 0 prohibits any recursion",
            "type":"number"		
        }})
schemaDictionary[requestName]["request"] = {
    "$schema":"http://json-schema.org/draft-04/schema#",
    "title":f"request: {requestName}",
    "description":f"Schema for a {requestName} request",
    "comment":f"Return file and folder tree in nodes list.",
    "type":"object",
    "properties": requestProperties_getfoldertree,
    "required":["request","path","folderpattern","filepattern","ignorefoldercase","ignorefilecase","showfiles","maxdepth"]
}
nodesComment = 'Each nodes list element will consist of a 3-tuple of (fileOrFolderName, isFolder, nodes). '\
    + 'Note the recursive nodes content. "isFolder" is true if the object is a folder. "nodes" are the '\
    + 'children of the current named node, omitted if a file or at max depth.'
schemaDictionary[requestName]["response"] = {
    "$schema":"http://json-schema.org/draft-04/schema#",
    "title":f"request: {requestName}",
    "description":f"Schema for a {requestName} response",
    "type":"object",
    "properties": (commonResponseProperties | {
        "nodes":{
            "description":"A list of 3-tuples (name, lastmodified, type, nodes).",
            "comment": nodesComment,
            "type":"array",
            "prefixItems": [
                {"type": "string"},
                {"type": "string"},
                {"type": "string"},
                {"$ref": "#"}
            ]
    }}),
    "required":["status"]
}

# Use case 1: Create a new template database in a folder that I select.
requestName = "gettemplatecatalog"
schemaDictionary[requestName] = {}
schemaDictionary[requestName]["request"] = {
    "$schema":"http://json-schema.org/draft-04/schema#",
    "title":f"request: {requestName}",
    "description":f"Schema for a {requestName} request",
    "comment":f"Returns JSON containing information about all available empty SSURGO SQLite templates.",
    "type":"object",
    "properties": commonRequestProperties,
    "required":["request"]
}
schemaDictionary[requestName]["response"] = {
    "$schema":"http://json-schema.org/draft-04/schema#",
    "title":f"request: {requestName}",
    "description":f"Schema for a {requestName} response",
    "type":"object",
    "properties": (commonResponseProperties | {
        "emptytemplates": {
            "description": "Dictionary by description containing dictionary entries for path, suffix & textTemplate flag",
            "type": "object",
            "properties": {
                "path": {
                    "description":"Path, starting under pyz root",
                    "type":"string"
                },
                "suffix":{
                    "description":"Required suffix in ArcGIS Pro for database file.",
                    "type":"string"
                },
                "textTemplate":{
                    "description":"Flag that denotes a template as Text or not",
                    "type":"boolean"
                }
            }
        }
    }),
    "required":["status", "emptytemplates"]
}

requestName = "copytemplatefile"
schemaDictionary[requestName] = {}
requestProperties_getfoldertree = (commonRequestProperties | {
    "templatename" : {
        "description":"Name of the template to copy, must match a catalog name.",
        "type":"string"		
    },
    "folder": {
        "description": "Destination folder for copy, created if it does not exist.",
        "type":"string"
    },
    "filename": {
        "description": "Name to give the copied file. Do not include the filename suffix, the appropriate one will be added.",
        "type":"string"
    },
    "overwrite": {
        "description": "If true then overwrite an existing file with same name.",
        "type":"boolean"
    }
})
schemaDictionary[requestName]["request"] = {
    "$schema":"http://json-schema.org/draft-04/schema#",
    "title":f"request: {requestName}",
    "description":f"Schema for a {requestName} request",
    "comment":f"Copies a template file to a specified folder path and name..",
    "type":"object",
    "properties": requestProperties_getfoldertree,
    "required":["request", "templatename", "folder", "filename", "overwrite"]
}
schemaDictionary[requestName]["response"] = {
    "$schema":"http://json-schema.org/draft-04/schema#",
    "title":f"request: {requestName}",
    "description":f"Schema for a {requestName} response",
    "type":"object",
    "properties": commonResponseProperties,
    "required":["status"]
}

# Use case 2: Open an existing template database ("ET") in a folder that I select.
requestName = "opentemplate"
schemaDictionary[requestName] = {}
schemaDictionary[requestName]["request"] = {
    "$schema":"http://json-schema.org/draft-04/schema#",
    "title":f"request: {requestName}",
    "comment":f"Opens a SQLite file to confirm that it meets certain minimal criteria.",
    "description":f"Schema for a {requestName} request",
    "type":"object",
    "properties": (commonRequestProperties | {
        "database":{
            "description": "Path to the SQLite template.",
            "type": "string"
        }
    }),
    "required":["request", "database"]
}
schemaDictionary[requestName]["response"] = {
    "$schema":"http://json-schema.org/draft-04/schema#",
    "title":f"request: {requestName}",
    "description":f"Schema for a {requestName} response",
    "type":"object",
    "properties": commonResponseProperties,
    "required":["status"]
}

# Use case 3: View all loaded soil data (“Soil Survey Areas” (SSA), with “areasymbol”) within an ET.
requestName = "getdatabaseinventory"
schemaDictionary[requestName] = {}
schemaDictionary[requestName]["request"] = {
    "$schema":"http://json-schema.org/draft-04/schema#",
    "title":f"request: {requestName}",
    "comment":f"List survey areas and related data within a SQLite database.",
    "description":f"Schema for a {requestName} request",
    "type":"object",
    "properties": (commonRequestProperties | {
        "database":{
            "description": "Path to the SQLite template.",
            "type": "string"
        },
        "wheretext": {
            "description": 'Optional text to follow a "WHERE" keyword. Note that sacatalog column names must be proceeded by "c.". Caution: SQLite is case sensitive.',
            "type": "string"
        }
    }),
    "required":["request", "database"]
}
schemaDictionary[requestName]["response"] = {
    "$schema":"http://json-schema.org/draft-04/schema#",
    "title":f"request: {requestName}",
    "description":f"Schema for a {requestName} response",
    "type":"object",
    "properties": (commonResponseProperties | {
        "records" : {
            "description": "Dictionary by areasymbol containing areaname, saverest and istabularonly.",
            "type": "object",
            "properties":{
                "areaname":{
                    "description":"full name of the areasymbol",
                    "type":"string"
                },
                "saverest":{
                    "description":"Date survey area version established.",
                    "type":"string"
                },
                "istabularonly":{
                    "description":"Is the survey area without spatial data?",
                    "type":"boolean"
                }
            }
        }
    }),
    "required":["status"]
}

# Use case 4: Delete one or more SSAs within an ET.
requestName = "deleteareasymbols"
schemaDictionary[requestName] = {}
schemaDictionary[requestName]["request"] = {
    "$schema":"http://json-schema.org/draft-04/schema#",
    "title":f"request: {requestName}",
    "comment":f"Delete the specified areasymbols from the database.",
    "description":f"Schema for a {requestName} request",
    "type":"object",
    "properties": (commonRequestProperties | {
        "database":{
            "description": "Path to the SQLite template.",
            "type": "string"
        },
        "areasymbols": {
            "description": 'List of areasymbols to remove (list of string).',
            "comment": "Schema not properly defined for the list.",
            "type": "array",
            "items":{
                "type":"string"
            }
        }
    }),
    "required":["request", "database", "areasymbols"]
}
schemaDictionary[requestName]["response"] = {
    "$schema":"http://json-schema.org/draft-04/schema#",
    "title":f"request: {requestName}",
    "description":f"Schema for a {requestName} response",
    "type":"object",
    "properties": commonResponseProperties,
    "required":["status"]
}

# Use case 5: Import one or more SSAs into an ET from a set of subfolders that I choose under a containing folder that I specify.
requestName = "pretestimportcandidates"
schemaDictionary[requestName] = {}
schemaDictionary[requestName]["request"] = {
    "$schema":"http://json-schema.org/draft-04/schema#",
    "title":f"request: {requestName}",
    "comment":f'Perform a "pre-test" on subfolders under a root folder.',
    "description":f"Schema for a {requestName} request",
    "type":"object",
    "properties": (commonRequestProperties | {
        "database":{
            "description": "Path to the SQLite template.",
            "type": "string"
        },
        "root": {
            "description": "Path to the folder containing zero or more SSURGO packages (must be unzipped).",
            "type": "string"
        },
        "istabularonly" : {
            "description": "If true then do not check spatial data.",
            "type": "boolean"
        },
        "subfolders": {
            "description": 'List of child folders, one for each SSURGO package. Optional, if omitted then all child folders of the root will be tested.',
            "type":"array",
            "items": {
                "type":"string"
            }
        }
    }),
    "required":["request", "database", "root", "istabularonly"]
}
schemaDictionary[requestName]["response"] = {
    "$schema":"http://json-schema.org/draft-04/schema#",
    "title":f"request: {requestName}",
    "description":f"Schema for a {requestName} response",
    "comment" : '''Note that the overall "status" is true if the request was performed without a non-test failure,
the "allpassed" is true only if none of the child folders failed''',
    "type":"object",
    "properties": (commonResponseProperties | {
        "allpassed" : {
            "description" : "True if there were no child folder pretest failures",
            "type": "boolean"
        },
        "subfolders": {
            "description": 'List of child folder dictionaries, one for each SSURGO package.',
            "type": "array",
            "items": {
                "type":"object",
                "properties":{
                    "childfoldername":{
                        "description":"the name of the folder",
                        "type":"string"
                    },
                    "preteststatus":{
                        "description":"if true then childfoldername pretest was successful, if false then pretest failed.",
                        "type":"boolean"
                    },
                    "errormessage":{
                        "description":"Error message generated by pretest of the childfoldername.",
                        "type":"string"
                    },
                    "areasymbols": {
                        "description":"The dictionary of areasymbols within the childfoldername.", 
                        "type": "object",
                        "properties": {
                            "areasymbol":{
                                "description":"name of the areasymbol",
                                "type":"string"
                            },
                            "details":{
                                "description":"Value of areasymbols dictionary.It is dictionary of areaname, fileversion and dbversion",
                                "type":"object",
                                 "properties":{
                                    "areaname" : {
                                        "description":"areaname of the areasymbol.",
                                        "type":"string"
                                        },
                                    "fileversion":{
                                        "description":"Date of surveyarea saverest in sacatalog.txt",
                                        "type":"string "
                                        },
                                    "dbversion":{
                                        "description":"Date of surveyarea saverest in sacatlog table in db if areasymbol already exist",
                                        "type":"string"
                                        }
                                 }
                            }

                        }
                    },
                    "sharedSSAs":{
                        "description":"The dictionary of duplicate areasymbols within the childfoldername. Key is areasymbol and Value is shared subfolders list", 
                        "type": "object"


                    }

                },
                "required":["childfoldername", "preteststatus"]
            }
        }
    }),
    "required":["status"]
}

requestName = "importcandidates"
schemaDictionary[requestName] = {}
schemaDictionary[requestName]["request"] = {
    "$schema":"http://json-schema.org/draft-04/schema#",
    "title":f"request: {requestName}",
    "comment":f'Import SSURGO data from subfolders under a root folder. The import terminates if any folder fails.',
    "description":f"Schema for a {requestName} request",
    "type":"object",
    "properties": (commonRequestProperties | {
        "database":{
            "description": "Path to the SQLite template.",
            "type": "string"
        },
        "root": {
            "description": "Path to the folder containing zero or more SSURGO packages (must be unzipped).",
            "type": "string"
        },
        "skippretest": {
            "description" : "Should the pre-test be performed?",
            "comment" : 'The pretest should only be skipped if the subfolders have been filtered by a "pretestimportcandidates" evaluation',
            "type" : "boolean"
        },
        "istabularonly" : {
            "description": "If true then do not attempt to load spatial data.",
            "comment": "Only tabular data will be imported, regardless of the existence of any spatial data in the folders.",
            "type": "boolean"
        },
        "loadinspatialorder":{
            "description": "If true load subfolders in spatial order, from northwest to southeast.",
            "type":"boolean"
        },
        "loadspatialdatawithinsubprocess":{
            "description": "Should spatial data be loaded using a subprocess?", 
            "comment":'''
            In the case where a shapefile contains polygonal data, the OGR import will 
            send a GEOS warning to STDOUT. This is undesirable in the context of a 
            Data Loader request as it will yield a non-JSON STDOUT string.
            Employing a subprocess allows the warning(s) to be captured within the 
            JSON response.
            ''',
            "default":True,
            "type": "boolean"
        },
        "dissolvemupolygon":{
            "description":"Should mupolygon geometries be dissolved by mukey value? Only used when the underlying mupolygon.shape column is 'MULTIPOLYGON', otherwise its value ignored.",
            "type":"boolean"
        },
        "subfolders": {
            "description": 'List of child folder names, one for each SSURGO package.',
            "type": "array",
            "items": {
                "description":"the name of the folder",
                "type":"string"
            },
        },
        "includeinterpretationsubrules": {
            "description":"If IncludeInterpretationSubRules applies (selected, meaning the box is checked in UI) then we need to load ALL RECORDS IN coniterp table, else only load those with ruledepth =0.  The default should be ruledepth = 0 (and the box should not be checked in UI). The user needs to check the box in UI to load ALL RECORDS.",
            "type":"boolean"
        }
    }),
    "required":["request", "database", "root", "skippretest", "istabularonly", "loadinspatialorder", "loadspatialdatawithinsubprocess", "dissolvemupolygon", "subfolders"]
}
schemaDictionary[requestName]["response"] = {
    "$schema":"http://json-schema.org/draft-04/schema#",
    "title":f"request: {requestName}",
    "description":f"Schema for a {requestName} response",
    "comment" : '''Note that the overall "status" is true if the request was performed without a non-import failure',
the "allimported" is true only if none of the child folders failed''',
    "type":"object",
    "properties": (commonResponseProperties | {
        "allimported" : {
            "description" : "True if there were no child folder import failures",
            "type": "boolean"
        },
        "subfolders": {
            "description": 'List of child folder dictionaries, one for each SSURGO package.',
            "type": "array",
            "items": {
                "type":"object",
                "properties":{
                    "childfoldername":{
                        "description":"the name of the folder",
                        "type":"string"
                    },
                    "elapsedsecondstabularimport": {
                        "description":"Number of seconds elapsed while importing tabular data. Rounded to the nearest second, automatically generated.",
                        "type":"integer"
                    },
                    "elapsedsecondsspatialimport": {
                        "description":"Number of seconds elapsed while importing spatial data. Rounded to the nearest second, automatically generated.",
                        "type":"integer"
                    },
                    "areasymbols": {
                        "description":"The dictionary of areasymbols within the childfoldername.", 
                        "type": "object",
                        "properties": {
                            "areasymbol":{
                                "description":"name of the areasymbol",
                                "type":"string"
                            },
                            "details":{
                                "description":"Value of areasymbols dictionary.It is dictionary of areaname, fileversion and dbversion",
                                "type":"object",
                                 "properties":{
                                    "areaname" : {
                                        "description":"areaname of the areasymbol.",
                                        "type":"string"
                                        },
                                    "fileversion":{
                                        "description":"Date of surveyarea saverest in sacatalog.txt",
                                        "type":"string "
                                        }
                                 }
                            }

                        }
                    }
                }
            },
        }
    }),
    "required":["status"]
}

requestName = "importspatialdata"
schemaDictionary[requestName] = {}
schemaDictionary[requestName]["request"] = {
    "$schema":"http://json-schema.org/draft-04/schema#",
    "title":f"request: {requestName}",
    "comment":f'Import SSURGO spatial data from shapefiles under a specified path. Note that this activity is isolated to support its use in a child process.',
    "description":f"Schema for a {requestName} request",
    "type":"object",
    "properties": (commonRequestProperties | {
        "database":{
            "description": "Path to the SQLite template.",
            "type": "string"
        },
        "shapefilepath":{
            "description": "The fully-qualified folder name that contains the shapefiles.",
            "type": "string"
        },
        "dissolvemupolygon":{
            "description":"Should mupolygon geometries be dissolved by mukey value?",
            "type":"boolean"
        },
        "shapefiles":{
            "description":"Dictionary (by tablename) with the shapefile name (without .shp filename suffix) as the value.",
            "type":"object",
            "patternProperties": {
                "shapefilename": { "type": "string" },
                '^[^<>:"/\\|?*]+$': { "type": "string" }
            },
            "additionalProperties": False
        }
    }),
    "required":["request", "database", "shapefilepath", "dissolvemupolygon", "shapefiles"],
    "additionalProperties": False
}
responseComment = \
    'Note that the overall "status" is true if the request ' \
    + 'was performed without a non-import failure, ' \
    + 'the "allimported" is true only if none of the child ' \
    + 'shapefiles failed. The "errormessage"  shows the ' \
    + 'failing shapefile if appropriate.'
schemaDictionary[requestName]["response"] = {
    "$schema":"http://json-schema.org/draft-04/schema#",
    "title":f"request: {requestName}",
    "description":f"Schema for a {requestName} response",
    "comment" : responseComment,
    "type":"object",
    "properties": (commonResponseProperties | {
        "allimported" : {
            "description" : "True if there were no child shapefile import failures",
            "type": "boolean"
        }
    }),
    "required":["status","allimported"],
    "additionalProperties": False
}
requestName = "logjavascripterror"
schemaDictionary[requestName] = {}
schemaDictionary[requestName]["request"] = {
    "$schema":"http://json-schema.org/draft-04/schema#",
    "title":f"request: {requestName}",
    "comment":f'Place an error that occured inside of the Java Script into the log file',
    "description":f"Schema for a {requestName} request",
    "type":"object",
    "properties": (commonRequestProperties | {
        "eventStack":{
            "description": "Contains the JavaScript call stack",
            "type": "string"
        }
    }),
    "required":["request", "eventStack"],
    "additionalProperties": False
}
schemaDictionary[requestName]["response"] = {
    "$schema":"http://json-schema.org/draft-04/schema#",
    "title":f"request: {requestName}",
    "description":f"Schema for a {requestName} response",
    "type":"object",
    "properties": (commonResponseProperties | {"message": {
        "description":"Message returned to Java Script",
        "type":"string"			
    }}),
    "required":["status"]
}

def parseRequest(json_data):
    """REF: https://json-schema.org/ """
    # Validates json_data string or Python object against related request schema
    # If valid returns True and returns the request object
    # and logs an information message.
    # If not a defined request or bad schema, returns False and logs 
    # an error.
    # usage: (status, requestObject, errormessage) = parseRequest(json_data)
    
    try:
        # Classify the input object type
        if isinstance(json_data, str):
            # Try to create a Python object from the string
            errormessage = "Invalid JSON format? Unable to understand JSON request"
            representation = json.loads(json_data)
        elif isinstance(json_data,dict):
            # Treat the dictionary as derived from JSON
            representation = json_data
        else:
            # Neither a string nor a dictionary
            format(type(json_data))
            errormessage = f'json_data is neither a string nor a dictionary, it is {format(type(json_data))}.'
            tlogger.critical(errormessage, stack_info=True)
            return (False, 'Application error detected by parseRequest(json_data).', errormessage)

        # Grab the "request" name
        if not "request" in representation:
            errormessage = f'"request" value missing from JSON request'
            tlogger.error(errormessage)
            return (False, None, errormessage)
        requestName = representation["request"].lower()

        # Is it in our schema dictionary?
        errormessage = f'Invalid request name? Unable to retrieve request name "{requestName}" from JSON request schema dictionary'
        if not requestName in schemaDictionary:
            tlogger.error(errormessage)
            return (False, None, errormessage)
        schema = schemaDictionary[requestName]
        # Confirm the parsability of the schema
        errormessage = f"Checking request schema for {requestName}"
        requestSchema = schema["request"]
        # Validate the request
        errormessage = f"Validating JSON request for {requestName}"
        validate(instance=representation, schema=requestSchema)

        # Success, return the request object
        tlogger.info(f"request: {requestName}")
        return (True, representation, None)

    except exceptions.SchemaError as err:
        errormessage = f'{errormessage}: {format(err)}' 
        tlogger.critical(errormessage)
        tlogger.critical(traceback.format_exc())
        return (False, None, errormessage)
    
    except (json.JSONDecodeError, exceptions.ValidationError) as err:
        errormessage = f'{errormessage}: {format(err)}' 
        tlogger.error(errormessage)
        return (False, None, errormessage)

    except Exception as err:
        (classType, exceptionMessage, tracebackObject) = sys.exc_info()
        errormessage = f'Unexpected exception type {format(classType)}. {errormessage}: {format(err)}' 
        tlogger.critical(errormessage)
        tlogger.critical(traceback.format_exc())
        return (False, None, errormessage)

def parseResponse(requestObject, responseObject):
    # Validates a response object against related response schema.
    # Assumes that the requestObject has a valid request value.
    # If valid returns True and no errrormessage, and logs an information message.
    # If not a defined request or bad schema, returns False and logs an error.
    # usage: (status, errormessage) = parseRequest(json_data)
    
    try:
        # Existence checks on method parameters
        errormessage = False
        if not requestObject:
            errormessage = 'parseResponse(): "requestObject" not true.'
        elif "request" not in requestObject:
            errormessage = 'parseResponse(): "request" not in "requestObject".'
        elif not responseObject:
            errormessage = 'parseResponse(): "responseObject" not true.'
        if errormessage:
            tlogger.critical(errormessage,stack_info=True)
            return (False, errormessage)

        # Retrieve opriginal request name
        requestName = requestObject["request"].lower()

        # Is it in our schema dictionary?
        errormessage = f'Invalid request name? Unable to retrieve request name "{requestName}" from JSON response schema dictionary'
        if not requestName in schemaDictionary:
            tlogger.critical(errormessage,stack_info=True)
            return (False, errormessage)
        schema = schemaDictionary[requestName]
        # Confirm the parsability of the schema
        errormessage = f"Checking response schema for {requestName}"
        responseSchema = schema["response"]

        errormessage = "Validating JSON response"
        validate(instance=responseObject, schema=responseSchema)

        # Success, return status
        return (True, None)

    except exceptions.SchemaError as err:
        errormessage = f'{errormessage}: {format(err)}' 
        tlogger.critical(errormessage)
        tlogger.critical(traceback.format_exc())
        return (False, errormessage)
    
    except (json.JSONDecodeError, exceptions.ValidationError) as err:
        errormessage = f'{errormessage}: {format(err)}' 
        tlogger.error(errormessage)
        return (False, errormessage)

    except Exception as err:
        (classType, exceptionMessage, tracebackObject) = sys.exc_info()
        errormessage = f'Unexpected exception type {format(classType)}. {errormessage}: {format(err)}' 
        tlogger.critical(errormessage)
        tlogger.critical(traceback.format_exc())
        return (False, errormessage)  