import sqlite3
import time
import datetime

from ClashInterface import GetPlayerInfo, GetClanWar

DATABASEFILE = "MainDatabase.db"

########################
# - Public Functions - #
########################

#Server Get Functions

def GetMemberMessages(serverID : int, databaseFile : str = DATABASEFILE) -> list:
    connectionSQL = sqlite3.connect(databaseFile)
    cursorSQL = connectionSQL.cursor()
    
    query = f"SELECT ChannelID, MessageID FROM MemberMessages WHERE ServerID = {serverID}"
    cursorSQL.execute(query)
    result = cursorSQL.fetchall()
    
    cursorSQL.close()
    connectionSQL.close()

    return result

def GetPrimaryClan(serverID : int, databaseFile : str = DATABASEFILE) -> str:
    connectionSQL = sqlite3.connect(databaseFile)
    cursorSQL = connectionSQL.cursor()

    query = f"SELECT ClanTag FROM ServerClansLink WHERE ServerID = {serverID}"

    cursorSQL.execute(query)
    result = cursorSQL.fetchall()
    
    cursorSQL.close()
    connectionSQL.close()

    return result[0][0]

# Player Get Functions

def GetWarParticipation(playerTag : str, databaseFile : str = DATABASEFILE) -> bool:
    # Opens connection to the database
    connectionSQL = sqlite3.connect(databaseFile)
    cursorSQL = connectionSQL.cursor() 
    
    # Query for finding participation
    query = f"SELECT ClanWarMark FROM MemberDetails WHERE PlayerTag = ?"

    cursorSQL.execute(query, [playerTag])
    result = cursorSQL.fetchall()
    
    cursorSQL.close()
    connectionSQL.close()
    # If the player isnt in the database then add them and return false
    if not result:
        AddPlayerDefault(playerTag)
        return False

    # Return their participation
    return result[0][0]

def GetClanGamesParticipation(playerTag : str, databaseFile : str = DATABASEFILE) -> bool:
    # Opens connection to the database
    connectionSQL = sqlite3.connect(databaseFile)
    cursorSQL = connectionSQL.cursor() 
    
    # Query for finding participation
    query = f"SELECT ClanGamesMark FROM MemberDetails WHERE PlayerTag = ?"

    cursorSQL.execute(query, [playerTag])
    result = cursorSQL.fetchall()
    
    cursorSQL.close()
    connectionSQL.close()
    # If the player isnt in the database then add them and return false
    if not result:
        AddPlayerDefault(playerTag)
        return False

    # Return their participation
    return result[0][0]

def GetClanGamesPoints(playerTag : str, databaseFile : str = DATABASEFILE) -> str:
    # Opens connection to the database
    connectionSQL = sqlite3.connect(databaseFile)
    cursorSQL = connectionSQL.cursor() 
    
    # Query for finding participation
    query = f"SELECT ClanGamesPoints FROM MemberDetails WHERE PlayerTag = ?"

    cursorSQL.execute(query, [playerTag])
    result = cursorSQL.fetchall()
    
    cursorSQL.close()
    connectionSQL.close()

    # If the player isnt in the database then add them and return false
    if not result:
        AddPlayerDefault(playerTag)
        return GetClanGamesPoints(playerTag, databaseFile)

    # Return their participation
    return result[0][0]

def GetClanGamesLastUpdate(playerTag : str, databaseFile : str = DATABASEFILE) -> str:
    # Opens connection to the database
    connectionSQL = sqlite3.connect(databaseFile)
    cursorSQL = connectionSQL.cursor() 
    
    # Query for finding participation
    query = f"SELECT ClanGamesLastUpdate FROM MemberDetails WHERE PlayerTag = ?"

    cursorSQL.execute(query, [playerTag])
    result = cursorSQL.fetchall()
    
    cursorSQL.close()
    connectionSQL.close()
    # If the player isnt in the database then add them and return false
    if not result:
        AddPlayerDefault(playerTag)
        return datetime.datetime.utcfromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M:%S") # Date&Time in the format YYYY-MM-DD HH:MM:SS.SSS

    # Return their participation
    return result[0][0]

# Other Database Functions

def LinkClan(serverID : int, clanTag : str, databaseFile : str = DATABASEFILE) -> bool:
    connectionSQL = sqlite3.connect(databaseFile)
    cursorSQL = connectionSQL.cursor()

    validClan = _CheckClan(clanTag)

    if validClan:
        DeleteRecord(cursorSQL, "ServerClansLink", f"ServerID = {serverID}")
        AddRecord(cursorSQL, "ServerClansLink", ["ServerID", "ClanTag"], [serverID, clanTag])
    
    cursorSQL.close()
    connectionSQL.commit()
    connectionSQL.close()

    return validClan

def AddPlayerDefault(playerTag : str, databaseFile : str = DATABASEFILE) -> None:
    # Opens connection to the database
    connectionSQL = sqlite3.connect(databaseFile)
    cursorSQL = connectionSQL.cursor() 
    
    # Fields and Data for the AddRecord Query
    fieldNames = ["PlayerTag", "ClanWarMark", "ClanGamesMark", "ClanGamesPoints", "ClanGamesLastUpdate"]

    date = datetime.datetime.utcfromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M:%S") # Date&Time in the format YYYY-MM-DD HH:MM:SS.SSS
    print(date)

    playerAchivements = GetPlayerInfo(tokens["CoC"]["token"], playerTag)["achievements"] # Players Current Clan Games Points

    for achivement in playerAchivements:
        if achivement["name"] == "Games Champion":
            cgPoints = achivement["value"]

    data = [playerTag, False, False, cgPoints, date]
    
    AddRecord(cursorSQL, "MemberDetails", fieldNames, data)

    # Closes the connection to the database
    cursorSQL.close()

    connectionSQL.commit()
    connectionSQL.close()

