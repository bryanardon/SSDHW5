from flask import Flask, request, make_response, redirect, render_template, g, abort
from user_service import get_user_with_credentials, logged_in, login_required
from account_service import get_balance, do_transfer, get_accounts
from flask_wtf.csrf import CSRFProtect
from secrets import token_hex
from functools import wraps
from flask import redirect, url_for
super_secret_key = token_hex(32)


app = Flask(__name__)
app.config['SECRET_KEY'] = super_secret_key
csrf = CSRFProtect(app) 

@app.route("/", methods=['GET'])
def home():
    if not logged_in():
        return render_template("login.html")
    return redirect('/dashboard')

@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("email")
    password = request.form.get("password")
    user = get_user_with_credentials(email, password)
    if not user:
        return render_template("login.html", error="Invalid credentials")
    response = make_response(redirect("/dashboard"))
    response.set_cookie("auth_token", user["token"])
    return response, 303
    

@app.route("/dashboard", methods=['GET'])
def dashboard():
    if not logged_in():
        return render_template("login.html")
    accounts = get_accounts(g.user)
    acc_nums = []
    for account in accounts:
        account_number, _, _ = account
        acc_nums.append(account_number)
    return render_template("dashboard.html", email=g.user, accounts=acc_nums)

@app.route("/logout", methods=['GET'])
def logout():
    response = make_response(redirect("/"))
    response.delete_cookie('auth_token')
    return response, 303

@app.route("/details", methods=['GET', 'POST'])
@login_required
def details():
    account_number = request.args['account']
    return render_template("details.html", account_number=account_number, user=g.user, balance=get_balance(account_number, g.user))

@app.route("/transfer", methods=["GET", "POST"])
@login_required
def transfer():
    if request.method == "GET":
        return render_template("transfer.html", user=g.user)
    
    source = request.form.get("from")
    target = request.form.get("to")
    try:
        amount = int(request.form.get("amount"))
    except ValueError:
        abort(400, "Invalid amount please make it integer")

    if amount < 0:
        abort(400, "Can't transfer from negative account balance")
    if amount > 1000:
        abort(400, "Can't transfer more than 1000 at a time")

    available_balance = get_balance(source, g.user)
    if available_balance is None:
        abort(404, "Account not found")
    if amount > available_balance:
        abort(400, "Not enough funds for transfer")

    if do_transfer(source, target, amount):
        return render_template("successful_transfer.html", source=source, target=target, amount=amount, user=g.user)
    else:
        abort(400, "Something bad happened")

    response = make_response(redirect("/dashboard"))
    return response, 303