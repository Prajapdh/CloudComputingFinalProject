# flaskapp.py

import os
import io
import base64
import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash
)
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy

# ─── Flask + Auth-DB (SQLite) ────────────────────────────────────────────────
app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = os.environ.get(
    'SECRET_KEY',
    'replace_with_a_strong_random_key'
)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = (
    'sqlite:///' + os.path.join(basedir, 'users.db')
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ─── Uploads folder for CSV fallback ─────────────────────────────────────────
UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ─── Cloud-SQL Analytics Engine ─────────────────────────────────────────────
DB_USER = os.environ.get('DB_USER', 'admin')
DB_PASS = os.environ.get('DB_PASS', 'admin')
DB_HOST = os.environ.get('DB_HOST', '34.45.4.119')
DB_PORT = os.environ.get('DB_PORT', '3306')
DB_NAME = os.environ.get('DB_NAME', '400_transactions')
ANALYTICS_URI = (
    f"mysql+pymysql://{DB_USER}:{DB_PASS}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
analytics_engine = create_engine(ANALYTICS_URI)


# ─── Models ───────────────────────────────────────────────────────────────────
class User(db.Model):
    __tablename__ = 'user'
    id        = db.Column(db.Integer,  primary_key=True)
    username  = db.Column(db.String(80), unique=True, nullable=False)
    password  = db.Column(db.String(128), nullable=False)
    firstname = db.Column(db.String(120), nullable=False)
    lastname  = db.Column(db.String(120), nullable=False)
    email     = db.Column(db.String(120), unique=True, nullable=False)


with app.app_context():
    db.create_all()  # only creates the SQLite tables


# ─── CSV‐based loader (for /upload fallback) ─────────────────────────────────
def load_data(tx_path, hh_path, pr_path):
    tx = pd.read_csv(tx_path)
    hh = pd.read_csv(hh_path)
    pr = pd.read_csv(pr_path)

    tx.columns = tx.columns.str.strip()
    hh.columns = hh.columns.str.strip()
    pr.columns = pr.columns.str.strip()

    if 'PURCHASE_' in tx.columns:
        tx = tx.rename(columns={'PURCHASE_': 'PURCHASE_DATE'})

    df = (
        tx
        .merge(pr, on='PRODUCT_NUM', how='inner')
        .merge(hh, on='HSHD_NUM',   how='inner')
    )

    hs = (
        df['HH_SIZE']
        .astype(str)
        .str.strip()
        .replace({'null':'0','5+':'5'})
        .astype(int)
    )
    df['HH_SIZE'] = hs
    df['SPEND']   = df['SPEND'].astype(float)

    return df.sort_values([
        'HSHD_NUM','BASKET_NUM','PURCHASE_DATE',
        'PRODUCT_NUM','DEPARTMENT','COMMODITY'
    ])


# ─── SQL-based loader ─────────────────────────────────────────────────────────
def load_data_from_sql():
    tx = pd.read_sql_table('transactions',   analytics_engine)
    hh = pd.read_sql_table('households',     analytics_engine)
    pr = pd.read_sql_table('products',       analytics_engine)

    tx = tx.rename(columns={
        'HSHD_NU':     'HSHD_NUM',
        'BASKET_N':    'BASKET_NUM',
        'PURCHASE_':   'PURCHASE_DATE',
        'PRODUCT_':    'PRODUCT_NUM'
    })

    tx.columns = tx.columns.str.strip()
    hh.columns = hh.columns.str.strip()
    pr.columns = pr.columns.str.strip()

    df = (
        tx
        .merge(pr, on='PRODUCT_NUM', how='inner')
        .merge(hh, on='HSHD_NUM',   how='inner')
    )

    hs = (
        df['HH_SIZE']
        .astype(str)
        .str.strip()
        .replace({'null':'0','5+':'5'})
        .astype(int)
    )
    df['HH_SIZE'] = hs
    df['SPEND']   = df['SPEND'].astype(float)

    return df.sort_values([
        'HSHD_NUM','BASKET_NUM','PURCHASE_DATE',
        'PRODUCT_NUM','DEPARTMENT','COMMODITY'
    ])


# initial load: prefer SQL, fallback to CSV if it fails
try:
    final_df = load_data_from_sql()
except Exception as e:
    app.logger.warning(f"SQL load failed, falling back to CSV: {e}")
    # point these at real CSVs if you need to bootstrap:
    #final_df = load_data(
    #    '../8451_The_Complete_Journey_2_Sample-2/400_transactions.csv',
    #    '../8451_The_Complete_Journey_2_Sample-2/400_households.csv',
    #    '../8451_The_Complete_Journey_2_Sample-2/400_products.csv'
    #)


# ─── Plot & correlation helpers ───────────────────────────────────────────────
def generate_plot(df):
    basket = (
        df.groupby(['HSHD_NUM','BASKET_NUM'])
          .agg({'HH_SIZE':'first','SPEND':'sum'})
          .reset_index()
    )
    agg = (
        basket.groupby('HSHD_NUM')
              .agg({'HH_SIZE':'first','SPEND':'sum'})
              .query('HH_SIZE>0')
    )

    plt.figure(figsize=(8,5))
    plt.scatter(agg['HH_SIZE'], agg['SPEND'], alpha=0.6)
    plt.title('Household Size vs Total Spend')
    plt.xlabel('Household Size')
    plt.ylabel('Total Spend')
    plt.grid(True)

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode()


def calculate_correlation(df):
    basket = (
        df.groupby(['HSHD_NUM','BASKET_NUM'])
          .agg({'HH_SIZE':'first','SPEND':'sum'})
          .reset_index()
    )
    agg = (
        basket.groupby('HSHD_NUM')
              .agg({'HH_SIZE':'first','SPEND':'sum'})
              .query('HH_SIZE>0')
    )
    return agg['HH_SIZE'].corr(agg['SPEND'])


# ─── Routes ───────────────────────────────────────────────────────────────────
@app.route('/')
def home():
    return render_template('home.html')


@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        if User.query.filter_by(username=request.form['username']).first():
            flash('Username already exists', 'danger')
        else:
            u = User(
                username = request.form['username'],
                password = request.form['password'],
                firstname= request.form['firstname'],
                lastname = request.form['lastname'],
                email    = request.form['email']
            )
            db.session.add(u)
            db.session.commit()
            flash('Registration successful. Please log in.','success')
            return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        user = User.query.filter_by(
            username=request.form['username'],
            password=request.form['password']
        ).first()
        if user:
            session['username'] = user.username
            return redirect(url_for('success', username=user.username))
        flash('Invalid credentials','danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


@app.route('/upload', methods=['POST'])
def upload():
    if 'username' not in session:
        return redirect(url_for('login'))

    files = {}
    for key in ['transactions_file','households_file','products_file']:
        f = request.files.get(key)
        if not f:
            flash(f'Missing file: {key}','danger')
            return redirect(url_for('success', username=session['username']))
        fn   = secure_filename(f.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], fn)
        f.save(path)
        files[key] = path

    global final_df
    final_df = load_data(
        files['transactions_file'],
        files['households_file'],
        files['products_file']
    )
    flash('Files uploaded successfully','success')
    return redirect(url_for('success', username=session['username']))

@app.route('/success/<username>', methods=['GET','POST'])
def success(username):
    if session.get('username') != username:
        return redirect(url_for('login'))

    # load fresh from Cloud SQL
    df = load_data_from_sql()

    # *new* — log how many rows came back
    app.logger.info(f"load_data_from_sql() returned DataFrame with shape: {df.shape}")

    # now generate your plot, correlation, filters, etc.
    plot_data   = generate_plot(df)
    corr        = calculate_correlation(df)
    # use the first household in the data as a default, not hard-coded “1”
    first_hshd  = int(df['HSHD_NUM'].min())
    num         = request.form.get('hshd_num', type=int, default=first_hshd)
    filtered_df = df.query('HSHD_NUM == @num')
    user        = User.query.filter_by(username=username).first()

    return render_template(
        'success.html',
        user_info   = user,
        plot_data   = plot_data,
        correlation = corr,
        # pass both the list of households and the currently‐selected one
        hshd_list   = sorted(df['HSHD_NUM'].unique()),
        selected_hshd = num,
        filtered_df = filtered_df
    )


@app.route('/notebook')
def notebook():
    return render_template('notebook_view.html')


if __name__ == '__main__':
    app.run(debug=True)
