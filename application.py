import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd
from datetime import datetime
from pytz import timezone
from zoneinfo import ZoneInfo
from datetime import datetime, timezone

# NOTE: To Convert from UTC to ETC, use following query
# SELECT datetime(date||"+04:00") FROM transactions;

globe = {}

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    # Shows the variety of stocks, # of shares owned, current price for stocks, totalt holding values
    # also diplay cash and total net worth of user
    total = 0.00
    global globe
    sold = db.execute("SELECT stk_symbol, SUM(share_quantity) as share_quantity FROM SOLD  WHERE user_id = ? GROUP BY stk_symbol ORDER BY stk_symbol ASC", session["user_id"])
    user_profil = db.execute("SELECT user_id, stk_symbol, SUM(share_quantity) as share_quantity, SUM(paid_amount) FROM transactions WHERE user_id = ? GROUP BY stk_symbol ORDER BY stk_symbol ASC", session["user_id"])
    # print('sold = ', sold)
    # print('user = ', user_profil)
    for x in range(len(sold)):
        for y in range(len(user_profil)):
            if sold[x]['stk_symbol'] == user_profil[y]['stk_symbol']:
                temp = user_profil[y]['share_quantity'] - sold[x]["share_quantity"]
                if temp < 1:
                    del user_profil[y]
                else:
                    user_profil[y]['share_quantity'] = temp
                break
    # print('user = ', user_profil)
    globe = {}
    for y in user_profil:
        globe[y['stk_symbol']] = y['share_quantity']
    # print('globe is ', globe)

    username = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])

    for x in range(len(user_profil)):
        user_profil[x].update(lookup(user_profil[x]['stk_symbol']))
        user_profil[x]['holding'] = user_profil[x]['price'] * user_profil[x]['share_quantity']
        total = total + user_profil[x]['holding']
        user_profil[x]['holding'] = usd(user_profil[x]['holding'])
        user_profil[x]['price'] = usd(user_profil[x]['price'])
    cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
    cash = cash[0]['cash']
    total = cash + total
    return render_template("index.html", username = username, user_profils = user_profil, cash = cash, total = total)


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    purchase = db.execute("SELECT stk_symbol, stk_price, share_quantity, paid_amount as amount, date FROM transactions WHERE user_id = ?", session["user_id"])
    sale = db.execute("SELECT stk_symbol, stk_price, share_quantity, paid_amount as amount, date FROM sold WHERE user_id = ?", session["user_id"])
    # esttime = sale[0]['date']
    # print("datemtime is", esttime)

    for y in purchase:
        buy_time = y['date']
        # print("Time in wrong timezone", y['date'])
        dtobj = datetime.strptime(buy_time, '%Y-%m-%d %H:%M:%S')
        dtobj = dtobj.replace(tzinfo=timezone.utc)
        dtobj = dtobj.astimezone(ZoneInfo('US/Eastern'))
        text = str(dtobj)
        y['date'] = text[0:len(text)-6]
        # print("Time in correct timezone", y['date'])
        # print("\n")

    for x in sale:
        x['share_quantity'] = x['share_quantity'] * -1
        sell_time = x['date']
        # print("Time in wrong timezone", x['date'])
        dtobj = datetime.strptime(sell_time, '%Y-%m-%d %H:%M:%S')
        dtobj = dtobj.replace(tzinfo=timezone.utc)
        dtobj = dtobj.astimezone(ZoneInfo('US/Eastern'))
        text = str(dtobj)
        x['date'] = text[0:len(text)-6]
        # print("Time in correct timezone", x['date'])
        # print("\n")
    # print("purchase is", purchase)
    # print("\n")
    # print("sale =", sale)

    purchase.extend(sale)
    all_trans = sorted(purchase, key=lambda k: k['date'])
    # if not all_trans:

    username = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])

    return render_template("history.html", all_trans = all_trans, username = username)

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == "POST":
        symbol = request.form.get("symbol").upper()
        if not symbol:
            return apology("Please enter Stock symbol", 400)
        prices = {}
        prices = lookup(symbol)
        if prices == None:
            return apology("Not a proper Stock symbol", 400)
        if not request.form.get("shares").isnumeric():
            return apology("Enter a postive integer as share quantity", 400)
        shares_num = int(request.form.get("shares"))
        if shares_num < 1:
            return apology("Enter a postive integer as share quantity", 400)
        stk_price = int(prices['price'])
        total_cost = stk_price * shares_num
        print("total_cost is", total_cost)
        money = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
        new_balance = money[0]['cash'] - total_cost
        print("new_balance is", new_balance)
        if new_balance < 0:
            return apology("Not Enough Funds to Buy", 400)
        db.execute("UPDATE users SET cash = ? WHERE id = ?", new_balance, session["user_id"])
        db.execute("INSERT INTO transactions (user_id, stk_symbol, stk_price, share_quantity, paid_amount) VALUES(?,?,?,?,?)", session["user_id"], symbol, stk_price, shares_num, total_cost)
        return redirect("/")
    return render_template("buy.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    if request.method == "POST":
        stock_symbol = request.form.get("symbol")
        prices = {}
        prices = lookup(stock_symbol)
        if prices == None:
            return apology("Not a proper Stock symbol", 400)
        return render_template("quoted.html", prices=prices)
        # {'name': 'NetFlix Inc', 'price': 510.82, 'symbol': 'NFLX'}
    # """Get stock quote."""
    return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        name = request.form.get("username")
        if not name:
            return apology("must provide username", 400)
        password = request.form.get("password")
        if not password:
            return apology("must provide password", 400)
        confirmation = request.form.get("confirmation")
        if not confirmation:
            return apology("must provide confirmation password", 400)
        if password != confirmation:
            return apology("passwords do not match", 400)
        check_user = db.execute("SELECT * FROM users WHERE username = ?", name)
        if len(check_user) != 0:
            return apology("Username alreadys exists", 400)

        hashed_pass = generate_password_hash(password)
        db.execute("INSERT INTO users (username, hash) VALUES(?,?)", name, hashed_pass)
        return redirect("/")
    return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    # stk_num = {}
    """Sell shares of stock"""
    # stk_symbols = db.execute("SELECT SUM(share_quantity) as shares, stk_symbol FROM transactions WHERE user_id = ? GROUP BY stk_symbol ORDER BY stk_symbol ASC", session["user_id"])

    if request.method == "POST":

        symbol = request.form.get('symbol')
        if not symbol:
            return apology("Please select an option to sell", 400)

        share_quantity = request.form.get('shares')
        if not share_quantity:
            return apology("Please select # of shares to sell", 403)


        shares_left = globe[symbol]

        share_quantity = int(share_quantity)

        if shares_left < share_quantity:
            return apology("Do not own that many shares", 400)

        prices = {}
        prices = lookup(symbol)
        stk_price = int(prices['price'])
        new_cash = stk_price * share_quantity
        shares_left = shares_left - share_quantity
        db.execute("INSERT INTO sold (user_id, stk_symbol, stk_price, share_quantity, paid_amount, type) VALUES (?,?,?,?,?, 'sold')", session["user_id"], symbol, stk_price, share_quantity, new_cash)
        cash_val = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
        insert_cash = cash_val[0]['cash'] + new_cash
        db.execute("UPDATE users SET cash = ? WHERE id = ?", insert_cash, session["user_id"])
        return redirect("/")

    return render_template("sell.html", stk_symbols = globe)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

# Time is wrong
# #time = "Tue, 12 Jun 2012 14:03:10 GMT"

#     # parse to datetime, using %Z for the time zone abbreviation
#     dtobj = datetime.strptime(time, '%Y-%m-%d %H:%M:%S')

#     # note that "GMT" (=UTC) is ignored:
#     # datetime.datetime(2012, 6, 12, 14, 3, 10)

#     # ...so let's correct that:
#     dtobj = dtobj.replace(tzinfo=timezone.utc)
#     # datetime.datetime(2012, 6, 12, 14, 3, 10, tzinfo=datetime.timezone.utc)

#     # convert to US/Eastern (EST or EDT, depending on time of the year)
#     dtobj = dtobj.astimezone(ZoneInfo('US/Eastern'))
#     # datetime.datetime(2012, 6, 12, 10, 3, 10, tzinfo=zoneinfo.ZoneInfo(key='US/Eastern'))
#     print(dtobj)
#     # 2012-06-12 10:03:10-04:00



