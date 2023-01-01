from sqlite3 import Cursor

def DeleteRecord(cursorSQL : Cursor, table : str, condition : str) -> None: ...
def AddRecord(cursorSQL : Cursor, table : str, fieldNames : list, data : list) -> None: ...
def CreateTable(cursorSQL : Cursor, tableName : str, fields : list) -> None: ...
def UpdateRecord(cursorSQL : Cursor, tableName : str, fields : list, data : list, condition : str = None) -> None: ...