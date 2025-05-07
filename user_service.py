import sqlite3
import datetime
from passlib.hash import pbkdf2_sha256
from flask import request, g
import jwt
from functools import wraps
from flask import redirect, url_for
from dotenv import load_dotenv
import os
load_dotenv()
SECRET = os.getenv('SECRET')

def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not logged_in():
            return redirect(url_for("login"))  # Redirect to the login route
        return func(*args, **kwargs)
    return wrapper

def get_user_with_credentials(email, password):
    try:
        con = sqlite3.connect('bank.db')
        cur = con.cursor()
        cur.execute('''
            SELECT email, name, password FROM users where email=?''',
            (email,))
        row = cur.fetchone()
        # Assign default values to email, name, and the_hash to avoid user enumeration.
        # By assigning default values to email, name, and the_hash, the application does 
        # not reveal whether the user exists or not and will take the same amount of time 
        # as a normal user.
        email = "fake_email"
        name = "fake_name" 
        the_hash = pbkdf2_sha256.hash("T9f!x#7B$wR@Z1qM&uK2L%yD^NpE4vGd")
        if row is not None:
            email, name, the_hash = row
        if not pbkdf2_sha256.verify(password, the_hash):
            return None
        return {"email": email, "name": name, "token": create_token(email)}
    finally:
        con.close()

def logged_in():
    # look inside cookie for auth_token
    token = request.cookies.get('auth_token')
    try:
        # checks to see if the token is valid 
        data = jwt.decode(token, SECRET, algorithms=['HS256'])
        # If so get the subject sub
        # g is a session, prononced "g" for global
        # g is a special object in Flask that is used to store data
        # for the current request. It is a global variable that is
        # unique to each request and is used to store data that
        # is needed for the duration of the request.
        g.user = data['sub']
        return True
    except jwt.InvalidTokenError:
        return False

def create_token(email):
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {'sub': email, 'iat': now, 'exp': now + datetime.timedelta(minutes=60)}
    token = jwt.encode(payload, SECRET, algorithm='HS256')
    return token