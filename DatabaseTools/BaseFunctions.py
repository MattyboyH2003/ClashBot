from sqlite3 import Cursor

def DeleteRecord(cursorSQL : Cursor, table, condition):
    query = f"""
        DELETE FROM {table} WHERE {condition};
    """
    cursorSQL.execute(query)

    print(f"Record(s) deleted from table '{table}'")

def AddRecord(cursorSQL : Cursor, table, fieldNames, data):
    query = f"""
        INSERT INTO {table} ({(''.join([str(fieldname) + ', ' for fieldname in fieldNames]))[:-2]}) 
        VALUES ({(''.join(['?, ' for _ in fieldNames]))[:-2]});
    """
    cursorSQL.execute(query, data)

    print(f"Record added to table '{table}'")

def CreateTable(cursorSQL : Cursor, tableName : str, fields : list) -> None:
    query = f"""CREATE TABLE {tableName} ({(''.join([str(fieldname) + ', ' for fieldname in fields]))[:-2]})"""

    cursorSQL.execute(query)

    print("Table Created")

def UpdateRecord(cursorSQL : Cursor, tableName : str, fields : list, data : list, condition : str = None):
    if len(fields) != len(data):
        raise ValueError(f"UPDATE command given {len(fields)} fields and {len(data)} data")
    
    query = f"UPDATE {tableName} SET "
    
    for i in range(0, len(fields)):
        query += fields[i] + " = ?"
    
    if condition:
        query += " WHERE " + condition
    
    print(query)

    cursorSQL.execute(query, data)

