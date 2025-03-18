import json
import urllib
from urllib.parse import urlencode, quote, unquote
from settings import *

import requests
from flask import Flask, request, url_for, render_template, redirect, flash, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import check_password_hash, generate_password_hash
import random
from datetime import date, timedelta
import datetime
from datetime import datetime
from flask_login import LoginManager, login_user, UserMixin, login_required, current_user, logout_user
import locale
import webbrowser

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///digits.sqlite"
app.config["SECRET_KEY"] = 'jcacbaucbascajcjahjcbacjashjahsdhch'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
migrate = Migrate()
migrate.init_app(app, db)

# Set the time limit (48 hours in this example)
time_limit = timedelta(hours=60)


class StartTime(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True)
    start_time = db.Column(db.DateTime, unique=False, nullable=False)

    def __init__(self, start_time):
        self.start_time = start_time

    def __repr__(self):
        return "<StartTime {}>".format(self.start_time)


class Admin(db.Model, UserMixin):
    tablename = 'admin'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    username = db.Column(db.String, unique=False, nullable=False)
    password = db.Column(db.String, unique=False, nullable=False)

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def __repr__(self):
        return "<Admin {}>".format(self.username)


@login_manager.user_loader
def loader_user(username):
    if username is not None:
        return Admin.query.get(username)
    return None


@login_manager.unauthorized_handler
def unauthorized():
    flash("You must be logged in to view this page.")
    return redirect(url_for("index"))


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(url_for('index'))


# @app.route('/timing', methods=['GET', 'POST'])
# def timing():
#     start = StartTime(datetime.now())
#     db.session.add(start)
#     db.session.commit()
#     return jsonify({'msg': 'Success'})


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get("password")
        current_user = Admin.query.filter_by(username=username).first()
        if current_user and current_user.password == password:
            login_user(current_user)
            return redirect(url_for('home', user=current_user))
        else:
            flash("Incorrect Login Credentials")
    return render_template('index.html', APP_NAME=APP_NAME)


@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        password1 = request.form.get('password1')
        if password != password1:
            flash('Password does not match')
        else:
            new_acct = Admin(username, password)
            db.session.add(new_acct)
            db.session.commit()
            flash('Account successfully created. You may now login')
    return render_template('create_account.html', APP_NAME=APP_NAME)


# @app.route('/', methods=['GET', 'POST'])
# def index():
#     if request.method == 'POST':
#         username = request.form.get('username')
#         password = request.form.get("password")
#         current_user = Admin.query.filter_by(username=username).first()
#         if current_user and current_user.password == password:
#             start_time_record = StartTime.query.order_by(StartTime.id.desc()).first()
#             if start_time_record:
#                 start_time = start_time_record.start_time
#                 elapsed_time = datetime.now() - start_time
#                 if elapsed_time > time_limit:
#                     flash("Time limit exceeded. The application is no longer available.")
#                 else:
#                     login_user(current_user)
#                     return redirect(url_for('home', user=current_user))
#             else:
#                 pass
#         else:
#             flash("Incorrect Login Credentials")
#     return render_template('index.html', APP_NAME=APP_NAME)


@app.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    api_url = f"{API_URL}/fetch_total_purchase_price"
    response = requests.get(api_url)
    response = response.json()
    api_end_point = f"{API_URL}/fetch_today_sales"
    resp = requests.get(api_end_point)
    resp = resp.json()
    api = f"{API_URL}/fetch_profit_today"
    res = requests.get(api)
    res = res.json()
    return render_template('home.html', title='ADMIN', total=response['Total'], sales=resp['sales'], cash=resp['cash'],
                           transfer=resp['transfer'], stock=resp['stock'], profit=res['profit'], APP_NAME=APP_NAME)


@app.route('/add_new_product', methods=['GET', 'POST'])
@login_required
def add_new_product():
    if request.method == 'POST':
        pro_name = request.form['pro_name']
        qty = int(request.form['qty'])
        unit_price = float(request.form['unit_price'])
        selling_price = float(request.form['selling_price'])
        date_ojo = request.form['date_ojo']
        purchase_price = float(unit_price * qty)
        details = {'pro_name': pro_name, 'qty': qty, 'unit_price': unit_price, 'selling_price': selling_price,
                   'purchase_price': purchase_price, 'date': date_ojo}
        details = json.dumps(details)
        resp = requests.post(f"{API_URL}/add_new_product", json=details)
        flash('Product Information successfully added')
    return render_template('add_new_product.html', title='ADMIN', APP_NAME=APP_NAME)


