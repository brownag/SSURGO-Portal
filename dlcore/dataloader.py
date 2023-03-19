import sys
import csv
from os import listdir, path
from dlcore.dlutilities import DlUtilities
from utilities.runchild import RunChild
#import pandas as pd
import os
import time
import json
try:
    from osgeo import ogr, osr, gdal
except:
    pass
import sqlite3
from template_logger import tlogger
import traceback

class dataloader:

    def setcsvfieldsizelimit():
        maxInt = sys.maxsize
        while True:
    # decrease the maxInt value by factor 10 
    # as long as the OverflowError occurs.
            try:
                csv.field_size_limit(maxInt)
                break
            except OverflowError:
                maxInt = int(maxInt/10)
    

    def getSacatalogData(database, root, subfolder, getDbversion):
        # Retrieve areasymbol and saversion for the subfolder
        # usage: (status, message, errormessage, areasymbol) = getSacatalogData(database, root, subfolder)
        # Status is True if the sacatlog.txt file can be read and returns the areasymbols for a given subfolder name
        # areasymbols is dictionary in which key elements are SSAs and values are saverest
        try:
            sacatalogFilename = 'sacatlog.txt'
            filePath = os.path.join(root, subfolder, "tabular", sacatalogFilename)
            areasymbols = {} 
            (status, errormessage) = DlUtilities.testFileExists(filePath, f"Error in {sacatalogFilename}")
            if not status: return (False, "", errormessage, areasymbols)
            (status, tbcon, errormessage) = DlUtilities.create_connection(database)
            if not status: return  (status, "Error encountered.", errormessage, areasymbols)
            with open(filePath, 'r', encoding='UTF-8') as file:
                csvreader = csv.reader(file, delimiter='|', quotechar='"')
                for row in csvreader:
                    details = {}
                    details["areaname"] = str(row[1])
                    details["fileversion"] = str(row[3])

                    if getDbversion:
                        saverestquery = f"SELECT saverest from sacatalog where areasymbol = '{str(row[0])}';"
                        cursor = tbcon.cursor()
                        cursor.execute(saverestquery)
                        saverest = cursor.fetchone()
                        if saverest is None:
                            saverest = ""
                        else:
                            saverest = saverest[0]
                        details["dbversion"] = saverest
                    areasymbols[str(row[0])] = details
            if not tbcon:
                tbcon.close()

            if len(areasymbols.keys())==0:
                return (False, "", "No areasymbol found in sacatalog.txt", areasymbols)

            return (True, "", "", areasymbols)

        except Exception as ex:
            errormessage = f"Error while executing getsacatalog function in {subfolder}, Unexcepted error: {format(ex)}"
            tlogger.critical(errormessage)
            tlogger.critical(traceback.format_exc())
            return (False, "", errormessage, areasymbols)
    

    def checkTabularfolderpath(root, subfolder):
        #Usage: (status, message, errormessage) = checkTabularFolderPath(root, subfolder)
        try:
            tbfolderdir = os.path.join(root, subfolder)
            if "tabular" in os.listdir(tbfolderdir):
                return (True,"","")
            else:
                return (False,"",f"tabular folder is either invalid (case sensitive, lower case required) or missing in folder {subfolder}")
        except Exception as ex:
            errormessage = f"Error while executing checkTabularfolderpath function in {subfolder}, Unexcepted error: {format(ex)}"
            tlogger.critical(errormessage)
            tlogger.critical(traceback.format_exc())
            return (False, "", errormessage)
    

    def checkSpatialfolderpath(root, subfolder):
        #Usage: (status, message, errormessage) = checkSpatialFolderPath(root, subfolder)
        try:
            spfolderdir = os.path.join(root, subfolder)
            if "spatial" in os.listdir(spfolderdir):
                return (True,"","")
            else:
                return (False,"",f"spatial folder is either invalid (case sensitive, lower case required) or missing in folder {subfolder}")
        except Exception as ex:
            errormessage = f"Error while executing checkSpatialfolderpath function in {subfolder}, Unexcepted error: {format(ex)}"
            tlogger.critical(errormessage)
            tlogger.critical(traceback.format_exc())
            return (False, "", errormessage)
    

    def checkVersion(database, root, subfolder):
        #Usage: (status, message, errormessage) = checkversion(database, root, subfolder)
        try:
            versioncheckquery = f"SELECT value from systemtemplateinformation where name ='SSURGO Version';"
            (status, tbcon, errormessage) = DlUtilities.create_connection(database)
            if not status:
                return  (status, "Error encountered.", errormessage)
            cursor = tbcon.cursor()
            cursor.execute(versioncheckquery)
            stiversion = (cursor.fetchone())[0]

            versionfilename = 'version.txt'
            tbfolderpath = os.path.join(root, subfolder, "tabular")
            filePath = os.path.join(root, subfolder, "tabular", versionfilename)
            (status, errormessage) = DlUtilities.testFileExists(filePath, f"Error in {versionfilename}")
            if not status: return (False,"", errormessage)
            
            with open(filePath, 'r', encoding='UTF-8') as file:
                tbversion = (file.read().splitlines())[0]

            if tbcon:
                tbcon.close()

            if stiversion == tbversion:
                return (True, "", "")
            else:
                return (False, "", f"SSURGO version {tbversion} doesn't match database version {stiversion}")   

        except Exception as ex:
            errormessage = f"Error while executing checkVersion function in {subfolder}, Unexcepted error: {format(ex)}"
            tlogger.critical(errormessage)
            tlogger.critical(traceback.format_exc())
            return (False, "", errormessage)


    def checkEmptyShapefiles(database, root, subfolder, IsWSSAoi, areasym): 
        #Usage: (status, message, errormessage) = checkEmptyShapefiles(database, root, subfolder, areasym)
        try:
            driver = ogr.GetDriverByName('ESRI Shapefile')
            #shpfilenamelst = [ f"soilsa_a_{areasym}.shp", f"soilmu_a_{areasym}.shp" ]
            (status, tbcon, errormessage) = DlUtilities.create_connection(database)
            if not status: 
                return  (status, "Error encountered.", errormessage)
            cursor = tbcon.cursor()
            cursor.execute( "SELECT tabphyname,iefilename,iefilenameaoi from mdstattabs where tabphyname in ('sapolygon', 'mupolygon')" )
            tblist = cursor.fetchall()
            shapefileFolder = os.path.join(root, subfolder, 'spatial')

            for rw in tblist:
                if not IsWSSAoi:
                    shpfilepath= os.path.join(shapefileFolder, str(rw[1]) + "_" + areasym.lower()  + ".shp")
                    shpfilename= str(rw[1]) + "_" + areasym.lower() + ".shp"
                else:
                    shpfilepath= os.path.join(shapefileFolder, str(rw[2]) + ".shp")
                    shpfilename= str(rw[2]) + ".shp"

                (status, errormessage) = DlUtilities.testFileExists(shpfilepath, 'Error with shapefile')
                if not status: return (False, "", errormessage)

                dataSource = driver.Open(shpfilepath, 0)    # 0 means read-only. 1 means writeable.
                if dataSource == None:
                    return(False, "", f"Unable to open the shapefile {shpfilename} in folder {subfolder}")
                layer = dataSource.GetLayer()
                hasfeature = False
                for feature in layer:
                    hasfeature = True
                    break  

                if not hasfeature:
                    return (False, "", f"Shapefile {shpfilename} in folder {subfolder} is empty.")

            return (True, "", "")
        
        except Exception as ex:
            errormessage = f"Error while executing checkEmptyShapefiles function in {subfolder}, Unexcepted error: {format(ex)}"
            tlogger.critical(errormessage)
            tlogger.critical(traceback.format_exc())
            return (False, '', errormessage)


    def checkEPSGAuthorityCode(database, root, subfolder, IsWSSAoi, areasym):
        #Usage: (status, message, errormessage) = checkEPSGAuthorityCode(database, root, subfolder, areasym)

        try:
            driver = ogr.GetDriverByName('ESRI Shapefile')
            (status, tbcon, errormessage) = DlUtilities.create_connection(database)
            if not status:
                return  (status, "Error encountered.", errormessage)
            cursor = tbcon.cursor()
            cursor.execute("SELECT iefilename, iefilenameaoi from mdstattabs where tabletype in ('Spatial')")
            tblist = cursor.fetchall()
            shapefileFolder = os.path.join(root, subfolder, 'spatial')

            for rw in tblist:
                if not IsWSSAoi:
                    shpfilepath= os.path.join(shapefileFolder, str(rw[0]) + "_" + areasym.lower()  + ".shp")
                    shpfilename= str(rw[0]) + "_" + areasym.lower() + ".shp"
                else:
                    shpfilepath= os.path.join(shapefileFolder, str(rw[1]) + ".shp")
                    shpfilename= str(rw[1]) + ".shp"
                if not os.path.exists(shpfilepath):
                    return (False, "", f"{shpfilename} file not found on path {subfolder}")
                dataSource = driver.Open(shpfilepath, 0)    # 0 means read-only. 1 means writeable.
                if dataSource == None:
                    return(False, "", f"Unable to open the shapefile {shpfilename} in folder {subfolder}")
                layer = dataSource.GetLayer()
                spatialRef = layer.GetSpatialRef()
                if spatialRef == None:
                    return (False, "", f"Coordinate system of shapefile {shpfilename} in folder {subfolder} is not WGS84")
                rootauthoritycode =  spatialRef.GetAuthorityCode(None)
                if rootauthoritycode != '4326':
                    return (False, "", f"Coordinate system of shapefile {shpfilename} in folder {subfolder} is not WGS84")
            return (True, "", "")
        except sqlite3.Error as error:
            return (False, f"Error while executing function checkEPSGAuthorityCode", str(error.args[0]))
        except Exception as ex:
            errormessage = f"Error while executing function checkEPSGAuthorityCode in {subfolder}, Unexcepted error: {format(ex)}"
            tlogger.critical(errormessage)
            tlogger.critical(traceback.format_exc())
            return (False, "", errormessage)

        finally:
            if tbcon:
                tbcon.close()


    def pretestImportCandidates(request):
        root = request["root"]
        (status, errormessage) = DlUtilities.testFolderExists(root, 'Error in "root"')
        if not status: return { "status": status, "errormessage": errormessage}
        database = request["database"]
        (status, errormessage) = DlUtilities.testFileExists(database, 'Error in "database"')
        if not status: return { "status": status, "errormessage": errormessage}

        if "subfolders" in request:
            # Case: folder list supplied
            requestSubfolders = request["subfolders"]
        else:
            # Case: no folder list supplied, get all child folder names
            requestSubfolders = []
            for name in listdir(root):
                childPath = path.join(root, name)
                if  path.isdir(childPath):
                    # case: we have a folder
                    requestSubfolders.append(name)
        
        dataloader.setcsvfieldsizelimit()
        
        istabularonly = request["istabularonly"]
        subfolders = []
        isValidPretest      = True

        for subfolder in requestSubfolders:

            (status, message, errormessage) = dataloader.checkTabularfolderpath(root, subfolder)         
            if not status:
                isValidPretest = status 
                subfolders.append({"childfoldername":subfolder, "preteststatus":status , "errormessage":errormessage, "areasymbols":""})
                continue

            if not istabularonly:
                (status, message, errormessage) = dataloader.checkSpatialfolderpath(root, subfolder)
                if not status:
                    isValidPretest = status 
                    subfolders.append({"childfoldername":subfolder, "preteststatus":status , "errormessage":errormessage, "areasymbols":""})
                    continue

            (status, message, errormessage, areasymbols) = dataloader.getSacatalogData(database, root, subfolder, True)
            if not status:
                isValidPretest = status 
                subfolders.append({"childfoldername":subfolder, "preteststatus":status , "errormessage":errormessage, "areasymbols":areasymbols})
                continue
            

            (status, message, errormessage) = dataloader.checkVersion(database, root, subfolder)
            if not status:
                isValidPretest = status 
                subfolders.append({"childfoldername":subfolder, "preteststatus":status , "errormessage":errormessage, "areasymbols":areasymbols})
                continue

            if not istabularonly:
                IsWSSAOI = False
                ssurgoDownloadRoot = os.path.join(root, subfolder)
                saaoifilename = 'aoi_a_aoi.shp'   #
                saaoifilepath = path.join(ssurgoDownloadRoot, 'spatial', saaoifilename)  #
                (status, errormessage) = DlUtilities.testFileExists(saaoifilepath, f"Error in {saaoifilepath}") #
                IsWSSAoi = status

                areasym = list(areasymbols.keys())[0]

                (status, message, errormessage) = dataloader.checkEmptyShapefiles(database, root, subfolder, IsWSSAoi, areasym)
                if not status: 
                    isValidPretest = status 
                    subfolders.append({"childfoldername":subfolder, "preteststatus":status , "errormessage":errormessage, "areasymbols":areasymbols})
                    continue
  
                (status, message, errormessage) = dataloader.checkEPSGAuthorityCode(database, root, subfolder, IsWSSAoi, areasym)
                if not status:
                    isValidPretest = status 
                    subfolders.append({"childfoldername": subfolder,"preteststatus":status , "errormessage":errormessage,"areasymbols":areasymbols})
                    continue
                subfolders.append({"childfoldername": subfolder,"preteststatus": status , "errormessage":errormessage,"areasymbols":areasymbols})

            else:
                subfolders.append({"childfoldername": subfolder,"preteststatus": status , "errormessage":errormessage,"areasymbols":areasymbols})

        
        # Code logic for cross scanning of duplicate areasymbols using the folders with preteststatus = True 
        filteredSubfolders = [subfolder for subfolder in subfolders if subfolder['preteststatus']]

        for subfolder in filteredSubfolders:
            sharedSSAs = {}
            # cross-overs
            for areasymbol in subfolder['areasymbols']:
                sharedFolders = []
                for otherSubfolder in filteredSubfolders:
                # Don't include our outer folder name in the innermost lists
                    if otherSubfolder['childfoldername'] != subfolder['childfoldername']:
                        if areasymbol in otherSubfolder['areasymbols']:
                            sharedFolders.append(otherSubfolder['childfoldername'])
                if sharedFolders:
                    sharedSSAs[areasymbol]=sharedFolders
                    # Only preserve results if any shared SSAs were found
            if sharedSSAs:
                subfolder['sharedSSAs'] = sharedSSAs
        
        # Code logic to log the pretest errors in all folders in log file
        if not isValidPretest:
            errorSubfolders = [subfolder for subfolder in subfolders if not subfolder['preteststatus']]
            for subfolder in errorSubfolders:
                tlogger.error(subfolder['childfoldername'] + ": " + subfolder['errormessage'])


        response = {
                "allpassed": isValidPretest,
                "status": True,
                "message":"",
                "errormessage": "", 
                "subfolders": subfolders      
            }

        return response

    # def importtabulardatausingpandas(db_file, data_file):
    #     try:
    #         start = time.time()
    #         con = dataloader.create_connection(db_file)
    #         #con.execute("PRAGMA foreign_keys = 1")
    #         ssa = os.path.basename(data_file)
    #         cursor = con.cursor()
    #         cursor.execute('select distinct daglevel from mdstattabs')
    #         rows = cursor.fetchall()

    #         dag = []

    #         for i in rows:
    #             dag.append(i[0])
    #         df = pd.read_sql_query("SELECT daglevel,tabphyname,iefilename,tabletype from mdstattabs where tabletype in ('Tabular in Tabular') ", con)
    #         tb_file_path =  os.path.join(data_file,'tabular')
    #         na_values = ["",
    #                  "#N/A",
    #                  "#N/A N/A",
    #                  "#NA",
    #                  "-1.#IND",
    #                  "-1.#QNAN",
    #                  "-NaN",
    #                  "-nan",
    #                  "1.#IND",
    #                  "1.#QNAN",
    #                  "<NA>",
    #                  #             "N/A",
    #                  #              "NA",
    #                  "NULL",
    #                  "NaN",
    #                  #             "n/a",
    #                  "nan",
    #                  "null"]
            
    #         for i in dag:                 # Loop through the dag levels [0,1,2,3,4,5,6]
    #             df2 = df[(df.daglevel==i) ]
    #             if df2.empty:             # If there is no table in Python dataframe for daglevel i
    #                 continue
    #             else:
    #                 for index, row in df2.iterrows():                                    
    #                     fldNames = []
    #                     queryFieldNames = "SELECT name, type FROM PRAGMA_TABLE_INFO('" + str(row['tabphyname']) + "');"
    #                     cursor.execute(queryFieldNames)
    #                     rows = cursor.fetchall()
    #                     fldInfo= [row for row in rows]
    #                     for fld in fldInfo:
    #                         fldName, fldType = fld
    #                         fldNames.append(fldName)
                            
    #                     f = pd.read_csv(os.path.join(tb_file_path,str(row['iefilename'])+ '.txt'),delimiter = '|',names = fldNames,na_values=na_values,keep_default_na=False,low_memory=False)
    #                     #print('\nPandas Dataframe content\n',f)               
    #                     f.to_sql(str(row['tabphyname']), con, if_exists='append',index=False)
    #                     #print('\nMetadata dag level {} file {} is loaded\n'.format(i,str(row['tabphyname'])))


    #         end = time.time()

    #         print(f"\n WSS tabular SSURGO files are loaded for SSA {ssa}. Runtime of the import program is {end - start}")


    #         if con:
    #             con.close()


    #         return (True,"All tabular files are loaded successfully in db file","")

    #     except sqlite3.Error as error:
    #         return (False,"Error while loading tabular data", str(error.args[0]))

    #     finally:
    #         if con:
    #             con.close()
    
    def importtabulardata(db_file, data_file, IncludeInterpretationSubRules):
        #usage (status, message, errormessage)= dataloader.importtabulardata (database, ssurgoDownloadRoot)
        try:
            (status, tbcon, errormessage) = DlUtilities.create_connection(db_file)
            if not status:
                return  (status, "Error encountered.", errormessage)
            tbcon.execute("PRAGMA foreign_keys = 1")
            cursor = tbcon.cursor()
            cursor.execute("SELECT daglevel,tabphyname,iefilename,tabletype from mdstattabs where tabletype in ('Tabular in Tabular') order by daglevel")
            tblist = cursor.fetchall()

            for rw in tblist:
                curValues = []
                queryFieldNames = "SELECT name FROM PRAGMA_TABLE_INFO('" + str(rw[1])  + "');" 
                cursor.execute(queryFieldNames)   
                rows = cursor.fetchall()
                src = len(rows) * ['?']
                tbfolderpath = os.path.join(data_file,'tabular')
                tbfilename = str(rw[2])+".txt"
                tbfilepath = os.path.join(tbfolderpath,str(rw[2])+".txt")
                (status, errormessage) = DlUtilities.testFileExists(tbfilepath, "Tabular file error")
                if not status: return (False, '', errormessage)
                
                #if str(rw[1]) == 'cointerp':
                #    na_values = ["","NULL","null"]
                #    f = pd.read_csv(tbfilepath,delimiter = '|',header=None, usecols=[0,1,2,3,4,5,6,11,12,15,16,17,18],names = ["cokey", "mrulekey", \
                #        "mrulename","seqnum","rulekey","rulename","ruledepth","interphr","interphrc","nullpropdatabool","defpropdatabool","incpropdatabool", \
                #        "cointerpkey"],na_values=na_values,keep_default_na=False,low_memory=False)
                #    newf = f[f.ruledepth==0]
                #    newf.to_sql(str(rw[1]), tbcon, if_exists='append',index=False)

                with open(tbfilepath,'r',  encoding='UTF-8') as datafile:
                    filerows = csv.reader(datafile, delimiter='|', quotechar='"')
                    if str(rw[1]) == 'cointerp':

                        usecols = [0,1,2,3,4,5,6,11,12,15,16,17,18]
                        src = len(usecols) * ['?']
                        if not IncludeInterpretationSubRules: #Apply ruledepth filter if IncludeInterpretationSubRules is not selected
                            for filerow in filerows:
                                rwlst = []
                                if filerow[6] != '0':  
                                    continue
                                for i,val in enumerate(filerow):
                                    if i in usecols:
                                        if val.strip():
                                            rwlst.append(val.strip())
                                        else:
                                            rwlst.append(None)
                                    else:
                                        continue
                                curValues.append(tuple(rwlst))

                        else:
                            for filerow in filerows:
                                rwlst = []
                                for i,val in enumerate(filerow):
                                    if i in usecols:
                                        if val.strip():
                                            rwlst.append(val.strip())
                                        else:
                                            rwlst.append(None)
                                    else:
                                        continue
                                curValues.append(tuple(rwlst))
                        insertQuery = "INSERT INTO " + str(rw[1]) + " VALUES (" + ",".join(src) + ");"
                        cursor.executemany(insertQuery, curValues)
                        tbcon.commit()


                    else:                                 #Load tables which are not cointerp

                        for filerow in filerows:
                            curValues.append(tuple([val.strip() if val.strip() else None for val in filerow]))
                        insertQuery = "INSERT INTO " + str(rw[1]) + " VALUES (" + ",".join(src) + ");"
                        cursor.executemany(insertQuery, curValues)
                        tbcon.commit()


            (status, response, error) = dataloader.loadSDVtables(data_file, tbcon)
            if not status:
                return (status, response, str(error))

            return (True,"All tabular files are loaded successfully in db file","")
            
        except sqlite3.IntegrityError as e:
            return (False, "", f"Error while loading tabular data of file {tbfilepath}, {str(e.args[0])}") 

        except sqlite3.Error as error:
            return (False, "" ,f"Error while loading tabular data of file {tbfilepath}, {str(error.args[0])}")
        
        except Exception as ex:
            errormessage = f"Error while loading tabular data in function importtabulardata for file {tbfilepath}, Unexcepted error: {format(ex)}"
            tlogger.critical(errormessage)
            tlogger.critical(traceback.format_exc())
            return (False,"", errormessage)

        finally:
            if tbcon:
                tbcon.close()
    

    def createSdvattributeKeyTable(keyTablename, oldTablename, newTablename, conn):
        # Create the key comparison table and populate it.
        # This table simplifies the case definitions for deleting and importing data.
        sqlCreate = f'''create TEMP table temp.{keyTablename} (
            case_name text,
            n_attributekey int,
            n_attributename	text, 
            n_datetime text, 
            o_attributekey	text, 
            o_attributename	text, 
            o_datetime text, 
            o_n_attributekey_for_name text,
            o_n_datetime_for_name text);
        '''
        conn.execute(sqlCreate)
        conn.commit

        # The wlupdated values will be converted to a sortable form by use of 
        # a SQL expression like:
        #   (substr(xxx.wlupdated,7,4)||xxx.wlupdated)
        sqlPopulateKeyTable = f'''
            insert into temp.{keyTablename}
            select distinct 
            N.attributedescription [case_name],
            N.attributekey [n_attributekey], 
            N.attributename [n_attributename], 
            (substr(N.wlupdated,7,4)||N.wlupdated) [n_datetime], 
            O.attributekey [o_attributekey], 
            O.attributename [o_attributename], 
            IFNULL(substr(O.wlupdated,7,4)||O.wlupdated, '') [o_datetime],
            O_N.attributekey [o_n_attributekey_for_name], 
            IFNULL(substr(O_N.wlupdated,7,4)||O_N.wlupdated, '') [o_n_datetime_for_name]
            from {newTablename} [N]
            left join {oldTablename} [O] on N.attributekey = O.attributekey
            left join {oldTablename} [O_N] on N.attributename = O_N.attributename
    '''
        conn.execute(sqlPopulateKeyTable)
        conn.commit

        
    def updateSdvattribute(oldTablename, newTablename, tempDeletionTablename, tempAdditionTablename, conn):
        # Assuming data tables have been populated, apply proposed sdvattribute updates.
        # Data are pulled from the new table  (i.e., sourced from CSV SSURGO data) and merged 
        # into the "old" (i.e., the database table) table.
        # A temporary "key table" is utilized to hold data state for each record.
        # This helps define the relationships needed for some of the cases.

        # Usage:
        #   dataloader.updateSdvattribute(oldTablename, newTablename, 
        #       tempDeletionTablename, tempAdditionTablename, conn)
        # Populates the tempDeletionTablename, tempAdditionTablename tables.

        # Create and populate the key table
        keyTablename = 'temp_sdvattribute_keytable'
        dataloader.createSdvattributeKeyTable(keyTablename, oldTablename, newTablename, conn)

        # A note on naming conventions:
        #   "ak"    attributekey
        #   "an"    attributename
        #   "old"   data in the database sdvattribute table before updating
        #   "new"   data imported from a CSV file
        #   "n_"    pertains to the "new" data table
        #   "o_n_"    pertains to the "old" data table, keys matched on attributename
        #   "o_"    pertains to the "old" data table, keys matched on attributekey

        # Temporary tables are used to hold keys for record deletion and addition.
        # For development and diagnostic purposes, the "useTrueTempTables", if False,
        # forces utilization of permanent tables for later review.

        conn.execute(f'CREATE TEMP TABLE {tempDeletionTablename} (attributekey  INT)')
        conn.commit()
        conn.execute(f'CREATE TEMP TABLE {tempAdditionTablename} (attributekey  INT)')
        conn.commit()

        # Isolate the key values for deletion and addition of records in the database
        sqlDeletionKeys = f'INSERT INTO {tempDeletionTablename} (attributekey) '
        sqlAdditionKeys = f'INSERT INTO {tempAdditionTablename} (attributekey) '
        deletionUnionFragment = ''
        additionUnionFragment = ''

        # case 1: new record
        # where o_attributekey is null and o_n_attributekey_for_name is null 
        #   then (no deletion)
        #   then (add n_attributekey)
        sqlAdditionKeys += f'''
            {additionUnionFragment}
            -- case 1: new record
            SELECT n_attributekey [attributekey] FROM {keyTablename}
            WHERE o_attributekey IS NULL AND o_n_attributekey_for_name IS NULL
        '''
        additionUnionFragment = 'UNION'
        
        # case 2: (old) match ak, match an
        # where o_attributekey is not null and o_n_attributekey_for_name is not null 
        # and o_attributekey = o_n_attributekey_for_name
        # and n_datetime <= o_datetime
        #   then (no deletion)
        #   then (no addition)

        # case 3: (new) match ak, match an
        # where o_attributekey is not null and o_n_attributekey_for_name is not null 
        # and o_attributekey = o_n_attributekey_for_name
        # and n_datetime > o_datetime
        #   then (delete o_attributekey)
        #   then (add n_attributekey)
        sqlDeletionKeys += f'''
            {deletionUnionFragment}
            -- case 3: (new) match ak, match an
            SELECT o_attributekey [attributekey] FROM {keyTablename}
            WHERE o_attributekey IS NOT NULL AND o_n_attributekey_for_name IS NOT NULL
            AND o_attributekey = o_n_attributekey_for_name
            AND  n_datetime > o_datetime
        '''
        deletionUnionFragment = 'UNION'

        sqlAdditionKeys += f'''
            {additionUnionFragment}
            -- case 3: (new) match ak, match an
            SELECT n_attributekey [attributekey] FROM {keyTablename}
            WHERE o_attributekey IS NOT NULL AND o_n_attributekey_for_name IS NOT NULL
            AND o_attributekey = o_n_attributekey_for_name
            AND n_datetime > o_datetime
        '''

        # case 4: (old) match ak, new an
        # where o_attributekey is not null and o_n_attributekey_for_name is null 
        # and n_datetime <= o_datetime
        #   then (no deletion)
        #   then (no addition)    

        # case 5: (new) match ak, new an
        # where o_attributekey is not null and o_n_attributekey_for_name is null 
        # and n_datetime > o_datetime
        #   then (delete o_attributekey)
        #   then (add n_attributekey)
        sqlDeletionKeys += f'''
            {deletionUnionFragment}
            -- case 5: (new) match ak, new an
            SELECT o_attributekey [attributekey] FROM {keyTablename}
            WHERE o_attributekey IS  NOT NULL AND o_n_attributekey_for_name IS NULL
            AND n_datetime > o_datetime
        '''

        sqlAdditionKeys += f'''
            {additionUnionFragment}
            -- case 5: (new) match ak, new an
            SELECT n_attributekey [attributekey] FROM {keyTablename}
            WHERE o_attributekey IS  NOT NULL AND o_n_attributekey_for_name IS NULL
            AND n_datetime > o_datetime
        '''

        # case 6: (old) n_ak not found, an found at different ak
        # where o_attributekey is null and o_n_attributekey_for_name is not null 
        # and n_datetime <= o_n_datetime_for_name
        #   then (no deletion)
        #   then (no addition)  

        # case 7: (new) n_ak not found, an found at different ak
        # where o_attributekey is null and o_n_attributekey_for_name is not null 
        # and n_datetime > o_n_datetime_for_name
        #   then (delete o_n_attributekey_for_name)
        #   then (add n_attributekey)
        sqlDeletionKeys += f'''
            {deletionUnionFragment}
            -- case 7: (new) n_ak not found, an found at different ak
            SELECT o_n_attributekey_for_name [attributekey] FROM {keyTablename}
            WHERE o_attributekey IS NULL AND o_n_attributekey_for_name IS NOT NULL
            AND n_datetime > o_n_datetime_for_name
        '''

        sqlAdditionKeys += f'''
            {additionUnionFragment}
            -- case 7: (new) n_ak not found, an found at different ak
            SELECT n_attributekey [attributekey] FROM {keyTablename}
            WHERE o_attributekey IS NULL AND o_n_attributekey_for_name IS NOT NULL
            AND n_datetime > o_n_datetime_for_name
        '''    

        # case 8: (n_ak < o_ak < o_an) ak found, newer an found
        # where o_attributekey is not null and o_n_attributekey_for_name is not null 
        # and o_attributekey <> o_n_attributekey_for_name
        # and and n_datetime < o_datetime AND o_datetime < o_n_datetime_for_name
        #   then (no deletion)
        #   then (no addition)  

        # case 9: (n_ak < o_an < o_ak) ak found, newer an found
        # where o_attributekey is not null and o_n_attributekey_for_name is not null 
        # and o_attributekey <> o_n_attributekey_for_name
        # and n_datetime < o_n_datetime_for_name AND o_n_datetime_for_name < o_datetime
        #   then (no deletion)
        #   then (no addition)  

        # case 10: (o_ak < n_ak < o_an) ak found, newer an found
        # where o_attributekey is not null and o_n_attributekey_for_name is not null 
        # and o_attributekey <> o_n_attributekey_for_name
        # and o_datetime < n_datetime AND n_datetime < o_n_datetime_for_name
        #   then (delete o_attributekey)
        #   then (no addition) 

        sqlDeletionKeys += f'''
            {deletionUnionFragment}
            -- case 10: (o_ak < n_ak < o_an) ak found, newer an found
            SELECT o_attributekey [attributekey] FROM {keyTablename}
            where o_attributekey is not null and o_n_attributekey_for_name is not null 
            and o_attributekey <> o_n_attributekey_for_name
            and o_datetime < n_datetime AND n_datetime < o_n_datetime_for_name
        '''

        # case 11: (o_an < n_ak <  o_ak) ak found, newer an found
        # where o_attributekey is not null and o_n_attributekey_for_name is not null 
        # and o_attributekey <> o_n_attributekey_for_name
        # and o_n_datetime_for_name <  n_datetime and  n_datetime < o_datetime
        #   then (no deletion)
        #   then (no addition)    

        # case 12: (o_ak < o_an < n_ak) ak found, newer an found
        # where o_attributekey is not null and o_n_attributekey_for_name is not null 
        # and o_attributekey <> o_n_attributekey_for_name
        # and  o_datetime < and o_n_datetime_for_name AND o_n_datetime_for_name < n_datetime
        #   then (delete o_attributekey and o_n_attributekey_for_name)
        #   then (add n_attributekey)
        sqlDeletionKeys += f'''
            {deletionUnionFragment}
            -- case 12: (o_ak < o_an < n_ak) ak found, newer an found
            SELECT o_attributekey [attributekey] FROM {keyTablename}
            where o_attributekey is not null and o_n_attributekey_for_name is not null 
            and o_attributekey <> o_n_attributekey_for_name
            and  o_datetime < o_n_datetime_for_name AND o_n_datetime_for_name < n_datetime
        '''
        sqlDeletionKeys += f'''
            {deletionUnionFragment}
            -- case 12: (o_ak < o_an < n_ak) ak found, newer an found
            SELECT o_n_attributekey_for_name [attributekey] FROM {keyTablename}
            where o_attributekey is not null and o_n_attributekey_for_name is not null 
            and o_attributekey <> o_n_attributekey_for_name
            and  o_datetime < o_n_datetime_for_name AND o_n_datetime_for_name < n_datetime
        '''

        sqlAdditionKeys += f'''
            {additionUnionFragment}
            -- case 12: (o_ak < o_an < n_ak) ak found, newer an found
            SELECT n_attributekey [attributekey] FROM {keyTablename}
            where o_attributekey is not null and o_n_attributekey_for_name is not null 
            and o_attributekey <> o_n_attributekey_for_name
            and  o_datetime < o_n_datetime_for_name AND o_n_datetime_for_name < n_datetime
        '''    

        # case 13: (o_an < o_ak < n_ak) ak found, newer an found
        # where o_attributekey is not null and o_n_attributekey_for_name is not null 
        # and o_attributekey <> o_n_attributekey_for_name
        # and o_n_datetime_for_name < o_datetime AND o_datetime < n_datetime
        #   then (delete o_attributekey and o_n_attributekey_for_name)
        #   then (add n_attributekey)
        sqlDeletionKeys += f'''
            {deletionUnionFragment}
            -- case 13: (o_an < o_ak < n_ak) ak found, newer an found
            SELECT o_attributekey [attributekey] FROM {keyTablename}
            where o_attributekey is not null and o_n_attributekey_for_name is not null 
            and o_attributekey <> o_n_attributekey_for_name
            and o_n_datetime_for_name < o_datetime AND o_datetime < n_datetime
        '''
        sqlDeletionKeys += f'''
            {deletionUnionFragment}
            -- case 13: (o_an < o_ak < n_ak) ak found, newer an found
            SELECT o_n_attributekey_for_name [attributekey] FROM {keyTablename}
            where o_attributekey is not null and o_n_attributekey_for_name is not null 
            and o_attributekey <> o_n_attributekey_for_name
            and o_n_datetime_for_name < o_datetime AND o_datetime < n_datetime
        '''

        sqlAdditionKeys += f'''
            {additionUnionFragment}
            -- case 13: (o_an < o_ak < n_ak) ak found, newer an found
            SELECT n_attributekey [attributekey] FROM {keyTablename}
            where o_attributekey is not null and o_n_attributekey_for_name is not null 
            and o_attributekey <> o_n_attributekey_for_name
            and o_n_datetime_for_name < o_datetime AND o_datetime < n_datetime
        '''    

        # Populate the deletion and addition tables
        conn.execute(sqlDeletionKeys)
        conn.commit()
        conn.execute(sqlAdditionKeys)
        conn.commit()        
        

    def loadSDVtables(data_file, tbcon):

        try:
            cursor = tbcon.cursor()
            cursor.execute("SELECT daglevel,tabphyname,iefilename,tabletype from mdstattabs where tabletype in ('SDV') order by daglevel")
            sdvtblist = cursor.fetchall()
            for rw in sdvtblist:
                sdvtbname = str(rw[1])
                csvfilename = str(rw[2])

                temptbname = f"temp_{sdvtbname}"

                createtmptable = f"CREATE TEMP TABLE temp.{temptbname} AS select * from {sdvtbname} where 1=0;"
                cursor.execute(createtmptable)
                tbcon.commit()

                queryFieldNames = f"SELECT name FROM PRAGMA_TABLE_INFO('{sdvtbname}');" 
                cursor.execute(queryFieldNames)   
                rows = cursor.fetchall()
                curValues = []
                columns = ",".join([ "["+str(row[0])+"]" for row in rows])
                src = len(rows) * ['?']
                tbfolderpath = os.path.join(data_file,'tabular')
                tbfilepath = os.path.join(tbfolderpath,csvfilename+".txt")
                (status, errormessage) = DlUtilities.testFileExists(tbfilepath, "SDV file error")
                if not status: return (False, '', errormessage)

                with open(tbfilepath,'r', encoding='UTF-8') as datafile:
                    filerows = csv.reader(datafile, delimiter='|', quotechar='"')
                    if sdvtbname.lower() == 'sdvattribute':
                        for filerow in filerows:
                            curValues.append(tuple([None if i==7 else val.strip() if val.strip() else None for i,val in enumerate(filerow)]))
                    else:
                        for filerow in filerows:
                            curValues.append(tuple([val.strip() if val.strip() else None for val in filerow]))
                insertQuery = f"INSERT INTO temp.{temptbname} VALUES (" + ",".join(src) + ");"
                cursor.executemany(insertQuery, curValues)
                tbcon.commit()
            
                #iswlupdatedexist = True
                iswlupdatedquery = f"SELECT name FROM PRAGMA_TABLE_INFO('{sdvtbname}') where name = 'wlupdated';"

                cursor.execute(iswlupdatedquery)
                rows = cursor.fetchall()
                # if len(rows) == 0:
                #     iswlupdatedexist = False

                lst = columns.split(",")
                newcolumnslst = ["new."+x for x in lst]
                newcolumns = ",".join (newcolumnslst)

                querypknm = f"SELECT name FROM PRAGMA_TABLE_INFO('{sdvtbname}') where pk=1;"
                cursor.execute(querypknm)
                row = cursor.fetchone()
                pknm = str(row[0])

                # if not iswlupdatedexist:
                #     sqldelete = (f"DELETE FROM {sdvtbname} "
                #     f" WHERE {pknm} IN ( SELECT old.{pknm} FROM {sdvtbname} old" 
                #     f" INNER JOIN temp.{temptbname} new ON new.{pknm} = old.{pknm} );"
                #     )
                #     sqlinsert = (f"INSERT INTO {sdvtbname}"
                #     f" SELECT {newcolumns}"
                #     f" FROM temp.{temptbname} new ;"                    
                #     )
                # elif sdvtbname == 'sdvattribute':
                #     tempDeletionTablename = 'temp_delete_sdvattribute'
                #     tempAdditionTablename = 'temp_add_sdvattribute'
                #     dataloader.updateSdvattribute(sdvtbname, temptbname, tempDeletionTablename, tempAdditionTablename, tbcon)
                #     sqldelete = f'DELETE FROM {sdvtbname} WHERE attributekey IN (SELECT attributekey FROM {tempDeletionTablename})'
                #     sqlinsert = f'INSERT INTO {sdvtbname} select * from {temptbname} WHERE attributekey IN (SELECT attributekey FROM {tempAdditionTablename})'
                # else:
                #     sqldelete = (f"DELETE FROM {sdvtbname} "
                #     f" WHERE {pknm} IN ( SELECT old.{pknm} FROM {sdvtbname} old"
                #     f" INNER JOIN temp.{temptbname} new ON new.{pknm} = old.{pknm}"
                #     f" WHERE substr(new.wlupdated,7,4)||new.wlupdated > IFNULL(substr(old.wlupdated,7,4)||old.wlupdated, ''));"
                #     )
                #     sqlinsert = (f"INSERT INTO {sdvtbname}"
                #     f" SELECT {newcolumns}"
                #     f" FROM temp.{temptbname} new LEFT JOIN {sdvtbname} old ON new.{pknm} = old.{pknm}"
                #     f" WHERE substr(new.wlupdated,7,4)||new.wlupdated > IFNULL(substr(old.wlupdated,7,4)||old.wlupdated, '');"
                #     )    
                sqldelete = False
                sqlupdate = False
                sqlinsert = False

                if sdvtbname == 'sdvalgorithm':
                    # The sdvalgorithm table has no children, therefore we cann delete and import
                    # without worrying about child table constraints.
                    sqldelete = (f"DELETE FROM {sdvtbname} "
                    f" WHERE {pknm} IN ( SELECT old.{pknm} FROM {sdvtbname} old" 
                    f" INNER JOIN temp.{temptbname} new ON new.{pknm} = old.{pknm} );"
                    )
                    sqlinsert = (f"INSERT INTO {sdvtbname}"
                    f" SELECT {newcolumns}"
                    f" FROM temp.{temptbname} new ;"                    
                    )
                elif sdvtbname == 'sdvfolder':
                    # The sdvfolder table has a child table, therefore we can't drop records.
                    # We will rely upon a later houssekeeping step to remove no-longer-needed 
                    # records.
                    sqlinsert = (f"insert into {sdvtbname}" 
                    		f" select * from temp.{temptbname} [new]"
		                    f" where [new].folderkey not in (select folderkey from {sdvtbname})"
                    )
                    sqlupdate = (f"update {sdvtbname}"
                        		f" set foldersequence = new.foldersequence,"
                        		f" foldername = new.foldername,"
                        		f" folderdescription = new.folderdescription,"
                        		f" parentfolderkey = new.parentfolderkey,"
        		                f" wlupdated = new.wlupdated"
		                        f" from temp.{temptbname} [new]"
		                        f" where {sdvtbname}.folderkey = [new].folderkey"
		                        f" and substr([new].wlupdated,7,4)||[new].wlupdated > IFNULL(substr({sdvtbname}.wlupdated,7,4)||{sdvtbname}.wlupdated, '')"
                                )
                elif sdvtbname == 'sdvfolderattribute':
                    # The sdvfolder table has a child table, therefore we can't drop records.
                    # We will rely upon a later houssekeeping step to remove no-longer-needed 
                    # records.                 
                    sqlinsert = (f"insert into {sdvtbname}"   
		                        f" select * from temp.{temptbname} [new]"
                                f" where [new].attributekey not in (select attributekey from {sdvtbname})"
                                )
                elif sdvtbname == 'sdvattribute':
                    # While the sdvattribute table has no childern, it does require evaluation of 
                    # thirteen different record comparison cases. We pass responsibility for defining the 
                    # record keys for deletion and addition off to dataloader.updateSdvattribute(...).
                    tempDeletionTablename = 'temp_delete_sdvattribute'
                    tempAdditionTablename = 'temp_add_sdvattribute'
                    dataloader.updateSdvattribute(sdvtbname, temptbname, tempDeletionTablename, tempAdditionTablename, tbcon)
                    sqldelete = f'DELETE FROM {sdvtbname} WHERE attributekey IN (SELECT attributekey FROM {tempDeletionTablename})'
                    sqlinsert = f'INSERT INTO {sdvtbname} select * from {temptbname} WHERE attributekey IN (SELECT attributekey FROM {tempAdditionTablename})'

                if sqldelete:
                    cursor.execute(sqldelete)
                    tbcon.commit()  
                if sqlupdate:
                    cursor.execute(sqlupdate)
                    tbcon.commit()  
                if sqlinsert:  
                    cursor.execute(sqlinsert)
                    tbcon.commit()

                droptmptable = f"DROP TABLE IF EXISTS temp.{temptbname};"
                cursor.execute(droptmptable)
                tbcon.commit()

            return (True,"SDV tables loaded successfully","")
        
        except sqlite3.IntegrityError as ex:
            return (False, "" , f"Error while loading SDV data of file {tbfilepath}, {format(ex)}")

        except sqlite3.Error as ex:
            return (False, "", f"Error while loading SDV data of file {tbfilepath}, {format(ex)}")

        except Exception as ex:
            errormessage = f"Error while loading SDV data in function loadSDVtables for file {tbfilepath}, Unexcepted error: {format(ex)}"
            tlogger.critical(errormessage)
            tlogger.critical(traceback.format_exc())
            return (False,"", errormessage)
     
       
    def importtabularinspatialdata(db_file, data_file, IsWSSAoi, ssa):
        # Usage: (status, message, errormessage) = importtabularinspatialdata(db_file, data_file, ssa)
        try:
            (status, tbcon, errormessage) = DlUtilities.create_connection(db_file)
            if not status: return  (status, "", errormessage)
            cursor = tbcon.cursor()
            cursor.execute("SELECT daglevel,tabphyname,iefilename,iefilenameaoi,tabletype from mdstattabs where tabletype in ('Tabular in Spatial') order by daglevel")
            tblist = cursor.fetchall()

            for rw in tblist:
                curValues = []
                queryFieldNames = "SELECT name FROM PRAGMA_TABLE_INFO('" + str(rw[1])  + "');" 
                cursor.execute(queryFieldNames)   
                rows = cursor.fetchall()
                src = len(rows) * ['?']
                tbinspfolderpath = os.path.join(data_file,'spatial')
                if not IsWSSAoi:
                    tbspfilename = str(rw[2]) + "_" + ssa.lower()  + ".txt"
                else:
                    tbspfilename = str(rw[3]) + ".txt"
                tbinspfilepath = path.join(tbinspfolderpath, tbspfilename)
                (status, errormessage) = DlUtilities.testFileExists(tbinspfilepath, "Tabular/Spatial file error")
                if not status: return (status, '', errormessage)

                with open(tbinspfilepath,'r',  encoding='UTF-8') as datafile:
                    filerows = csv.reader(datafile, delimiter='|', quotechar='"')
                    for filerow in filerows:
                        curValues.append(tuple([val.strip() if val.strip() else None for val in filerow]))
                insertQuery = "INSERT INTO " + str(rw[1]) + " VALUES (" + ",".join(src) + ");"
                cursor.executemany(insertQuery, curValues)
                tbcon.commit()

            return (True,f"All tabular in spatial files in folder {tbinspfolderpath} are loaded successfully in db file","")

        except sqlite3.Error as error:
            return (False,'', f"Error while loading tabular in spatial data: {format(error)}")

        except Exception as ex:
            errormessage = f"Error while executing importtabularinspatialdata for folder {tbinspfolderpath}, Unexcepted error: {format(ex)}"
            tlogger.critical(errormessage)
            tlogger.critical(traceback.format_exc())
            return (False,"", errormessage)

        finally:
            if tbcon:
                tbcon.close()
  

    def isGeopackage(db_path):
        # Determine whether the SQLite file is GeoPackage or not.
        # We only test whetehr the database is GeoPackage. There's no equivalent 
        # test for SpatiaLite, short of looking for existence of specific
        # tables that are unique to GeoPackage or SpatiaLite.
        # Parameter:
        #   db_path     Path to the SQLite database to be tested.
        # References:
        #  GeoPackage Encoding Standard (OGC) Format Family
        #  https://www.loc.gov/preservation/digital/formats/fdd/fdd000520.shtml
        #	Magic numbers	Hex: 47 50 4B 47
        #	ASCII: GKPG
        #	In the application_id field (byte offset 68) of the SQLite database header. 
        #	Specific to GeoPackage files. Applies to Version 1.2 and greater Version 
        #	1.0 has value "GP10". Version 1.1 has value "GP11".
        #  PRAGMA Statements
        #  https://www.sqlite.org/pragma.html#pragma_application_id
        #	PRAGMA schema.application_id;
        #	PRAGMA schema.application_id = integer ;
        #	The application_id PRAGMA is used to query or set the 32-bit signed 
        #	big-endian "Application ID" integer located at offset 68 ...
        # Usage: (status, isGeopackageTrue, errormessage) = isGeopackage(db_path)

        # Checking of several SpatiaLite files shows an identifier of four null bytes.
        # For GeoPackage, geopackage decimal: 1196444487 / hex  0x47504b47   'GPKG'
        try:
            geopackage_identifier = 1196444487
            sql = 'PRAGMA application_id;' 

            isGeopackageTrue = None
            (status, conn, errormessage) = DlUtilities.create_connection(db_path)
            if not status:
                return (status, isGeopackageTrue, errormessage)

            cur = conn.cursor()
            cur.execute(sql)
            identifier = (cur.fetchone())[0]
            isGeopackageTrue = identifier == geopackage_identifier
            return (True, isGeopackageTrue, "")
        except Exception as ex:
            errormessage = f"Error while executing function isGeopackage, Unexcepted error: {format(ex)}"
            tlogger.critical(errormessage)
            tlogger.critical(traceback.format_exc())
            return (False, isGeopackageTrue, errormessage)
    

    def getSqlString(db_path, tablename, shapefile_name, dissolvemupolygon):
        # Get SQL string for use with gdal.VectorTranslate method.
        # Usage: (status, loadSql, errormessage)
        try:

            (status, conn, errormessage) = DlUtilities.create_connection(db_path)
            if not status:
                return (status, None, errormessage)

        # Database safety: the mupolygon table must support multipolygon
        # data for dissolve to succeed. If the type is not multipolygon then 
        # the dissolve setting will be ignored.

            if (dissolvemupolygon and tablename == "mupolygon"):
                columnTypeSql = "SELECT type FROM PRAGMA_TABLE_INFO('mupolygon') where name = 'shape';"
                curColumnType = conn.cursor()
                curColumnType.execute(columnTypeSql)
                rows = curColumnType.fetchall()
                columnType =  rows[0][0]
                curColumnType.close()
                if columnType == 'MULTIPOLYGON':
                    name = f'VectorTranslate_SQL_{tablename}_dissolve'  
                else:
                    name = f'VectorTranslate_SQL_{tablename}'
            elif shapefile_name == 'aoi_a_aoi':
                name = f'VectorTranslate_SQL_{tablename}_aoi'
            else:
                name = f'VectorTranslate_SQL_{tablename}'

            infoSql = f"SELECT value FROM systemtemplateinformation WHERE name='{name}';"

            cur = conn.cursor()
            cur.execute(infoSql)
            rows = cur.fetchall()

            loadSql = rows[0][0].replace('__shapename__', shapefile_name)
            
            cur.close()
            conn.close()

            return (True, loadSql, "")

        except Exception as ex:
            errormessage = f"Error while executing function getSqlString, Unexcepted error: {format(ex)}"
            tlogger.critical(errormessage)
            tlogger.critical(traceback.format_exc())
            return (False, "", errormessage)  


    def loadShapefileData(tablename, shapefilefolder, shapefileName,  database, db_format, dissolvemupolygon):
        # Returns (status, message, errormessage)
        try:
            shapefilePath = path.join(shapefilefolder, shapefileName + '.shp')
            (status, loadSql, errormessage) = dataloader.getSqlString(database, tablename, shapefileName, dissolvemupolygon)
            if not status:
                return (False, "Unable to open database.", errormessage)    
        except Exception as ex:
            return (False, "Error during spatial import", f"Error retrieving SQL query command, Unexcepted error: {format(ex)}")

        try: 

            gdal.UseExceptions()
            if shapefileName == 'aoi_a_aoi':           #This is to import WSS AOI sapolygon shape file
                subfolderpath = os.path.dirname(shapefilefolder)
                root = os.path.dirname(subfolderpath)
                subfolder = os.path.basename(subfolderpath)
                (status, message, errormessage, areasymbols) = dataloader.getSacatalogData(database, root, subfolder, False)
                if not status:
                    return (False, f"Error importing the shapefile {shapefileName}", "")
                areasymfilter = tuple(areasymbols)
                if len(areasymfilter) ==1:
                    areasymfilter = "('"+str(areasymfilter[0])+"')"

                loadSql = loadSql.replace('__areasymbols__', str(areasymfilter))

                gdal.VectorTranslate(database, database, SQLStatement = loadSql, 
                        SQLDialect = "INDIRECT_SQLITE", format=f'{db_format}', 
                        accessMode='append', layerName=tablename)

            else:
                gdal.VectorTranslate(database, shapefilePath, SQLStatement = loadSql, 
                        SQLDialect = "SQLite", format=f'{db_format}', 
                        accessMode='append', layerName=tablename)
            return (True, f"shapefile {shapefileName} imported", "")
        except Exception as ex:

            return (False, "", f"Error reading shapefile {shapefileName}, Unexcepted error: {format(ex)}")


    def loadAllShapefiles(childRequest):
        # load all shapefiles, assume WSS format for spatial folder
        #print(f'ssurgoDownloadRoot: {ssurgoDownloadRoot}')
        # Usage: (status, message, errormessage, allimported) =  loadAllShapefiles(childRequest)
        try:
            db_path = childRequest["database"]
            shapefileFolder = childRequest["shapefilepath"]
            dissolvemupolygon= childRequest["dissolvemupolygon"]
            shapefiles = childRequest["shapefiles"] 
            #print(f'areasymbol: {areasymbol}')

            (status, isGeopackageTrue, errormessage) = dataloader.isGeopackage(db_path)
            if not status:
                (status, "Unable to connect to database.", errormessage, False)
            elif isGeopackageTrue:
                db_format = 'GPKG'
            else:   
                db_format = 'SQLite'

            #(status, conn, errormessage) = DlUtilities.create_connection(db_path)
            #if not status:
            #    return  (status, "Error encountered.", errormessage, False)
            #cursor = conn.cursor()        
            #cursor.execute("SELECT daglevel,tabphyname,iefilename,tabletype from mdstattabs where tabletype in ('Spatial') order by daglevel")
            #tblist = cursor.fetchall()
        
            #conn.close()

            for tablename in shapefiles.keys():
                shapefileName = shapefiles[tablename]
                (status, message, errormessage)=dataloader.loadShapefileData(tablename, shapefileFolder, shapefileName, db_path, db_format, dissolvemupolygon)
                if not status:
                    return (status, "Error loading spatial data", errormessage, False)

            return (status, "", "", True)
        
        except Exception as ex:
            errormessage = f"Error while executing function loadAllShapefiles, Unexcepted error: {format(ex)}"
            tlogger.critical(errormessage)
            tlogger.critical(traceback.format_exc())
            return (False, "", errormessage, False)
    

    def initiateSpatialDataImport(loadspatialdatawithinsubprocess, ssurgoDownloadRoot, IsWSSAoi, areasym, database, requestSubfolder, dissolvemupolygon):
        # Usage:
        #   (status, message, errormessage, allimported) = 
        #       dataloader.initiateSpatialDataImport 
        #           (loadspatialdatawithinsubprocess, ssurgoDownloadRoot, areasym, database, requestSubfolder, dissolvemupolygon)

        try:
            shapefiles = {}
            (status, conn, errormessage) = DlUtilities.create_connection(database)
            if not status:
                return  (status, "Error encountered.", errormessage, False)
            cursor = conn.cursor()
            updtsapdag  = "update mdstattabs set daglevel = ((select daglevel from mdstattabs where tabphyname = 'mupolygon')+1) WHERE tabphyname = 'sapolygon' ;"       
            cursor.execute(updtsapdag)
            conn.commit()
            cursor.execute("SELECT tabphyname,iefilename, iefilenameaoi from mdstattabs where tabletype in ('Spatial') order by daglevel")
            tblist = cursor.fetchall()
            conn.close()

            if not IsWSSAoi:
                for rw in tblist:
                    sptbname  = str(rw[0])
                    spfilename= str(rw[1]) + "_" + areasym.lower()
                    shapefiles[sptbname] = spfilename
            else:

                for rw in tblist:
                    sptbname  = str(rw[0])
                    spfilename= str(rw[2])
                    shapefiles[sptbname] = spfilename

            shapefilepath = path.join(ssurgoDownloadRoot, 'spatial')

            childRequest = {
                "request": "importspatialdata",
                "database": database,
                "shapefilepath": shapefilepath,
                "dissolvemupolygon": dissolvemupolygon,
                "shapefiles": shapefiles,
                "verbose":True
            }

            (status, response, error) = dataloader.importtabularinspatialdata(database, ssurgoDownloadRoot, IsWSSAoi, areasym)
            if not status:
                return(status, response, error, False)
            #(status, response) = dataloader.loadAllShapefiles(ssurgoDownloadRoot, db_path, db_format, ssa)
            if loadspatialdatawithinsubprocess:
                # case: use a child process to load
                # Form the command vector and push in the request via stdin
                cmd = [
                    sys.argv[0],    # Path to the Python script
                    '@'             # Input should come from the STDIN channel    
                ]
                showVerboseMessage = True
                requestString = json.dumps(childRequest)
                (status, message) = RunChild.runSub(cmd, showVerboseMessage, stdinString=requestString)

                if status:
                    return  (status, message, "", True)
                else:
                    return  (status, "Error encountered.", message, False)
            else:
                # case: load in the current process
                (status, message, errormessage, allimported) = \
                    dataloader.loadAllShapefiles(childRequest)
                return (status, message, errormessage, allimported)
        
        except sqlite3.Error as error:
            return (False, "", 
                f"Error while executing function initiateSpatialDataImport for folder {requestSubfolder}, Unexcepted error: {format(error)}",
                False)
        
        except Exception as ex:
            errormessage = f"Error while executing function initiateSpatialDataImport for folder {requestSubfolder}, Unexcepted error: {format(ex)}"
            tlogger.critical(errormessage)
            tlogger.critical(traceback.format_exc())
            return (False, "", errormessage, False)


    def importspatialdata(request):
        (status, message, errormessage, allimported) = dataloader.loadAllShapefiles(request)  
        response = {
            "status": status,
            "message": message,
            "errormessage": errormessage,
            "allimported":allimported
        }
        return response    
    

    def getDistanceSquared(x, y, originX, originY):
        # Return the cartesian distance-squared of (x,y) from an origin.
        # Used for ordering surevey area centroids
        distanceSquared = pow(x - originX, 2) + pow(y - originY, 2)
        return distanceSquared


    def getChildDistanceSquaredAndMbr(database,root,subfolder,IsWSSAoi, ssaName):
        # Return the distanceSquared and MBR of the survey area's centroid from the sapolygon shapefile.
        # Usage: (status,errormessage,distanceSquared, minX, maxX, minY, maxY) = dataloader.getChildDistanceSquaredAndMbr(request["root"], originalSubfolder, areasym)
        try:
            #filename = f'soilsa_a_{ssaName}.shp'
            (status, tbcon, errormessage) = DlUtilities.create_connection(database)
            if not status:
                return  (None, None, None, None, None, None, None)
            cursor = tbcon.cursor()
            cursor.execute( "SELECT iefilename,iefilenameaoi from mdstattabs where tabphyname in ('sapolygon')" )
            tblist = cursor.fetchall()
            driver = ogr.GetDriverByName('ESRI Shapefile')
            distanceSquared = 0
            for rw in tblist:
                if not IsWSSAoi:
                    spfilename = str(rw[0]) + "_" + ssaName.lower() + ".shp"
                else:
                    spfilename = str(rw[1]) + ".shp"
                shapefilepath = path.join(root, subfolder, "spatial", spfilename)
                if not os.path.isfile(shapefilepath):
                    return (None, None, None, None, None)
                dataSource = driver.Open(shapefilepath, 0)
                layer = dataSource.GetLayer()
                originX = -180
                originY = 90

                compositeEnvelope = []
                # The envelope is a 4-tuple: (minX, maxX, minY, maxY)
                for feature in layer:
                    geom = feature.GetGeometryRef()
                    envelope = list(geom.GetEnvelope())
                    #compositeEnvelope.add(geom.GetEnvelope())
                    if not compositeEnvelope: 
                       compositeEnvelope = envelope
                    else:
                        compositeEnvelope[0] = min(compositeEnvelope[0], envelope[0])
                        compositeEnvelope[1] = max(compositeEnvelope[1], envelope[1])
                        compositeEnvelope[2] = min(compositeEnvelope[2], envelope[2])
                        compositeEnvelope[3] = max(compositeEnvelope[3], envelope[3])
                averageX = (compositeEnvelope[0] + compositeEnvelope[1]) / 2
                averageY = (compositeEnvelope[2] + compositeEnvelope[3]) / 2                
                distanceSquared = dataloader.getDistanceSquared(averageX, averageY, originX, originY)               

            return (True,"",distanceSquared, compositeEnvelope[0], compositeEnvelope[1], compositeEnvelope[2], compositeEnvelope[3])
        
        except Exception as ex:
            errormessage = f"Error while executing getChildDistanceSquaredAndMbr function in {subfolder}, Unexcepted error: {format(ex)}"
            tlogger.critical(errormessage)
            tlogger.critical(traceback.format_exc())
            return (False,errormessage,None, None, None, None, None)


    def getSpatialSummary(request, getMbr, cdict):
        # Given the request with a list of subfolders, 
        # returns a subfolder list (cloned from the request)
        # with distance-squared from a NW origin and MBR for each.
        # We don't do much of this if istabularonly is true
        # or if loadinspatialorder is false.
        # Note: WSS SSA is assumed
        # Usage: (status, errormessage, sortedSubfolders, minXaggregated, maxXaggregated, minYaggregated, maxYaggregated) = (request, getMbr, cdict)
        # Note that if a new list is not required the old list is preserved.

        istabularonly = request["istabularonly"]
        if "loadinspatialorder" in request:
            performSort = request["loadinspatialorder"]
        else:
            performSort = True      
            
        database = request["database"]
        root = request["root"]

        # Short circuit: if no spatial data are involved, return the 
        # folder list as-is.
        # Additionally, if an MBR is not needed and sort order is not required,
        # we can also return early
        if istabularonly or (not getMbr and not performSort):
            return (True, "", request["subfolders"], None, None, None, None)
        
        # We are dealing with spatial data and either MBR or sorting 
        # is required.
        # The sort order will be represented by a list of 
        # the square of the distance from a northwest origin to the 
        # centroid of each sapolygon.
        isFirst = True
        distancesSquared = []
        for originalSubfolder in request["subfolders"]:
            # As required we'll accumulate an aggregated mBR and 
            # a vector of squared distances.
            areasymbols = cdict[originalSubfolder]

            IsWSSAoi = False
            saaoifilename = 'aoi_a_aoi.shp'   #
            saaoifilepath = path.join(root, originalSubfolder, 'spatial', saaoifilename)  #
            
            (status, errormessage) = DlUtilities.testFileExists(saaoifilepath, f"Error in {saaoifilepath}") #
            IsWSSAoi = status   #

            areasym   = list(areasymbols.keys())[0]

            if isFirst:
                (status, errormessage, distanceSquared, minXaggregated, maxXaggregated, minYaggregated, maxYaggregated) = \
                    dataloader.getChildDistanceSquaredAndMbr(database,root,originalSubfolder, IsWSSAoi, areasym)
                if not status:
                    return (False, errormessage, None, None, None, None, None) 

                distancesSquared.append(distanceSquared)
                isFirst = False
            else:
                (status, errormessage, distanceSquared, minX, maxX, minY, maxY) = \
                    dataloader.getChildDistanceSquaredAndMbr(database,root,originalSubfolder, IsWSSAoi, areasym)
                if not status:
                    return (False, errormessage, None, None, None, None, None) 

                distancesSquared.append(distanceSquared)
                if getMbr:
                    minXaggregated = min(minXaggregated, minX)
                    maxXaggregated = max(maxXaggregated, maxX)
                    minYaggregated = min(minYaggregated, minY)
                    maxYaggregated = max(maxYaggregated, maxY)

        if performSort:
            # Return a new sorted list if required.
            # The MBR values can be ignored.
            sortedFolders = [i for _,i in sorted(zip(distancesSquared,request["subfolders"]))]
            return (True, "", sortedFolders, minXaggregated, maxXaggregated, minYaggregated, maxYaggregated)    
        else:
            # Only the MBR is required, return the original list,
            return (True, "", request["subfolders"], minXaggregated, maxXaggregated, minYaggregated, maxYaggregated)
    

    def updateGeopackageMbr(database, minXaggregated, maxXaggregated, minYaggregated, maxYaggregated):
        # Given a GeoPackage and not a tabular-only import,
        # update the MBR for all tables in the database.
        # Usage: (status, errormessage) = (updateGeopackageMbr...)

        # Use the stored sapolygon's max_y < 180 as a proxy for an initialized database.
        # We only want one row.
        checkSql = \
            "select min_x, min_y, max_x, max_y " \
            + "from gpkg_contents where table_name = 'sapolygon';"
        (status, conn, errormessage) = DlUtilities.create_connection(database)
        if not status:
            return (status, errormessage)
        cur = conn.cursor()
        cur.execute(checkSql)
        (min_x, min_y, max_x, max_y) = cur.fetchall()[0]

        updateSql = "update gpkg_contents set min_x=?, min_y=?, max_x=?, max_y=?;"
            
        initializedSql = "select exists (select 1 from sapolygon) as 'isinitialized'"        
        cur = conn.cursor()
        cur.execute(initializedSql)
        isinitialized= cur.fetchone()
        isinitialized = bool(isinitialized[0])
        if isinitialized:
            # Case: initialized database, determine updated values
            min_x = min(min_x, minXaggregated)
            min_y = min(min_y, minYaggregated)
            max_x = max(max_x, maxXaggregated)
            max_y = max(max_y, maxYaggregated)           
        else:
            # Case: initialized database, replace all values
            min_x = minXaggregated
            min_y = minYaggregated
            max_x = maxXaggregated
            max_y = maxYaggregated

        cur.execute(updateSql, (min_x, min_y, max_x, max_y))
        conn.commit()
        conn.close()

        return (True, "")


    def importCandidates(request):
        # Use case 5b request: importCandidates
        # Use case 5: "Import one or more SSAs into an ET from a set of subfolders 
        # that I choose under a containing folder that I specify."
        # Import one or more SSAs into a SSURGO SQLite database from a set of
        # subfolders that I choose under a root folder.

        #response = {"status":True, "allimported": False, "message":"", "errormessage":"", "subfolders":[]}
        root = request["root"]
        (status, errormessage) = DlUtilities.testFolderExists(root, 'Error in "root"')
        if not status: return { "status": status, "errormessage": errormessage}
        database = request["database"]
        (status, errormessage) = DlUtilities.testFileExists(database, 'Error in "database"')
        if not status: return { "status": status, "errormessage": errormessage}

        requestSubfolders = request["subfolders"]

        istabularonly = request["istabularonly"]
        skippretest = request["skippretest"]

        if "includeinterpretationsubrules" in request:
            IncludeInterpretationSubRules = request["includeinterpretationsubrules"]
        else:
            IncludeInterpretationSubRules = False
        
        subfolders = []
        cdict = {}
        
        dataloader.setcsvfieldsizelimit()

        if skippretest:     #skippretest is always True when DP sends the rqeuest. It could be True\False in case of DL
            for subfolder in requestSubfolders:
                (status, message, errormessage, areasymbols) = dataloader.getSacatalogData(database, root, subfolder, False)
                if status:          
                    cdict[subfolder] = areasymbols
                else:
                    subfolders.append({"childfoldername": subfolder, "elapsedsecondstabularimport":0, "elapsedsecondsspatialimport":0,"areasymbols":areasymbols})
                    response = {
                        "allimported":status,
                        "status":status,
                        "message": message,
                        "errormessage":errormessage,
                        "subfolders": subfolder
                        }
                    return response

        else:
            pretestresponse = dataloader.pretestImportCandidates(request)
            if not pretestresponse["allpassed"]:
                return pretestresponse
            else:
                for children in pretestresponse["subfolders"]:
                    cdict[children["childfoldername"]] = children["areasymbols"]

        
        # Do we perform the mupolygon dissolve on mukey value?
        dissolvemupolygon               = request["dissolvemupolygon"]
        loadspatialdatawithinsubprocess = request["loadspatialdatawithinsubprocess"]
        # SORT POINT - if needed, reorder subfolders by spatial ordering
        # before iterating through them.
        # We also have an MBR that can be used to update a GeoPackage
        (status, isGeopackageTrue, errormessage) = dataloader.isGeopackage(database)
        
        if not status:
            response["message"] = "Unable to connect to database."
            response["errormessage"] = errormessage
            response["status"] = False
            return response
        
        getMbr = (isGeopackageTrue and not istabularonly)
        (status, errormessage, sortedSubfolders, minXaggregated, maxXaggregated, minYaggregated, maxYaggregated) = \
            dataloader.getSpatialSummary(request, getMbr, cdict)
        if not status:
            response["errormessage"] = errormessage
            response["status"] = False
            return response
        if getMbr:
            dataloader.updateGeopackageMbr(database, minXaggregated, maxXaggregated, minYaggregated, maxYaggregated)

    
        # Import candidates into specified database
        subfolders = []

        for requestSubfolder in sortedSubfolders:

            time_elapsed_tabular=0
            time_elapsed_spatial=0

            tlogger.debug(f'Starting import of subfolder {requestSubfolder}')

            (status, message, errormessage, areasymbols) = dataloader.getSacatalogData(database, root, requestSubfolder, False)
            if not status:
                subfolders.append({"childfoldername": requestSubfolder,"elapsedsecondstabularimport": time_elapsed_tabular , "elapsedsecondsspatialimport":time_elapsed_spatial, "errormessage":errormessage, "areasymbols":areasymbols})
                response = {
                    "allimported":status,
                    "status": status,
                    "message":message,
                    "errormessage": errormessage,                  
                    "subfolders": subfolders
                    }
                return response 
            else:
                (status, connection, errormessage) = DlUtilities.create_connection(database)
                if not status:
                    subfolders.append({"childfoldername": requestSubfolder,"elapsedsecondstabularimport": time_elapsed_tabular , "elapsedsecondsspatialimport":time_elapsed_spatial, "errormessage":errormessage, "areasymbols":areasymbols})
                    response = {
                        "allimported":status,
                        "status": status,
                        "message":message,
                        "errormessage": errormessage,        
                        "subfolders": subfolders
                        }
                    if connection: connection.close()
                    return response 
                for areasymbol in areasymbols:
                    (status, message, errormessage) = DlUtilities.deleteAreasymbol(database, areasymbol, connection)
                    if not status:
                        response = {
                            "allimported":status,
                            "status": status,
                            "message":message,
                            "errormessage": errormessage,                  
                            "subfolders": subfolders
                            }
                        if connection: connection.close()
                        return response
                if connection: connection.close()

            ssurgoDownloadRoot = os.path.join(root, requestSubfolder) 
            IsWSSAoi = False
            saaoifilename = 'aoi_a_aoi.shp'   #
            saaoifilepath = path.join(ssurgoDownloadRoot, 'spatial', saaoifilename)  #
            
            (status, errormessage) = DlUtilities.testFileExists(saaoifilepath, f"Error in {saaoifilepath}") #
            IsWSSAoi = status   #
        
            areasym = list(areasymbols.keys())[0]       #

            start_time_tabular = time.time()
            (status, message, errormessage)= dataloader.importtabulardata (database, ssurgoDownloadRoot, IncludeInterpretationSubRules)
            end_time_tabular = time.time()
            time_elapsed_tabular = round(end_time_tabular - start_time_tabular)
 
            #(status, message, error)= dataloader.importtabulardatausingpandas (database, ssurgoDownloadRoot)

            if not status:
                subfolders.append({"childfoldername": requestSubfolder,"elapsedsecondstabularimport": time_elapsed_tabular , "elapsedsecondsspatialimport":time_elapsed_spatial, "errormessage":errormessage, "areasymbols":areasymbols})

                message = "Tabular import failed. Please check errormessage"
                response = {
                    "allimported":status,
                    "status": status,
                    "message":message,
                    "errormessage": errormessage,                  
                    "subfolders": subfolders
                }
                return response  

            if not istabularonly:
                start_time_spatial = time.time()
                #(status, message, errormessage) = dataloader.importspatialdata (database, ssurgoDownloadRoot, areasym, loadspatialdatawithinsubprocess, dissolvemupolygon)
                (status, message, errormessage, allimporrted) = \
                    dataloader.initiateSpatialDataImport (loadspatialdatawithinsubprocess, ssurgoDownloadRoot, IsWSSAoi, areasym, database, requestSubfolder, dissolvemupolygon)
                end_time_spatial = time.time()
                time_elapsed_spatial = round(end_time_spatial - start_time_spatial)
                
                if not status:
                    subfolders.append({"childfoldername": requestSubfolder,"elapsedsecondstabularimport": time_elapsed_tabular , "elapsedsecondsspatialimport":time_elapsed_spatial, "errormessage":errormessage, "areasymbols":areasymbols})

                    message = "Spatial import failed. Please check errormessage"
                    response = {
                        "allimported":status,
                        "status": status,
                        "message":message,
                        "errormessage": errormessage,                  
                        "subfolders": subfolders
                    }
                    return response 
            
            subfolders.append({"childfoldername": requestSubfolder,"elapsedsecondstabularimport": time_elapsed_tabular , "elapsedsecondsspatialimport":time_elapsed_spatial, "errormessage":errormessage, "areasymbols":areasymbols})

        # We have finished iterating through the import folders.
        # We need to perform housekeeping and remove sdvfolderattribute and sdvfolder records.
        # Remove parent table records 
        (status, connection, errormessage) = DlUtilities.create_connection(database)
        if not status:
            response = {
                "allimported":False,
                "status": status,
                "message":message,
                "errormessage": errormessage,        
                "subfolders": subfolders
                }
            if connection: connection.close()
            return response                 
        else:
            sqlRemoveFArecords = 'DELETE FROM sdvfolderattribute WHERE attributekey NOT IN (SELECT attributekey FROM sdvattribute)'
            connection.execute(sqlRemoveFArecords)
            connection.commit()
            sqlRemoveFrecords = 'DELETE FROM sdvfolder WHERE folderkey NOT IN (SELECT folderkey FROM sdvfolderattribute)'
            connection.execute(sqlRemoveFrecords)
            connection.commit()
            connection.close()
            tlogger.debug('SDV* housekeeping: finished')
    
        response = {
                "allimported":True,
                "status": True,
                "message":"SSURGO data import succeeded",
                "errormessage":"",                  
                "subfolders":subfolders
                }   

        return response






