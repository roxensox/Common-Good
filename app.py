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

# Show the home page, which displays all posts from friends chronologically
@app.route("/", methods=["GET","POST"])
def index():
    # Filters based on friends if the user is signed in
    if session.get("username") != None:
        data = select("data.db","SELECT username, title, time, body, post_id, id, category FROM users JOIN ( SELECT * FROM categories JOIN (SELECT DISTINCT title, user_id, body, time, post_id AS pid FROM posts JOIN connections ON user_id = friend_id AND friender_id = ? OR user_id = ?) ON post_id = pid) ON id = user_id ORDER BY time DESC;", (session.get("user_id"), session.get("user_id")))
    else:
        data = select("data.db", "SELECT username, title, time, body, post_id, id, category FROM users JOIN (SELECT * FROM posts JOIN categories ON posts.post_id = categories.post_id) ON user_id = id ORDER BY time DESC;")
    for row in data:
        row["time"] = row["time"].split(' ')
    return render_template("index.html", posts=data)

# Add a new user to the database, checking to make sure that the username isn't already taken
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Make sure the fields are filled
        if not username or not password:
            flash("Must provide a username and password")
            return redirect("/register")

        # Make sure the username isn't taken
        dbsearch = select("data.db", "SELECT * FROM users WHERE username = ?", username)
        if len(dbsearch) > 0:
            flash('Username taken')
            return redirect("/register")

        # Configure the database connection
        con, cur = connect()
        cur.execute("INSERT INTO users (username, hash, ismod) VALUES (?, ?, ?)", (username, generate_password_hash(password), "N"))
        con.commit()

        # Restart the connection to refresh the database
        con, cur = connect()

        # Get the user's ID from the database to begin initializing the other tables
        id_num = select("data.db", "SELECT id FROM users WHERE username = ?", (username))[0]["id"]

        # Make a timestamp to initialize a blank profile
        ts = time()
        timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        cur.execute("INSERT INTO profiles (user_id, pic_url, join_date) VALUES (?, ?, ?)", (id_num, 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ5zjHGydxteBYChYUS7ZyQSveSrqHHhyA4yw&usqp=CAU', timestamp))
        con.commit()

        # Get the user's username to set the session
        dbsearch = select("data.db", "SELECT * FROM users WHERE username = ?", (username))
        session["user_id"] = dbsearch[0]["id"]
        session["username"] = username

        # Send the user to home with a success message
        flash(f"Registration successful. You are now signed in as {username.capitalize()}.")
        return redirect("/")
    else:
        # If the user is logged in, take them to a page informing them (OBSOLETE: LINK REMOVED FOR LOGGED-IN USERS)
        if session.get("username") != None:
            return render_template("logout.html", name=session.get("username"))
        return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def log_in():
    if request.method == "POST":
        # Get the login information and do the standard database checks
        username = request.form.get("username")
        password = request.form.get("password")
        if not username or not password:
            flash("Must provide a username and password")
            return redirect("/login")
        dbsearch = select("data.db", "SELECT * FROM users WHERE username = ?", username)
        if not check_password_hash(dbsearch[0]["hash"], password):
            flash("Incorrect password")
            return redirect("/login")

        # Set the session up and send the user to home with a success message
        session["user_id"] = dbsearch[0]["id"]
        session["username"] = username
        flash(f"Welcome back, {username.capitalize()}.")
        return redirect("/")
    else:
        # OBSOLETE: LINK REMOVED FOR LOGGED IN USERS
        if session.get("username") != None:
            flash ("You are already signed in.")
            return render_template("logout.html", name=session.get("username").capitalize())    
        return render_template("login.html")

# The page for reading/searching posts
@app.route("/read", methods=["GET","POST"])
def read():
    # If the user has searched, this will return the same page with the filtered results
    if request.method == "POST":
        search = request.form.get("search")
        search = search.split(' ')
        data = []
        pids = []
        for term in search:
            term = f"%{term}%"
            temp = select("data.db", "SELECT * FROM users JOIN (SELECT * FROM posts JOIN categories ON posts.post_id = categories.post_id) ON id = user_id WHERE title LIKE (?) OR username LIKE (?) ORDER BY time DESC;", (term, term))
            for post in temp:
                if post["post_id"] not in pids:
                    post["time"] = post["time"].split(' ')
                    pids.append(post["post_id"])
                    data.append(post)
        return render_template("read.html", posts=data)
    # When the user enters this page through a link, they get all posts ordered chronologically
    else:
        data = select("data.db", "SELECT * FROM users JOIN (SELECT * FROM posts JOIN categories ON  posts.post_id = categories.post_id) ON id = user_id ORDER BY time DESC;")
        for post in data:
            post["time"] = post["time"].split(' ')
        return render_template("read.html", posts=data)

# Logs the user out
@app.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return redirect("/")

# Allows users to post simple reviews, with just a title and text body
@app.route("/write", methods=["GET","POST"])
@login_required
def write_post():
    if request.method == "POST":
        # Gets the information submitted by the user and adds it to the database if everything was done correctly
        title = request.form.get("title")
        bodytext = request.form.get("body")
        user_id = session.get("user_id")
        new_category = request.form.get("addcat")
        category = request.form.get("category")
        if not new_category and not category:
            category = "general"
        if new_category:
            category = new_category
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
        con, cur = connect()
        post_id = select("data.db", "SELECT post_id FROM posts WHERE user_id = ? ORDER BY time DESC LIMIT 1", (user_id))[0]["post_id"]
        cur.execute("INSERT INTO categories VALUES (?, ?);", (post_id, category))
        con.commit()
        flash("Post submitted")
        return redirect("/write")
    else:
        data = select("data.db", "SELECT DISTINCT category FROM categories")
        return render_template("write.html", categories=data)

# Allows the user to view a single post
@app.route("/review", methods=["POST"])
def view():
    # Get the post ID and locates it in the database
    pid = request.form.get("id")
    data = select("data.db", "SELECT username, title, body, time FROM users JOIN posts ON id = user_id WHERE post_id = ?;", (pid))
    if not data:
        return apology("Post not found", 404)
    # Narrow the resulting list down to the one dictionary
    data = data[0]
    # Format the timestamp for viewing
    time = data["time"].split(' ')
    return render_template("review.html", data=data, time=time)

# Loads the user's profile page
@app.route("/myprofile", methods=["GET"])
def profile():
    # Load three lists of dictionaries (users, posts, and profdata) to draw information from for the profile page
    users = select("data.db", "SELECT * FROM users WHERE id = ?;", (session.get("user_id")))
    posts = select("data.db", "SELECT * FROM posts JOIN categories ON posts.post_id = categories.post_id WHERE user_id = ? ORDER BY time DESC;", (session.get("user_id")))
    # Check to make sure that the user has posted before attempting to format the timestamps
    if len(posts) > 0:
        for row in posts:
            row["time"] = row["time"].split(' ')
    profdata = select("data.db", "SELECT * FROM profiles WHERE user_id = ?", (session.get("user_id")))
    profdata = profdata[0]
    profdata["join_date"] = profdata['join_date'].split(' ')
    return render_template("profile.html", users=users, profdata=profdata, posts=posts)

# Allows users to view other users' profiles
@app.route("/usrprofile", methods=["GET","POST"])
def usrprofile():
    # Check to make sure the user isn't trying to view their own profile indirectly
    targ_id = request.form.get("id")
    if session.get("user_id") != None:
        if int(request.form.get("id")) == int(session.get("user_id")):
            return redirect("/myprofile")
    # Initialize the value of friend to reflect that the users are not friends, and then check in the database to see if they are friends
    friend = "N"
    if len(select("data.db", "SELECT * FROM connections WHERE friender_id = ? AND friend_id = ?", (session.get("user_id"), targ_id))) > 0:
        friend = "Y"
    # Load the three necessary dictionaries
    users = select("data.db", "SELECT * FROM users WHERE id = ?;", (targ_id))
    profdata = select("data.db", "SELECT * FROM profiles WHERE user_id = ?", (targ_id))
    profdata = profdata[0]
    profdata["join_date"] = profdata["join_date"].split(' ')
    posts = select("data.db", "SELECT * FROM posts JOIN categories ON posts.post_id = categories.post_id WHERE user_id = ?", (targ_id))
    for row in posts:
        row["time"] = row["time"].split(' ')    
    return render_template("profile.html", users=users, profdata=profdata, posts=posts, friend = friend)

# Allows users to add and remove friends using the button on the user profiles
@app.route("/togglefriend", methods=["POST"])
def togfriend():
    targ_id = request.form.get("toggle")
    usr_id = session.get("user_id")
    # Check to see if the users are already friends. If they are, remove the connection, and update the status of the mutual column to reflect the change
    checkdb = select("data.db", "SELECT * FROM connections WHERE friender_id = ? AND friend_id = ?", (usr_id, targ_id))
    con, cur = connect()
    if len(checkdb) > 0:
        cur.execute("DELETE FROM connections WHERE friender_id = ? AND friend_id = ?", (usr_id, targ_id))
        con.commit()
        mutcheck = select("data.db", "SELECT * FROM connections WHERE friender_id = ? AND friend_id = ?", (targ_id, usr_id))
        if len(mutcheck) > 0:
            cur.execute("UPDATE connections SET mutual = 'N' WHERE friender_id = ? AND friend_id = ?", (targ_id, usr_id))
            con.commit()
        flash("Friend removed")
        return redirect("/")
    else:
        # If they are not friends, add the connection. Then check if the connection is mutual, and update the database to reflect that
        cur.execute("INSERT INTO connections (friender_id, friend_id, mutual) VALUES (?, ?, 'N')", (usr_id, targ_id))
        con.commit()
        con, cur = connect()
        mutcheck = select("data.db", "SELECT * FROM connections WHERE friender_id = ? AND friend_id = ?", (targ_id, usr_id))
        if len(mutcheck) > 0:
            cur.execute("UPDATE connections SET mutual = 'Y' WHERE (friender_id = ? AND friend_id = ?) OR (friender_id = ? AND friend_id = ?)", (usr_id, targ_id, targ_id, usr_id))
            con.commit()
        flash("Friend added")
        return redirect("/friends")

# Allows users to view their friends list
@app.route("/friends", methods=["GET","POST"])
def viewfriends():
    # Start with a list of dictionaries for each friend, and add the appropriate information to it before loading the page
    flist = select("data.db", "SELECT friend_id, mutual FROM connections WHERE friender_id = ?", session.get("user_id"))
    for row in flist:
        data = select("data.db", "SELECT username, id FROM users WHERE id = ?", (row["friend_id"]))[0]
        row["username"] = data["username"]
        row["id"] = data["id"]
        data = select("data.db", "SELECT join_date FROM profiles WHERE user_id = ?", row["friend_id"])[0]
        row["join_date"] = data["join_date"].split(' ')[0]
        data = select("data.db", "SELECT COUNT(post_id) AS posts FROM posts WHERE user_id = ?", (row["friend_id"]))[0]
        row["posts"] = data["posts"]
    return render_template("friends.html", friends=flist)

# TODO: Make a settings page where users can change their username or password
@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    return render_template("settings.html")

@app.route("/changeusername", methods=["POST"])
def changeusr():
    new_name = request.form.get("username")
    data = select("data.db", "SELECT * FROM users WHERE username = ?", (new_name))
    if not new_name:
        flash("Must provide a new username")
        return redirect("/settings")
    if len(data) > 0:
        flash("Username taken")
        return redirect("/settings")
    con, cur = connect()
    cur.execute("UPDATE users SET username = ? WHERE id = ?", (new_name, session.get("user_id")))
    con.commit()
    flash("Username updated")
    return redirect("/settings")

@app.route("/changepassword", methods=["POST"])
def changepw():
    new_password = request.form.get("password")
    old_password = select("data.db", "SELECT hash FROM users WHERE id = ?", (session.get("user_id")))[0]["hash"]
    if not new_password:
        flash("Must provide a new password")
        return redirect("/settings")
    if check_password_hash(old_password, new_password):
        flash("New password cannot be the same as the old password")
        return redirect("/settings")
    con, cur = connect()
    cur.execute("UPDATE users SET hash = ? WHERE id = ?", (generate_password_hash(new_password), session.get("user_id")))
    con.commit()
    flash("Password updated")
    return redirect("/settings")

@app.route("/deleteaccount", methods=["POST"])
def deleteacc():
    password = request.form.get("confirm")
    passhash = select("data.db", "SELECT hash FROM users WHERE id = ?", (session.get("user_id")))[0]["hash"]
    user_id = session.get("user_id")
    if not password:
        flash("Must confirm your password before deleting")
        return redirect("/settings")
    if check_password_hash(passhash, password):
        con, cur = connect()
        posts = select("data.db", "SELECT post_id FROM posts WHERE user_id = ?", (user_id))
        if len(posts) > 0:
            for row in posts:
                print(row["post_id"])
                cur.execute("DELETE FROM posts WHERE post_id = ?", (row["post_id"],))
                cur.execute("DELETE FROM categories WHERE post_id = ?", (row["post_id"],))
        cur.execute("DELETE FROM connections WHERE friend_id = ? OR friender_id = ?", (user_id, user_id))
        cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
        cur.execute("DELETE FROM profiles WHERE user_id = ?", (user_id,))
        con.commit()
        session.clear()
        flash("Account deleted.")
        return redirect("/")
    flash("Incorrect password")
    return redirect("/settings")

@app.route("/changepic", methods=["POST"])
@login_required
def changepic():
    url = request.form.get("new_url")
    if not url:
        flash("Must provide a url for your new picture")
        return redirect("/myprofile")
    con, cur = connect()
    cur.execute("UPDATE profiles SET pic_url = ? WHERE user_id = ?", (url, session.get("user_id")))
    con.commit()
    flash("Picture updated")
    return redirect("/myprofile")

@app.route("/changedescription", methods=["POST"])
@login_required
def changedesc():
    description = request.form.get("new_description")
    if not description:
        flash("For a blank description, write [BLANK] for the description.")
        return redirect("/myprofile")
    if description == "[BLANK]":
        description = ''
    con, cur = connect()
    cur.execute("UPDATE profiles SET description = ? WHERE user_id = ?", (description, session.get("user_id")))
    con.commit()
    flash("Description updated.")
    return redirect("/myprofile")