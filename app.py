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
            flash("Must provide a username and password")
            return redirect("/register")
        dbsearch = select("data.db", "SELECT * FROM users WHERE username = ?", username)
        if len(dbsearch) > 0:
            flash('Username taken')
            return redirect("/register")
        con, cur = connect()
        cur.execute("INSERT INTO users (username, hash, ismod) VALUES (?, ?, ?)", (username, generate_password_hash(password), "N"))
        con.commit()
        con, cur = connect()
        return redirect("/")
    else:
        return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def log_in():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if not username or not password:
            flash("Must provide a username and password")
            return redirect("/login")
        dbsearch = select("data.db", "SELECT * FROM users WHERE username = ?", username)
        if not check_password_hash(dbsearch[0]["hash"], password):
            flash("Incorrect password")
            return redirect("/login")
        session["user_id"] = dbsearch[0]["id"]
        session["username"] = username
        flash("Session on")
        return redirect("/")
    else:
        if session.get("username") != None:
            flash ("You are already signed in.")
            return render_template("logout.html", name=session.get("username"))    
        return render_template("login.html")

@app.route("/read", methods=["GET","POST"])
def read():
    return apology("TODO: Read Menu")

@app.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return redirect("/")