@app.route('/view_products', methods=['GET', 'POST'])
@login_required
def view_products():
    if request.method == 'POST':
        data = request.json
        ojo = data.get('ojo')
        details = ojo
        details = json.dumps(details)
        resp = requests.post(f"{API_URL}/total_products_by_date", json=details)
        if resp:
            total = resp.json()['sum']
            return jsonify(total)
    api_url = f"{API_URL}/fetch_product_table"
    response = requests.get(api_url)
    response = response.json()
    api_url = f"{API_URL}/fetch_product_date"
    resp = requests.get(api_url)
    resp = resp.json()
    return render_template('view_products.html', title='ADMIN', items=response, ojo=resp,
                           APP_NAME=APP_NAME, INTERNAL_URL=INTERNAL_URL)


@app.route('/total_products_by_date', methods=['GET', 'POST'])
@login_required
def total_products_by_date():
    api_url = f"{API_URL}/fetch_product_table"
    response = requests.get(api_url)
    response = response.json()
    api_url = f"{API_URL}/fetch_product_date"
    resp = requests.get(api_url)
    resp = resp.json()
    return render_template('view_products.html', title='ADMIN', items=response, ojo=resp, APP_NAME=APP_NAME)


@app.route('/make_sales', methods=['POST', 'GET'])
@login_required
def make_sales():
    if request.method == 'POST':
        data = request.json
        pro = data.get('pro')
        details = pro
        details = json.dumps(details)
        resp = requests.post(f"{API_URL}/fetch_product_price", json=details)
        price = resp.json()['price']
        return jsonify(price)
    api_url = f"{API_URL}/fetch_all_products"
    response = requests.get(api_url)
    target = response.json()
    date_day = datetime.today().strftime('%d-%m-%Y')
    api_add = f"{API_URL}/fetch_ref"
    resp = requests.get(api_add)
    id_no = resp.json()['id_no']
    return render_template('make_sales.html', title='ADMIN', products=target, date_day=date_day, id_no=id_no,
                           APP_NAME=APP_NAME)


@app.route('/filtered_options', methods=['POST'])
@login_required
def filtered_options():
    api_url = f"{API_URL}/fetch_all_products"
    response = requests.get(api_url)
    target = response.json()
    input_text = request.form['input_text'].lower()
    options = target
    filtered_options = [option for option in options if input_text in option.lower()]
    return {'filtered_options': filtered_options}


@app.route('/item_for_sale', methods=['POST', 'GET'])
@login_required
def item_for_sale():
    if request.method == 'POST':
        data = request.json
        details = data
        print(details)
        details = json.dumps(details)
        resp = requests.post(f"{API_URL}/item_for_sale", json=details)
    api_url = f"{API_URL}/fetch_all_products"
    response = requests.get(api_url)
    target = response.json()
    date_day = datetime.today().strftime('%d-%m-%Y')
    api_add = f"{API_URL}/fetch_ref"
    resp = requests.get(api_add)
    id_no = resp.json()['id_no']
    return render_template('make_sales.html', title='ADMIN', products=target, date_day=date_day, id_no=id_no,
                           APP_NAME=APP_NAME)


@app.route('/item_for_removal', methods=['POST', 'GET'])
@login_required
def item_for_removal():
    if request.method == 'POST':
        data = request.json
        details = data
        print(details)
        details = json.dumps(details)
        resp = requests.post(f"{API_URL}/item_for_removal", json=details)
    api_url = f"{API_URL}/fetch_all_products"
    response = requests.get(api_url)
    target = response.json()
    date_day = datetime.today().strftime('%d-%m-%Y')
    api_add = f"{API_URL}/fetch_ref"
    resp = requests.get(api_add)
    id_no = resp.json()['id_no']
    return render_template('make_sales.html', title='ADMIN', products=target, date_day=date_day, id_no=id_no,
                           APP_NAME=APP_NAME)


