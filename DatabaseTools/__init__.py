import sqlite3

DATABASEFILE = "MainDatabase.db"

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

if __name__ == "__main__":
    from TableVisualiser import tableVisualise
    from BaseFunctions import *
    
    connectionSQL = sqlite3.connect("MainDatabase.db")
    cursorSQL = connectionSQL.cursor()

    #cursorSQL.execute("""CREATE TABLE MemberMessages (ID INTEGER PRIMARY KEY, ServerID INTEGER NOT NULL, ChannelID INTEGER NOT NULL, MessageID INTEGER NOT NULL)""")
    #cursorSQL.execute("""CREATE TABLE ServerClansLink (ID INTEGER PRIMARY KEY, ServerID INTEGER NOT NULL, ClanTag VARCHAR(10) NOT NULL)""")

    
    connectionSQL.commit()
    
    tableVisualise(connectionSQL, "MemberMessages")
    tableVisualise(connectionSQL, "ServerClansLink")


else:
    from DatabaseTools.BaseFunctions import *


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
    ClanTag VARCHAR(10) NOT NULL
)

CREATE TABLE ClanWarStars (
    ID INTEGER PRIMARY KEY,
    PlayerTag VARCHAR(10) NOT NULL,
    ClanWarStars INTEGER NOT NULL
)

"""