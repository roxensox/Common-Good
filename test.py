import sqlite3

def select(connection, query, query_variables):

    # Declare the cursor
    cur = connection.cursor()

    # Execute the select query and put all the names in a list, then get all the data as a list
    cur.execute(query, query_variables)
    names = list(map(lambda x: x[0], cur.description))
    db = cur.fetchall()

    # Initialize the output list
    dictlist = []

    # Create a dictionary for each row, then add it to the output list
    for row in range(len(db)):
        currow = db[row]
        currowdict = {}
        for col in range(len(currow)):
            currowdict[names[col]] = currow[col]
        dictlist.append(currowdict)

    return dictlist