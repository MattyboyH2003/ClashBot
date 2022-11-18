
def _visualiseBase(fieldNames, resultData):

    # Calculates the length of the longest piece of data in each field
    longestPieceOfData = []
    counter = 0
    for fieldName in fieldNames: 
        longestLength = len(fieldName)
        for record in resultData:
            if longestLength < len(str(record[counter])):
                longestLength = len(str(record[counter]))
        longestPieceOfData.append(longestLength)
        counter += 1

    # Start the visualised database string empty
    visualised = ""

    # Add the upper line
    output = "╔═"
    for item in longestPieceOfData:
        output += "".join(["═" for _ in range(0, item)])
        output += "═╤═"
    output = output[0:(len(output)-3)] + "═╗"
    visualised += output + "\n"

    # Add the field names
    output = "║ "
    columnNum = 0
    for fieldName in fieldNames:
        spaces = ""
        if len(fieldName) < longestPieceOfData[columnNum]:
            addedSpaces = longestPieceOfData[columnNum] - len(fieldName)
            spaces = " "*addedSpaces
        output += fieldName + spaces + " │ "
        columnNum += 1
    output = output[0:(len(output)-2)] + "║"
    visualised += output + "\n"

    # Add the divider between field names and records
    output = "╠═"
    for item in longestPieceOfData:
        output += "".join(["═" for _ in range(0, item)])
        output += "═╪═"
    output = output[0:(len(output)-3)] + "═╣"
    visualised += output + "\n"

    # Add the records
    for item in resultData:
        output = "║ "
        columnNum = 0
        for data in item:
            spaces = ""
            if len(str(data)) < longestPieceOfData[columnNum]:
                addedSpaces = longestPieceOfData[columnNum] - len(str(data))
                spaces = " "*addedSpaces
            output += str(data) + spaces + " │ "
            columnNum += 1
        output = output[0:(len(output)-2)] + "║"
        visualised += output + "\n"

    # Add the bottom line
    output = "╚═"
    for item in longestPieceOfData:
        output += "".join(["═" for _ in range(0, item)])
        output += "═╧═"
    output = output[0:(len(output)-3)] + "═╝"
    visualised += output + "\n"

    # Return the string containing the visualised database
    return(visualised)

def tableVisualise(connectionSQL, table, output = True):
    
    cursorSQL = connectionSQL.cursor()
    
    #This section gets the names of all columns in a table
    query = ("PRAGMA table_info({})").format(table)
    cursorSQL.execute(query)
    result = cursorSQL.fetchall()
    fieldNames =  []
    for i in range(0, len(result)):
        fieldNames.append(result[i][1])

    #This section gets the number of records in a table
    query = ("SELECT * FROM {}").format(table)
    cursorSQL.execute(query)
    result = cursorSQL.fetchall()

    visualised = _visualiseBase(fieldNames, result)
    if output:
        print(visualised)
    return visualised

def advancedVisualise(fieldNames, resultData, print = True):
    visualised = _visualiseBase(fieldNames, resultData)
    print(visualised)
    return visualised

def queryVisualise(cursorSQL, query, *args, print = True):

    # Find the position of the FROM keyword
    frompos = -1
    for i in range(0, len(query) - 4):
        segment = query[i:i+4]
        if segment == "FROM":
            frompos = i
            break

    # Find the position of the SELECT keyword
    selectpos = -1
    for i in range(0, len(query) - 6):
        segment = query[i:i+6]
        if segment == "SELECT":
            selectpos = i+6
            break

    # Cut the query down to just the selected fields secion
    fields = query[selectpos:frompos]
    fields = fields.replace(" ", "")
    fields = fields.replace("\n", "")

    # If selecting all fields
    if fields == "*":
        # Blacklist of known non-tablenames
        BLACKLIST = ["", "JOIN", "SELECT", "WHERE", "?", "ON", "=", "ORDER", "BY"]

        # Select all the statement after the FROM keyword and split around spaces
        querySegments = query[frompos+5:].split(" ") 
        
        # Remove all '\n's and brackets from all segments
        for i in range(0, len(querySegments)):
            querySegments[i] = querySegments[i].replace("\n", "")
            querySegments[i] = querySegments[i].replace(")", "")
            querySegments[i] = querySegments[i].replace("(", "")

        # Remove all blacklisted segments
        removedItems = 0
        for i in range(0, len(querySegments)):
            for item in BLACKLIST:
                if querySegments[i-removedItems] == item:
                    querySegments.remove(item)
                    removedItems += 1
                    break
        
        # Remove all segments that are table.fields
        removedItems = 0
        for i in range(0, len(querySegments)):
            if '.' in querySegments[i-removedItems]:
                querySegments.remove(querySegments[i-removedItems])
                removedItems += 1
        
        # Get all fields from all tables
        fieldNames = []
        for table in querySegments:
            pragmaQuery = ("PRAGMA table_info({})").format(table)
            cursorSQL.execute(pragmaQuery)
            result = cursorSQL.fetchall()
            for i in range(0, len(result)):
                fieldNames.append(table + "." + result[i][1])

    # Split the fields around commas and store in the fieldNames list
    else:
        fieldNames = fields.split(",")
    
    # Collect the data from the query
    cursorSQL.execute(query, *args)
    result = cursorSQL.fetchall()

    # Visualise the result with the fields identified
    visualised = _visualiseBase(fieldNames, result)

    print(visualised)

    # Return the string containing the visualised table
    return visualised
