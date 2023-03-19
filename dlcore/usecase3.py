# usecase3.py
# Use case 3: View all loaded soil data (“Soil Survey Areas” (SSA), with “areasymbol”) within an ET.

import sqlite3

from dlcore.dlutilities import DlUtilities

class UseCase3:
    def getDatabaseInventory(request):
        # Use case 3 request: getDatabaseInventory
        # Use case 3: 'View all loaded soil data (“Soil Survey Areas” (SSA), with 
        # “areasymbol”) within an ET.'
        # List survey areas and related data within a SQLite database.
        # Use "<script> ?getdatabaseinventory" to retrieve schemas with request and response fields.
        database = request["database"]
        if "wheretext" in request:
            wheretext = request["wheretext"]
        else:
            wheretext = False

        (status, conn, errormessage) = DlUtilities.create_connection(database)
        if not status:
            response = {"status": False, "message" : f"Error connecting to database {database}", "errormessage": errormessage}
            return response

        sql = \
            'SELECT c.areasymbol, c.areaname, c.saverest, ' \
                + 'CASE WHEN p.areasymbol ISNULL THEN 1 ELSE 0 END [istabularonly] ' \
                + 'FROM sacatalog [c] LEFT JOIN sapolygon [p] on c.areasymbol = p.areasymbol '
        if wheretext:
            sql += ' where ' + wheretext + ';'

        try:
            cur = conn.cursor()
            cur.execute(sql)
            rows = cur.fetchall()

            records = {}
            for row in rows:
                records[row[0]] = {"areaname": row[1], "saverest": row[2], "istabularonly": row[3] == 1}

            cur.close()
            conn.close()

            response = {"status": True, "message" : f"Data read from database {database}", "errormessage": "", "records": records}
            return response
        except Exception as ex:
            response = {"status": True, "message" : f"Error reading from database {database}", "errormessage": format(ex)}

            return response
