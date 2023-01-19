from werkzeug.security import check_password_hash, generate_password_hash
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from functools import wraps
import sqlite3

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message), username=session.get("username")), code


def select(database, query:str, query_variable=None):

    # Declare the cursor
    connection = sqlite3.connect(database)
    cur = connection.cursor()

    # Turn single variables into tuples so the sql executes
    if not isinstance(query_variable, tuple) and query_variable != None:
        query_variable = tuple([query_variable])

    # Execute the select query and put all the names in a list, then get all the data as a list
    if len(query_variable) > 1:
        cur.execute(query, query_variable)
    elif query_variable == None:
        cur.execute(query)
    else:
        cur.execute(query, query_variable)
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