@app.route('/make_payment', methods=['POST', 'GET'])
@login_required
def make_payment():
    if request.method == 'POST':
        data = request.json
        details = data
        ojo = details['date']
        bill_no = details['bill']
        amount_paid = float(details['amountPaid'])
        total = float(details['total'])
        change = float(amount_paid - total)
        detail = {'date': ojo, 'bill': bill_no, 'total_amount': total, 'amount_paid': amount_paid, 'change': change}
        details = json.dumps(details)
        resp = requests.post(f"{API_URL}/make_payment", json=details)
        res = requests.post(f"{API_URL}/amount_paid", json=detail)
    api_url = f"{API_URL}/fetch_all_products"
    response = requests.get(api_url)
    target = response.json()
    date_day = datetime.today().strftime('%d-%m-%Y')
    api_add = f"{API_URL}/fetch_ref"
    resp = requests.get(api_add)
    id_no = resp.json()['id_no']
    return render_template('make_sales.html', title='ADMIN', products=target, date_day=date_day, id_no=id_no,
                           APP_NAME=APP_NAME)


@app.route('/generate_invoice', methods=['POST', 'GET'])
@login_required
def generate_invoice():
    if request.method == 'POST':
        bill_no = request.form['bill_no']
        # amount_paid = request.form['amount_paid']
        # change = request.form['change']
        dt = date.today()
        dts = dt.strftime("%B %d %Y")
        ojo = dts
        details = {'bill': bill_no}
        details = json.dumps(details)
        response = requests.post(f"{API_URL}/generate_invoice", json=details)
        invoices = response.json()
        # print(invoices)
        # print(invoices[0]['invoice_number'])
        # for item in invoices[1]['items']:
        #     print(item)
        resp = requests.post(f"{API_URL}/total_amount", json=details)
        amount = resp.json()
        res = requests.post(f"{API_URL}/requests_for_amount_paid", json=details)
        amount_paid = res.json()['amount']
        change = res.json()['change']
        return render_template('invoice_template.html', invoices=invoices, ojo=ojo, change=change,
                               amount_paid=amount_paid, amount=amount, bill_no=bill_no, APP_NAME=APP_NAME)
    api_url = f"{API_URL}/fetch_all_products"
    response = requests.get(api_url)
    target = response.json()
    date_day = datetime.today().strftime('%d-%m-%Y')
    api_add = f"{API_URL}/fetch_ref"
    resp = requests.get(api_add)
    id_no = resp.json()['id_no']
    return render_template('make_sales.html', title='ADMIN', products=target, date_day=date_day, id_no=id_no,
                           APP_NAME=APP_NAME)


@app.route('/view_sales', methods=['POST', 'GET'])
@login_required
def view_sales():
    api_end_point = f"{API_URL}/view_sales"
    resp = requests.get(api_end_point)
    sales = resp.json()
    return render_template('view_sales.html', title='ADMIN', sales=sales, APP_NAME=APP_NAME)


@app.route('/previous_sales', methods=['GET', 'POST'])
@login_required
def previous_sales():
    if request.method == 'POST':
        data = request.json
        ojo = data.get('ojo')
        details = ojo
        details = json.dumps(details)
        resp = requests.post(f"{API_URL}/view_sales_by_date", json=details)
        return jsonify(resp.json())
    api_url = f"{API_URL}/fetch_sales_by_date"
    resp = requests.get(api_url)
    resp = resp.json()
    return render_template('previous_sales.html', title='ADMIN', ojo=resp, APP_NAME=APP_NAME)


@app.route('/regenerate_receipt', methods=['GET', 'POST'])
@login_required
def regenerate_receipt():
    if request.method == 'POST':
        data = request.json
        ojo = data.get('ojo')
        details = ojo
        details = json.dumps(details)
        resp = requests.post(f"{API_URL}/view_bill_by_date", json=details)
        return jsonify(resp.json())
    api_url = f"{API_URL}/fetch_bill_by_date"
    resp = requests.get(api_url)
    resp = resp.json()
    return render_template('regenerate_receipt.html', title='ADMIN', ojo=resp, APP_NAME=APP_NAME)


@app.route('/regenerate_invoice', methods=['POST', 'GET'])
@login_required
def regenerate_invoice():
    if request.method == 'POST':
        data = request.json
        details = data
        response = requests.post(f"{API_URL}/regenerate_invoice", json=details)
        invoices = response.json()
        return invoices


@app.route('/invoice_template', methods=['GET', 'POST'])
@login_required
def invoice_template():
    data_param = request.args.get('data')  # Retrieve the data from the query parameter
    data = json.loads(urllib.parse.unquote(data_param))  # Deserialize the data
    ojo = data[0]['date']

    details = {'bill': data[1]['invoice_number']}
    resp = requests.post(f"{API_URL}/total_amounts", json=details)
    response = requests.post(f"{API_URL}/request_for_amount_paid", json=details)
    amount = resp.json()
    amount_paid = response.json()['amount']
    change = response.json()['change']
    return render_template('invoice_template.html', invoices=data, amount=amount, ojo=ojo, amount_paid=amount_paid,
                           change=change, APP_NAME=APP_NAME)


