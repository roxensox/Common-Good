import os

import sqlite3
from sqlite3 import Error
from werkzeug.security import check_password_hash, generate_password_hash
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from functools import wraps
from helpers import login_required, apology, select

# Configure application
app = Flask(__name__)

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

    # Configure SQLite to use my database
def connect():
    connection = None
    try:
        connection = sqlite3.connect("data.db")
        print("Connection to SQLite DB successful")
        cursor = connection.cursor()
        return (connection, cursor)

    except Error as e:
        print(f"The error '{e}' occurred")

@app.route("/", methods=["GET","POST"])
def index():
    """ Show Menu """
    return apology("TODO: Main page")

@app.route("/write", methods=["GET","POST"])
@login_required
def post_content():
    """ Allow users to post reviews """
    return apology("TODO: Post content")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if not username or not password:
            return apology("Must provide a username and password")
        dbsearch = select("data.db", "SELECT * FROM users WHERE username = ?", username)
        if len(dbsearch) > 1:
            return apology("Username taken")
        con, cur = connect()
        cur.execute("INSERT INTO users (username, hash, ismod) VALUES (?, ?, ?)", (username, generate_password_hash(password), "N"))
        con.commit()
        return redirect("/")
    else:
        return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def log_in():
    return apology("TODO: Login page")

@app.route("/read", methods=["GET","POST"])
def read():
    return apology("TODO: Read Menu")

