from flask import *
from functools import wraps
import sqlite3 as lite
import re
import smtplib

DATABASE = '/home/wcm/dhsstore/data.db'

app = Flask(__name__)
app.config.from_object(__name__)

app.secret_key = 'my precious'

def connect_db():
    return lite.connect(app.config['DATABASE'])

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
        return username and USER_RE.match(username)

PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
        return password and PASS_RE.match(password)

EMAIL_RE = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
def valid_email(email):
        return email and EMAIL_RE.match(email)

def gethot(items):
    hot = [0 for i in range(5)]
    hotid = [(i+1) for i in range(5)]
    for item in items:
        i = 3
        while int(hot[i])<= int(item['like']) and i >= 0:
            hot[i+1] = hot[i]
            hot[i] = item['like']
            hotid[i+1] = hotid[i]
            hotid[i] = item['id']
            i-=1
    return hotid

@app.route('/', methods=['GET', 'POST'])
def home():
    g.db = connect_db()
    cur = g.db.execute('select name, prize, id, like from items')
    items = [dict(like = row[3], name = row[0], prize = row[1], id = row[2]) for row in cur.fetchall()]
    hot = gethot(items)
    if 'user' in session:
        login = True
        if request.method == 'POST':
            cur = g.db.execute("select cart from users where id= '%s'"%session['user'])
            l = cur.fetchone()[0]
            list = []
            for tup in l.split(" "):
                quantitys, totals = tup.split(":")
                quantity = int(quantitys)
                total = float(totals)
                list.append((quantity, total))
            i = 0
            for item in items:
                i += 1
                if request.form[str(i)] != '0':
                    list[i-1] = (list[i-1][0]+int(request.form[str(i)]), list[i-1][1]+int(request.form[str(i)])*item['prize'])
                strList = ""
            for item in list:
                strList += "{}:{} ".format(str(item[0]), str(item[1]))
            strList = strList[:-1]
            cur = g.db.execute("update users set cart = '%s' where id= '%s'"%(strList, session['user']))
            g.db.commit()
            flash('Your order has been added to your cart.')
        return render_template('sales.html', items = items, select = 'home', login = login, hot = hot)
    else:
        login = False
        return render_template('home.html', items = items, select = 'home', login = login)
    g.db.close

@app.route('/log', methods=['GET', 'POST'])
def log():
    error = None
    if request.method == 'POST':
        g.db = connect_db()
        username = request.form['username']
        cur = g.db.execute("SELECT password FROM users WHERE id = '%s'" %username)
        password = cur.fetchone()
        if password == None:
            error = 'User does not exist.';
        elif str(hash(request.form['password'])) != password[0]:
            error = 'Incorrect password, try again.'
        else:
            session['user'] = request.form['username']
            return redirect('/')
    return render_template('log.html', error=error, select = 'log')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    if request.method =='POST':
        g.db = connect_db()
        username = request.form['username']
        password = request.form['password']
        repass = request.form['repass']
        email = request.form['email']
        cur = g.db.execute("SELECT * FROM users WHERE id = '%s'" %username)
        check = cur.fetchone()
        if valid_username(username) and valid_password(password) and valid_email(email) and check == None and password == repass:
            defaultcart = '0:0 0:0 0:0 0:0 0:0 0:0 0:0 0:0 0:0 0:0 0:0 0:0 0:0 0:0 0:0 0:0 0:0 0:0 0:0 0:0'
            g.db.execute('insert into users (id, password, status, email, cart, like) values (?, ?, 0, ?, ?, 0)',[username, hash(password), email, defaultcart])
            g.db.commit()
            flash('You have signed up successfully.')
            session['user'] = request.form['username']
            return render_template('signup.html', signup = True, select = 'log')
        else:
            error = 'There is an error'
        g.db.close
    return render_template('signup.html', error=error, select = 'log')

