import os
import io
import base64
import pandas as pd
import matplotlib.pyplot as plt
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash
)
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy

# Flask app setup
app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = 'replace_with_a_strong_random_key'
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# User model for persistent storage
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    firstname = db.Column(db.String(120), nullable=False)
    lastname = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

# Create tables
with app.app_context():
    db.create_all()

# Upload folder for CSVs
datasrc = 'uploads'
os.makedirs(datasrc, exist_ok=True)
app.config['UPLOAD_FOLDER'] = datasrc

# Data loading function
def load_data(transactions_path, households_path, products_path):
    tx = pd.read_csv(transactions_path)
    hh = pd.read_csv(households_path)
    pr = pd.read_csv(products_path)
    tx.columns = tx.columns.str.strip()
    hh.columns = hh.columns.str.strip()
    pr.columns = pr.columns.str.strip()
    if 'PURCHASE_' in tx.columns:
        tx = tx.rename(columns={'PURCHASE_': 'PURCHASE_DATE'})
    df = tx.merge(pr, on='PRODUCT_NUM', how='inner') \
           .merge(hh, on='HSHD_NUM', how='inner')
    hs = df['HH_SIZE'].astype(str).str.strip().replace({'null':'0','5+':'5'})
    df['HH_SIZE'] = hs.astype(int)
    df['SPEND'] = df['SPEND'].astype(float)
    return df.sort_values([
        'HSHD_NUM','BASKET_NUM','PURCHASE_DATE',
        'PRODUCT_NUM','DEPARTMENT','COMMODITY'
    ])

# Initial data load
final_df = load_data(
    './../8451_The_Complete_Journey_2_Sample-2-1/8451_The_Complete_Journey_2_Sample-2/400_transactions.csv',
    './../8451_The_Complete_Journey_2_Sample-2-1/8451_The_Complete_Journey_2_Sample-2/400_households.csv',
    './../8451_The_Complete_Journey_2_Sample-2-1/8451_The_Complete_Journey_2_Sample-2/400_products.csv'
)

# Plot helper
def generate_plot(df):
    basket = df.groupby(['HSHD_NUM','BASKET_NUM']).agg({'HH_SIZE':'first','SPEND':'sum'}).reset_index()
    agg = basket.groupby('HSHD_NUM').agg({'HH_SIZE':'first','SPEND':'sum'}).query('HH_SIZE>0')
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

# Correlation helper
def calculate_correlation(df):
    basket = df.groupby(['HSHD_NUM','BASKET_NUM']).agg({'HH_SIZE':'first','SPEND':'sum'}).reset_index()
    agg = basket.groupby('HSHD_NUM').agg({'HH_SIZE':'first','SPEND':'sum'}).query('HH_SIZE>0')
    return agg['HH_SIZE'].corr(agg['SPEND'])

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        uname = request.form['username']
        if User.query.filter_by(username=uname).first():
            flash('Username already exists','danger')
        else:
            user = User(
                username=uname,
                password=request.form['password'],
                firstname=request.form['firstname'],
                lastname=request.form['lastname'],
                email=request.form['email']
            )
            db.session.add(user)
            db.session.commit()
            flash('Registration successful. Please log in.','success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        uname = request.form['username']
        pwd = request.form['password']
        user = User.query.filter_by(username=uname, password=pwd).first()
        if user:
            session['username'] = uname
            return redirect(url_for('success', username=uname))
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
        fn = secure_filename(f.filename)
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
    if 'username' not in session or session['username'] != username:
        return redirect(url_for('login'))
    user = User.query.filter_by(username=username).first()
    plot_data = generate_plot(final_df)
    corr = calculate_correlation(final_df)
    hshd_10 = final_df.query('HSHD_NUM==10')
    num = request.form.get('hshd_num', type=int, default=1)
    filtered = final_df.query('HSHD_NUM==@num')
    return render_template(
        'success.html',
        user_info=user,
        plot_data=plot_data,
        correlation=corr,
        hshd_10_df=hshd_10,
        filtered_df=filtered
    )

@app.route('/notebook')
def notebook():
    return render_template('notebook_view.html')

if __name__ == '__main__':
    app.run(debug=True)