@app.route('/stock_manager', methods=['GET', 'POST'])
@login_required
def stock_manager():
    api_url = f"{API_URL}/fetch_stock"
    response = requests.get(api_url)
    response = response.json()
    return render_template('stock_manager.html', open_stock=response, APP_NAME=APP_NAME)


@app.route('/add_stock', methods=['GET', 'POST'])
@login_required
def add_stock():
    if request.method == 'POST':
        pro_name = request.form['pro_name']
        qty = int(request.form['qty'])
        unit_price = float(request.form['unit_price'])
        selling_price = float(request.form['selling_price'])
        date_ojo = request.form['date_ojo']
        purchase_price = float(unit_price * qty)
        details = {'pro_name': pro_name, 'qty': qty, 'unit_price': unit_price, 'selling_price': selling_price,
                   'purchase_price': purchase_price, 'date': date_ojo}
        details = json.dumps(details)
        resp = requests.post(f"{API_URL}/add_new_product", json=details)
        flash('Product Information successfully Updated')
    api_url = f"{API_URL}/fetch_all_products"
    response = requests.get(api_url)
    target = response.json()
    return render_template('add_stock.html', products=target, APP_NAME=APP_NAME)


@app.route('/adjust_price', methods=['GET', 'POST'])
@login_required
def adjust_price():
    if request.method == 'POST':
        pro_name = request.form['pro_name']
        new_price = request.form['new_price']
        details = {'pro_name': pro_name, 'new_price': new_price}
        details = json.dumps(details)
        response = requests.post(f"{API_URL}/adjust_price", json=details)
        flash('Product price successfully Updated')
    api_url = f"{API_URL}/fetch_all_products"
    response = requests.get(api_url)
    target = response.json()
    return render_template('adjust_price.html', products=target, APP_NAME=APP_NAME)


@app.route('/view_stock', methods=['GET', 'POST'])
@login_required
def view_stock():
    api_url = f"{API_URL}/fetch_supermarket_table"
    response = requests.get(api_url)
    avail_stock = response.json()
    return render_template('view_stock.html', stock=avail_stock, APP_NAME=APP_NAME)


@app.route('/return_goods', methods=['POST', 'GET'])
@login_required
def return_goods():
    data_param = request.args.get('data')  # Retrieve the data from the query parameter
    data = json.loads(urllib.parse.unquote(data_param))  # Deserialize the data
    print(data)

    ojo = data[0]['date']
    details = {'bill': data[0]['invoice_number']}
    ref_no = data[0]['invoice_number']
    resp = requests.post(f"{API_URL}/total_amounts", json=details)
    response = requests.post(f"{API_URL}/request_for_amount_paid", json=details)
    amount = resp.json()
    amount_paid = response.json()['amount']
    change = response.json()['change']
    return render_template('return_goods.html', invoices=data, amount=amount, ojo=ojo, amount_paid=amount_paid,
                           change=change, ref_no=ref_no, APP_NAME=APP_NAME)


@app.route('/returned_items', methods=['POST', 'GET'])
@login_required
def returned_items():
    if request.method == 'POST':
        data = request.json
        details = data
        # response = requests.post(f"{API_URL}/returned_items", json=details)
        # invoices = response.json()
        # print(invoices)
        # return invoices


@app.route('/create_user', methods=['GET', 'POST'])
@login_required
def create_user():
    if request.method == 'POST':
        rep = request.form['rep']
        name = request.form['name']
        username = request.form['username']
        mobile = request.form['mobile']
        email = request.form['email']
        password = request.form['password']
        details = {'rep': rep, 'name': name, 'username': username, 'mobile': mobile, 'email': email,
                   'password': password}
        details = json.dumps(details)
        response = requests.post(f"{USER_SERVER}/create_user", json=details)
        flash(f"{response.json()['msg']}")
    return render_template('create_user.html', APP_NAME=APP_NAME)


@app.route('/block_user', methods=['GET', 'POST'])
@login_required
def block_user():
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        details = username
        details = json.dumps(details)
        response = requests.post(f"{USER_SERVER}/block_user", json=details)
        print(response.json())
        return jsonify(flash(f"{response.json()['msg']}"))


