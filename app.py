import os

import sqlite3
from sqlite3 import Error
from werkzeug.security import check_password_hash, generate_password_hash
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from functools import wraps
from helpers import login_required, apology

# Configure application
app = Flask(__name__)

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure SQLite to use my database
connection = None
try:
    con = sqlite3.connect("data.db")
    print("Connection to SQLite DB successful")
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
        return apology("TODO: Register action")
    else:
        return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def log_in():
    return apology("TODO: Login page")

@app.route("/read", methods=["GET","POST"])
def read():
    return apology("TODO: Read Menu")