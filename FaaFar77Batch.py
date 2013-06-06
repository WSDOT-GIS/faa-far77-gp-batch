"""Runs the FAA FAR 77 tool for each runway feature in a z-enabled polyline feature class.

:See http://resources.arcgis.com/en/help/main/10.1/#/FAA_FAR_77/010m0000000z000000/

Parameters
==========
1. Geodatabase path. Defaults to "FAA_Airports.gdb".
2. Runway Centerlines feature class. Defaults to 'RunwayCenterlinesForSurfacesWithZ_NewElevations'.
3. Output Surface feature class. Defaults to 'ObstructionIdSurface'.
4. Approach Types table. Defaults to "ApproachTypeCode".

Required Licenses
=================
* ArcGIS for Desktop Standard (nee ArcEditor)
* Aeronautical Solution Extention

Sample::
    python FaaFar77Batch.py "c:\path\to\db\FAA_Airports.gdb" "RunwayCenterlinesForSurfacesWithZ_NewElevations" "ObstructionIdSurface" "ApproachTypeCode"
"""

import sys, os, datetime

print "Checking out license..."
try:
    import arceditor
except RuntimeError as e:
    print "ArcGIS for Desktop Standard (nee ArcEditor) license not available."
    try:
        import arcinfo
    except RuntimeError:
        msg = "ArcInfo license not available. Cannot continue."
        print msg
        sys.exit(msg)
    else:
        print "Successfully checked out ArcGIS for Desktop Advanced (nee ArcInfo) license"
else:
    print "Successfully checked out ArcGIS for Desktop Standard (nee ArcEditor) license"


print "Importing arcpy..."
import arcpy, arcpy.da
print "Finished importing arcpy."

starttime = datetime.datetime.now()
print "Started at %s..." % starttime

# Ensure the Aeronautical extension is available. Exit if it is not.
availability = arcpy.CheckExtension("Aeronautical")
if availability != "Available":
    sys.exit('"Aeronautical" extension unavailable: %s' % availability)

try:
    arcpy.CheckOutExtension("Aeronautical")
    workspace = "FAA_Airports.gdb"
    runwayCenterlinesFC = 'RunwayCenterlinesForSurfacesWithZ_NewElevations'
    surfaceFC = 'ObstructionIdSurface'
    approachTypesTable = "ApproachTypeCode"

    # Use parameters from command line if provided.
    paramCount = arcpy.GetArgumentCount();
    if paramCount > 1:
        workspace = arcpy.GetParameterAsText(0)
    if paramCount > 2:
        runwayCenterlines = arcpy.GetParameterAsText(1)
    if paramCount > 3:
        surfaceFC = arcpy.GetParameterAsText(2)
    if paramCount > 4:
        approachTypesTable = arcpy.GetParameterAsText(3)
    del paramCount

    # Make sure the workspace exists.
    if not arcpy.Exists(workspace):
        # "Error in accessing the workspace"
        arcpy.AddIDMessage("ERROR", 198)

    # Set the workspace environment variable.
    arcpy.env.workspace = workspace

    # Ensure that the runway centerlines and approach types tables exist.
    for name in (runwayCenterlinesFC, approachTypesTable):
        if not arcpy.Exists(name):
            # "Error in accessing <value>".
            arcpy.AddIDMessage("ERROR", 196, name)

    # Create a dictionary of approach type codes.
    approachTypes = {}
    with arcpy.da.SearchCursor(approachTypesTable, ["LowApproachType", "ESRIApproachType"]) as cursor:
        for row in cursor:
            approachTypes[row[0]] = row[1]
    del approachTypesTable

    fields = [
                "OID@", #OBJECTID
                #"SHAPE@", #SHAPE
                #"OWNERSHIP",
                #"ASSOCIATED",
                #"DESIGNATIO",
                #"RUNWAY_",
                #"ELEVATION",
                #"LineID",
                #"ID",
                #"NAME",
                #"COUNTY",
                #"LENGTH",
                #"WIDTH",
                #"SURFACE",
                "AirportReferenceElev",
                #"HighApproach",
                #"LowApproach",
                "ClearWayLength",
                #"HighID",
                #"LowID",
                "HighApproachType",
                "LowApproachType",
                #"Z_Min",
                #"Z_Max",
                #"Z_Mean",
                #"Avg_Slope",
                # "SHAPE_Length"
            ]

    # Create a dictionary of field names and associated IDs.  Keys are names, values are IDs.
    fieldsDict = {}
    for i in range(0,len(fields)):
        fieldsDict[fields[i]] = i

    layer = "TEMP_LAYER"
    arcpy.management.MakeFeatureLayer(runwayCenterlinesFC, layer)
    centerlineCount = arcpy.management.GetCount(runwayCenterlinesFC)
    i = 0

    try:
        # Loop through the runway centerline features...
        with arcpy.da.SearchCursor(runwayCenterlinesFC, fields) as cursor:
            for row in cursor:
                print "\n\n\nProcessing row %s of %s..." % (i, centerlineCount)
                i = i + 1

                try:
                    # Get parameters from the search cursor row.
                    clear_way_length = row[fieldsDict["ClearWayLength"]]
                    high_runway_end_type = approachTypes[row[fieldsDict["HighApproachType"]]]
                    low_runway_end_type = approachTypes[row[fieldsDict["LowApproachType"]]]
                    airport_elevation = row[fieldsDict["AirportReferenceElev"]]

                    # Select the feature with matching OID.
                    arcpy.management.SelectLayerByAttribute(layer, "NEW_SELECTION", '"OBJECTID" = %s' % row[0])

                    arcpy.FAAFAR77_aeronautical(layer, surfaceFC, clear_way_length, "#", high_runway_end_type,
                                                low_runway_end_type, airport_elevation, "PREDEFINED_SPECIFICATION")
                    # Check for warnings or errors.  If there are any, print the messages from the tool.
                    if arcpy.GetMaxSeverity() > 0:
                        print arcpy.GetMessages()
                except arcpy.ExecuteError as ex:
                    print arcpy.GetMessages()                
    finally:
        arcpy.management.Delete(layer)

except Exception as e:
    print e
    raise
finally:
    arcpy.CheckInExtension("Aeronautical")
    endtime = datetime.datetime.now();
    print "Ended at %s." % endtime
    elapsedtime = endtime - starttime
    print "Elapsed time: %s" % elapsedtime