@app.route('/activate_user', methods=['GET', 'POST'])
@login_required
def activate_user():
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        details = username
        details = json.dumps(details)
        response = requests.post(f"{USER_SERVER}/activate_user", json=details)
        print(response.json())
        return jsonify(flash(f"{response.json()['msg']}"))


@app.route('/delete_user', methods=['GET', 'POST'])
@login_required
def delete_user():
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        details = username
        details = json.dumps(details)
        response = requests.post(f"{USER_SERVER}/delete_user", json=details)
        print(response.json())
        return jsonify(flash(f"{response.json()['msg']}"))


@app.route('/reset_password', methods=['GET', 'POST'])
@login_required
def reset_password():
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        details = username
        details = json.dumps(details)
        response = requests.post(f"{USER_SERVER}/reset_password", json=details)
        print(response.json())
        sales_rep = response.json()
        return sales_rep


@app.route('/password_reset', methods=['GET', 'POST'])
@login_required
def password_reset():
    data_param = request.args.get('data')  # Retrieve the data from the query parameter
    data = json.loads(urllib.parse.unquote(data_param))  # Deserialize the data

    return render_template('password_reset.html', data=data, APP_NAME=APP_NAME)


@app.route('/reset_pswd', methods=['GET', 'POST'])
@login_required
def reset_pswd():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['old_password']
        new_password = request.form['new_password']
        conf_password = request.form['new_password1']
        if new_password != conf_password:
            detail = username
            detail = json.dumps(detail)
            resp = requests.post(f"{USER_SERVER}/reset_password", json=detail)
            data = resp.json()
            flash('New Password & Confirm New Password do not match')
            return render_template('password_reset.html', data=data, APP_NAME=APP_NAME)
        else:
            details = {'username': username, 'password': password, 'new_pswd': new_password, 'new_pswd1': conf_password}
            details = json.dumps(details)
            response = requests.post(f"{USER_SERVER}/reset_pswd", json=details)
            flash(f"{response.json()['msg']}")
    return redirect(url_for('view_users'))


@app.route('/view_users', methods=['GET', 'POST'])
@login_required
def view_users():
    api_url = f"{USER_SERVER}/fetch_users"
    response = requests.get(api_url)
    users = response.json()
    return render_template('view_users.html', users=users, APP_NAME=APP_NAME)


@app.route('/user_sales_act', methods=['GET', 'POST'])
@login_required
def user_sales_act():
    if request.method == 'POST':
        data = request.json
        ojo = data.get('ojo')
        details = ojo
        details = json.dumps(details)
        resp = requests.post(f"{API_URL}/view_rep_sales_date", json=details)
        return jsonify(resp.json())
    api_url = f"{API_URL}/fetch_rep_sales_date"
    resp = requests.get(api_url)
    resp = resp.json()
    return render_template('user_sales_act.html', title='ADMIN', ojo=resp, APP_NAME=APP_NAME)


@app.route('/sales_rep_proceeds', methods=['GET', 'POST'])
@login_required
def sales_rep_proceeds():
    api_url = f"{API_URL}/fetch_rep_sales_proceeds"
    resp = requests.get(api_url)
    items = resp.json()
    print(items)
    return render_template('sales_rep_proceeds.html', title='ADMIN', items=items, APP_NAME=APP_NAME)


@app.route('/admin_change_password', methods=['GET', 'POST'])
def admin_change_password():
    if request.method == 'POST':
        old_user = request.form.get('old_username')
        old_pass = request.form.get('old_password')
        new_user = request.form.get('username')
        new_pass1 = request.form.get('password1')
        new_pass2 = request.form.get('password2')
        details_check = Admin.query.filter_by(username=old_user, password=old_pass).first()
        if details_check:
            if new_pass1 == new_pass2:
                details_check.username = new_user
                details_check.password = new_pass1
                db.session.add(details_check)
                db.session.commit()
                flash('Login Credentials Successfully Changed')
                return redirect(url_for('index'))
            else:
                flash('New Password Does Not Match.')
                return render_template('admin_change_password.html', APP_NAME=APP_NAME)
        else:
            flash('Incorrect Old Login Credential.')
            return render_template('admin_change_password.html', APP_NAME=APP_NAME)
    return render_template('admin_change_password.html', APP_NAME=APP_NAME)


with app.app_context():
    db.create_all()

# webbrowser.open('http://127.0.0.1:5000', new=1)
if __name__ == '__main__':
    app.run(debug=True, port=5000)
