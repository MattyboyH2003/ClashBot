from DatabaseTools.BaseFunctions import UpdateRecord
import sqlite3
import time
import datetime

databaseFile = "MainDatabase.db"

# Opens connection to the database
connectionSQL = sqlite3.connect(databaseFile)
cursorSQL = connectionSQL.cursor() 

date = datetime.datetime.utcfromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M:%S") # Date&Time in the format YYYY-MM-DD HH:MM:SS.SSS

UpdateRecord(cursorSQL, "MemberDetails", ["ClanGamesLastUpdate"], [date], f"ID = 1")

# Closes the connection to the database
cursorSQL.close()

connectionSQL.commit()
connectionSQL.close()
