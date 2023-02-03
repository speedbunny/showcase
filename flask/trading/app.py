import os
#import sys
#import subprocess

# implement pip as a subprocess:
# subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'password_strength'])

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
# from password_strength import PasswordStats
from helpers import apology, login_required, lookup, usd

# configure application
app = Flask(__name__)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///trading.db")

@app.route("/")
@login_required
def index():

    shares = db.execute("SELECT * FROM shares WHERE user_id = :user_id ORDER BY symbol ASC", user_id=session["user_id"])
    user = db.execute("SELECT * FROM users WHERE id = :id", id=session["user_id"])
    grand_total = 0.0

    for i in range(len(shares)):
        share = lookup(shares[i]["symbol"])
        shares[i]["company"] = share["name"]
        shares[i]["cur_price"] = "%.2f"%(share["price"])
        shares[i]["cur_total"] = "%.2f"%(float(share["price"]) * float(shares[i]["quantity"]))
        shares[i]["profit"] = "%.2f"%(float(shares[i]["cur_total"]) - float(shares[i]["total"]))
        grand_total += shares[i]["total"]
        shares[i]["total"] = "%.2f"%(shares[i]["total"])

    grand_total += float(user[0]["cash"])

    return render_template("index.html", shares=shares, cash=usd(user[0]["cash"]), grand_total=usd(grand_total))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares"""
    # User reaches this route via a POST request
    if request.method == "POST":
        # Check if shares and symbol are entered correctly
        if not request.form.get("shares").isdigit() or not request.form.get("symbol") or not request.form.get("shares") or int(request.form.get("shares")) < 1:
            return apology("not a valid amount", code="400")

        # Get the symbol and quantity entered by the user
        symbol = request.form.get("symbol").upper()
        quantity = request.form.get("shares")
        user_id = session["user_id"]

        # Lookup the ticker
        share = lookup(symbol)

        # Ensure the symbol exists
        if not share:
            return apology("symbol not found", 400)

        # Calculate the total price
        total_price = float(share["price"]) * float(quantity)

        # Get the user's current balance
        user = db.execute("SELECT * FROM users WHERE id = :id", id=user_id)
        balance = float(user[0]["cash"])

        # Check if the user has enough money
        if balance < total_price:
            return apology("not enough money", code="400")

        # Calculate the user's remaining balance
        balance_remaining = balance - total_price

        # Check if the user already owns the stock
        shares_owned = db.execute("SELECT * FROM shares WHERE user_id = :user_id AND symbol = :symbol",
                            user_id=user_id, symbol=symbol)

        # Update the user's stock if they already own it
        if len(shares_owned) == 1:
            new_quantity = int(shares_owned[0]["quantity"]) + int(quantity)
            new_total = float(shares_owned[0]["total"]) + total_price
            new_strike = "%.2f"%(new_total / float(new_quantity))
            db.execute("UPDATE shares SET quantity = :quantity, total = :total, strike = :strike WHERE user_id = :user_id AND symbol = :symbol",
                        quantity=new_quantity, total=new_total, strike=new_strike, user_id=user_id, symbol=symbol)

        # If the user does not own the stock, create a new entry in the database
        else:
            db.execute("INSERT INTO shares (user_id, symbol, quantity, total, strike) VALUES (:user_id, :symbol, :quantity, :total, :strike)",
                        user_id=user_id, symbol=symbol, quantity=quantity, total=total_price, strike=share["price"])

        # Update the user's available balance
        db.execute("UPDATE users SET cash = :cash WHERE id = :id", cash=balance_remaining, id=user_id)

        # send a success message
        return render_template("success.html", action="bought", quantity=quantity,
                                name=share["name"], total=usd(total_price), balance=usd(balance_remaining))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("buy.html")



@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Clear sessions
    session.clear()

    # User reaches this route via a POST request
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

     # User reaches this route via a GET request
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))

@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get share quote."""

     # User reaches this route via a POST request
    if request.method == "POST":

        # ensure a symbol was submited
        if not request.form.get("symbol"):
            return apology("no symbol entered", code=400)

        # request share information
        share = lookup(request.form.get("symbol"))

        if not share:
            return apology("symbol not found", code=400)

        return render_template("feed.html", symbol=share["symbol"], name=share["name"], price=usd(share["price"]))

    # User reaches this route via a GET request
    else:
        return render_template("quote.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    #stats = PasswordStats(request.form.get("password"))
    rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))
    # User reaches this route via a POST request
    if request.method == "POST":
         if len(rows) >= 1:
            return apology("Please choose another username, this one is in use.", code=400)
         if not request.form.get("username"):
            return apology("Please enter a username.", code=400)
         elif not request.form.get("password") or not request.form.get("confirmation"):
            return apology("Please enter and confirm your password.", code=400)
         elif request.form.get("password") != request.form.get("confirmation"):
            return apology("Your passwords do not match.", code=400)
         #elif stats.strength() < 0.5:
         #   return apology("Your password strength is " + str(stats.strength()) + " You need a stronger password.")
         else:
            db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)",
                            username=request.form.get("username"), hash=generate_password_hash(request.form.get("password")))

            # thanks and login
            return render_template("registered.html")
    else:
        #How else did you get here?
        print("Something went wrong please try again")
        return render_template("register.html")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of share."""
    shares = db.execute("SELECT * FROM shares WHERE user_id = :user_id", user_id=session["user_id"])

    # User reaches this route via a POST request
    if request.method == "POST":

        # Check for valid entry.
        if not request.form.get("shares").isdigit() or not request.form.get("symbol") or not request.form.get("shares") or int(request.form.get("shares")) < 1:
            return apology("not a valid amount", code="400")


        user_id = session["user_id"]
        symbol = request.form.get("symbol").upper()
        quantity = request.form.get("shares")

        # Retrieve shares owned
        shares_owned = db.execute("SELECT * FROM shares WHERE user_id = :user_id AND symbol = :symbol",
                            user_id=user_id, symbol=symbol)
        if shares_owned:
            shares_owned = shares_owned[0]
        else:
            return render_template("sell.html", shares=shares)

        # Get user information
        user = db.execute("SELECT * FROM users WHERE id = :id", id=user_id)

        # Ensure they own the shares
        if int(quantity) > shares_owned["quantity"]:
            return apology("not enough shares", code="400")

        # Look-up the ticker
        share = lookup(symbol)

        # Calculate total price
        total_price = float(share["price"]) * float(quantity)

        # Update share ownership
        if int(quantity) == shares_owned["quantity"]:
            db.execute("DELETE FROM shares WHERE user_id = :user_id AND symbol = :symbol", user_id=user_id, symbol=symbol)
        else:
            new_quantity = int(shares_owned["quantity"]) - int(quantity)
            new_total = float(new_quantity) * float(shares_owned["strike"])
            db.execute("UPDATE shares SET quantity = :quantity, total = :total WHERE user_id = :user_id AND symbol = :symbol",
                        quantity=new_quantity, total=new_total, user_id=user_id, symbol=symbol)

        # Update balance
        balance_remaining = float(user[0]["cash"]) + total_price
        db.execute("UPDATE users SET cash = :cash WHERE id = :id", cash=balance_remaining, id=user_id)

             # send a success message
        return render_template("success.html", action="sold", quantity=quantity,
                                name=share["name"], total=usd(total_price), balance=usd(balance_remaining))

    # User reaches this route via a GET request
    else:
        return render_template("sell.html", shares=shares)