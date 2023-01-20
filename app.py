import os

import sqlite3
from sqlite3 import Error
from werkzeug.security import check_password_hash, generate_password_hash
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from functools import wraps
from helpers import login_required, apology, select
from time import time
import datetime

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
    data = select("data.db","SELECT username, title, time, body, post_id FROM users JOIN posts ON id = user_id;")
    for row in data:
        row["time"] = row["time"].split(' ')
    return render_template("index.html", posts=data)

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
        dbsearch = select("data.db", "SELECT * FROM users WHERE username = ?", username)
        session["user_id"] = dbsearch[0]["id"]
        session["username"] = username
        flash(f"Registration successful. You are now signed in as {username.capitalize()}.")
        return redirect("/")
    else:
        if session.get("username") != None:
            return render_template("logout.html", name=session.get("username"))
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
        flash(f"Welcome back, {username.capitalize()}.")
        return redirect("/")
    else:
        if session.get("username") != None:
            flash ("You are already signed in.")
            return render_template("logout.html", name=session.get("username").capitalize())    
        return render_template("login.html")

@app.route("/read", methods=["GET","POST"])
def read():
    if request.method == "POST":
        search = request.form.get("search")
        search = search.split(' ')
        data = []
        pids = []
        for term in search:
            term = f"%{term}%"
            temp = select("data.db", "SELECT * FROM posts JOIN users ON id = user_id WHERE title LIKE (?) OR username LIKE (?) OR body LIKE (?);", (term, term, term))
            for post in temp:
                if post["post_id"] not in pids:
                    post["time"] = post["time"].split(' ')
                    pids.append(post["post_id"])
                    data.append(post)
        return render_template("read.html", posts=data)   
    else:
        data = select("data.db", "SELECT * FROM posts JOIN users ON id = user_id;")
        for post in data:
            post["time"] = post["time"].split(' ')
        return render_template("read.html", posts=data)

@app.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return redirect("/")

@app.route("/write", methods=["GET","POST"])
@login_required
def write_post():
    if request.method == "POST":
        title = request.form.get("title")
        bodytext = request.form.get("body")
        user_id = session.get("user_id")
        ts = time()
        timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        
        if not title:
            flash("Must provide a title")
            return redirect("/write")
        if not bodytext:
            flash("Must provide body text")
            return redirect("/write")
        con, cur = connect()
        cur.execute("INSERT INTO posts (user_id, title, body, time) VALUES (?, ?, ?, ?)", (user_id, title, bodytext, timestamp))
        con.commit()
        flash("Post submitted")
        return redirect("/write")
    else:
        return render_template("write.html")

@app.route("/review", methods=["POST"])
def view():
    pid = request.form.get("id")
    data = select("data.db", "SELECT username, title, body, time FROM users JOIN posts ON id = user_id WHERE post_id = ?;", (pid))
    if not data:
        return apology("Post not found", 404)    
    data = data[0]
    time = data["time"].split(' ')
    return render_template("review.html", data=data, time=time)

@app.route("/profile", methods=["GET", "POST"])
def profile():
    return apology("TODO: Profile")

@app.route("/settings", methods=["GET", "POST"])
def settings():
    return apology("TODO: Settings")

@app.route("/friends", methods=["GET","POST"])
def friends():
    return apology("TODO: Friends")