def login_required(test):
    @wraps(test)
    def wrap(*args, **kwargs):
        if 'user' in session:
            return test(*args, **kwargs)
        else:
            flash('You need to login first.')
            return redirect(url_for('log'))
    return wrap

def get_cart(l):
    cart = []
    for tup in l.split(" "):
        quantitys, totals = tup.split(":")
        quantity = int(quantitys)
        total = float(totals)
        cart.append((quantity, total))
    return cart
@app.route('/cart', methods=['GET', 'POST'])
@login_required
def cart():
    g.db  = connect_db()
    user = session['user']
    cur = g.db.execute("select cart from users where id ='%s'"%session['user'])
    l = cur.fetchone()[0]
    cart = get_cart(l)
    cur = g.db.execute('select name, prize, id from items')
    items = [dict(name = row[0], prize = row[1], id = row[2]) for row in cur.fetchall()]
    if request.method =='POST':
        cur = g.db.execute("select email from users where id ='%s'"%session['user'])
        mail = cur.fetchone()[0]
        FROM = 'dstore@dhs.sg'
        TO = [mail, 'wu.chenmu@dhs.sg']
        SUBJECT = "D'Store Purchase List"
        TEXT = str(cart)
        message = """\
From: %s
To: %s
Subject: %s

%s
""" % (FROM, ", ".join(TO), SUBJECT, TEXT)
        try:
            server = smtplib.SMTP('www.gmail.com')
            server.sendmail(FROM, TO, message)
            server.quit()
            status = 'Purchase successfully.'
        except Exception, error:
            status = "Purchase successfully.                                       %s." % str(error)
        defaultcart = '0:0 0:0 0:0 0:0 0:0 0:0 0:0 0:0 0:0 0:0 0:0 0:0 0:0 0:0 0:0 0:0 0:0 0:0 0:0 0:0'
        cur = g.db.execute("update users set cart = '%s' where id='%s'" %(defaultcart, session['user']))
        cart = get_cart(defaultcart)
        g.db.commit()
        flash(status)
    g.db.close()
    total = 0
    for item in cart:
        total = total + item[1]
    return render_template('hello.html', cart = cart, items = items, login = True, select = 'cart', user = user, total = total)

@app.route('/deleteorder/<user_id>',)
@login_required
def delete_order(user_id):
    g.db  = connect_db()
    defaultcart = '0:0 0:0 0:0 0:0 0:0 0:0 0:0 0:0 0:0 0:0 0:0 0:0 0:0 0:0 0:0 0:0 0:0 0:0 0:0 0:0'
    g.db.execute("update users set cart = '%s' where id='%s'" %(defaultcart, session['user']))
    g.db.commit()
    g.db.close()
    flash('The order has been deleted.')
    return redirect(url_for('cart'))

@app.route('/like/<item_id>',)
@login_required
def like(item_id):
    g.db = connect_db()
    cur = g.db.execute("select like from users where id ='%s'"%session['user'])
    curr =int(cur.fetchone()[0])
    if curr >= 3:
        flash('You can only like 3 times everytime you logged in.')
    else:
        cur = g.db.execute("update users set like = '%s' where id= '%s'"%(str(curr+1), session['user']))
        cur = g.db.execute("select like from items where id= '%s'"%item_id)
        like = cur.fetchone()[0]
        cur = g.db.execute("update items set like = '%s' where id= '%s'"%(str(int(like)+1), item_id))
    g.db.commit()
    g.db.close()
    return redirect('/')

@app.route('/account', methods=['GET', 'POST'])
@login_required
def get_user():
    g.db  = connect_db()
    cur = g.db.execute("select * from users where id ='%s'"%session['user'])
    info =cur.fetchone()
    g.db.close()
    return render_template('account.html', info=  info, login = True, select = 'account')

@app.route('/logout')
def logout():
    g.db = connect_db()
    g.db.execute("update users set like = '%s' where id= '%s'"%('0', session['user']))
    g.db.commit()
    g.db.close()
    session.pop('user', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