def UpdateClanGamesInfo(playerTag : str, monthDiff : int, databaseFile : str = DATABASEFILE) -> None:
    if monthDiff < 1:
        return

    lastCGPoints = GetClanGamesPoints(playerTag, databaseFile)
    playerAchivements = GetPlayerInfo(tokens["CoC"]["token"], playerTag)["achievements"] # Players Current Clan Games Points

    for achivement in playerAchivements:
        if achivement["name"] == "Games Champion":
            currentCGPoints = achivement["value"]

    pointsDiff = currentCGPoints - lastCGPoints
    avgPointsDiff = int(pointsDiff/monthDiff)

    earntMark = avgPointsDiff > 1000

    # Opens connection to the database
    connectionSQL = sqlite3.connect(databaseFile)
    cursorSQL = connectionSQL.cursor() 

    date = datetime.datetime.utcfromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M:%S") # Date&Time in the format YYYY-MM-DD HH:MM:SS.SSS

    UpdateRecord(cursorSQL, "MemberDetails", ["ClanGamesMark", "ClanGamesPoints", "ClanGamesLastUpdate"], [earntMark, currentCGPoints, date], f"PlayerTag = {playerTag}")

    # Closes the connection to the database
    cursorSQL.close()

    connectionSQL.commit()
    connectionSQL.close()

def UpdateWarMark(playerTag : str, newState : bool, databaseFile : str = DATABASEFILE) -> None:
    # Opens connection to the database
    connectionSQL = sqlite3.connect(databaseFile)
    cursorSQL = connectionSQL.cursor() 

    UpdateRecord(cursorSQL, "MemberDetails", ["ClanWarMark"], [newState], "PlayerTag = ?", [playerTag[1:]])

    # Closes the connection to the database
    cursorSQL.close()

    connectionSQL.commit()
    connectionSQL.close()


########################
# - Hidden Functions - #
########################

def _CheckClan(clanTag):
    validChars = [
        "A", "B", "C", "D", "E", "F", "G", "H", "I", "J",
        "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T",
        "U", "V", "W", "X", "Y", "Z",
        "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"
    ]
    if len(clanTag) > 10 or len(clanTag) < 7:
        return False

    for char in clanTag:
        if char not in validChars:
            return False

    return True


#############
# - Other - #
#############

if __name__ == "__main__":
    from TableVisualiser import tableVisualise
    from BaseFunctions import *
    
    connectionSQL = sqlite3.connect("MainDatabase.db")
    cursorSQL = connectionSQL.cursor()

    #cursorSQL.execute("""CREATE TABLE MemberMessages (ID INTEGER PRIMARY KEY, ServerID INTEGER NOT NULL, ChannelID INTEGER NOT NULL, MessageID INTEGER NOT NULL)""")
    #cursorSQL.execute("""CREATE TABLE ServerClansLink (ID INTEGER PRIMARY KEY, ServerID INTEGER NOT NULL, ClanTag VARCHAR(10) NOT NULL)""")
    
    #cursorSQL.execute("""CREATE TABLE MemberDetails (
    #    ID INTEGER PRIMARY KEY,
    #    PlayerTag TEXT NOT NULL,
    #    ClanWarMark BOOLEAN NOT NULL,
    #    ClanGamesMark BOOLEN NOT NULL,
    #    ClanGamesPoints INTEGER NOT NULL,
    #    ClanGamesLastUpdate TEXT NOT NULL
    #)""")

    #AddRecord(cursorSQL, "MemberDetails", 
    #    ["PlayerTag", "ClanWarMark", "ClanGamesMark", "ClanGamesPoints", "ClanGamesLastUpdate"],
    #    ["Y802GG8L", True, True, 67600, "2023-01-01 12:30:00"]
    #)

    connectionSQL.commit()
    
    #tableVisualise(connectionSQL, "MemberMessages")
    tableVisualise(connectionSQL, "ServerClansLink")

else:
    from DatabaseTools.BaseFunctions import *
    from ClashInterface import GetPlayerInfo
    import json

    with open("tokens.json", "r") as tokenfile:
        tokens = json.loads(tokenfile.read())

#####################
# - Table Formats - #
#####################

"""
CREATE TABLE MemberMessages (
    ID INTEGER PRIMARY KEY,
    ServerID INTEGER NOT NULL,
    ChannelID INTEGER NOT NULL,
    MessageID INTEGER NOT NULL
)

CREATE TABLE ServerClansLink (
    ID INTEGER PRIMARY KEY,
    ServerID INTEGER NOT NULL,
    ClanTag TEXT NOT NULL
)

CREATE TABLE MemberDetails (
    ID INTEGER PRIMARY KEY,
    PlayerTag TEXT NOT NULL,
    ClanWarMark BOOLEAN NOT NULL,
    ClanGamesMark BOOLEN NOT NULL,
    ClanGamesPoints INTEGER NOT NULL,
    ClanGamesLastUpdate TEXT NOT NULL
)

+----------------------------------------------------------+
|                          Not Used                        |
\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/

CREATE TABLE ClanWarStars (
    ID INTEGER PRIMARY KEY,
    PlayerTag VARCHAR(10) NOT NULL,
    ClanWarStars INTEGER NOT NULL
)

CREATE TABLE ClanGamesPoints (
    ID INTEGER PRIMARY KEY,
    PlayerTag VARCHAR(10) NOT NULL,
    ClanGamesPoints INTEGER NOT NULL
)

"""