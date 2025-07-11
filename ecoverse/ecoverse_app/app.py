from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import pandas as pd

# Flask app setup
app = Flask(__name__)
app.secret_key = 'spidey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecoverse.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
db = SQLAlchemy(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))  # Full name
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    points = db.Column(db.Integer, default=0)

# Create DB
with app.app_context():
    db.create_all()

# Home -> redirect to login
@app.route('/')
def home():
    return redirect(url_for('login'))

# Signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        if User.query.filter_by(email=email).first():
            flash('Email already exists.')
            return redirect(url_for('signup'))

        hashed_pw = generate_password_hash(password)
        new_user = User(name=name, email=email, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        flash('Signup successful! Please login.')
        return redirect(url_for('login'))

    return render_template('signup.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password_input = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password_input):
            session['user_id'] = user.id
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password')
            return redirect(url_for('login'))

    return render_template('login.html')

# Dashboard
@app.route('/index')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    return render_template('index.html', user=user)

# View Points
@app.route('/view_points')
def view_points():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    return render_template('view_points.html', user=user)

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.')
    return redirect(url_for('login'))

# PlastiLoop (1 point for upload)
@app.route("/plastiloop", methods=["GET", "POST"])
def plastiloop():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == "POST":
        image = request.files.get("image")  
        location = request.form.get("location")
        time = request.form.get("time")

        # ✅ Server-side validation
        if not image or not image.filename or not location or not time:
            flash("All fields are required to submit!")
            return redirect(url_for("plastiloop"))

        # Save uploaded image
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
        image.save(image_path)

        # Save to Excel
        os.makedirs("data", exist_ok=True)
        excel_path = "data/plastiloop_data.xlsx"

        df = pd.DataFrame([[image.filename, location, time]], columns=["Image", "Location", "Time"])
        if os.path.exists(excel_path):
            df_existing = pd.read_excel(excel_path)
            df = pd.concat([df_existing, df], ignore_index=True)
        df.to_excel(excel_path, index=False)

        # ✅ Update user points only if valid
        user = User.query.get(session['user_id'])
        user.points += 1
        db.session.commit()

        return redirect("/view_points")

    return render_template("plastiloop.html")
# EcoTap (10 points for tap)
@app.route("/ecotap", methods=["GET", "POST"])
def ecotap():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == "POST":
        location = request.form.get("location")
        time = request.form.get("time")

        # ✅ Server-side validation
        if not location or not time:
            flash("Please fill in all fields.")
            return redirect(url_for("ecotap"))

        # Save to Excel
        os.makedirs("data", exist_ok=True)
        excel_path = "data/ecotap_data.xlsx"

        df = pd.DataFrame([[location, time]], columns=["Location", "Time"])
        if os.path.exists(excel_path):
            df_existing = pd.read_excel(excel_path)
            df = pd.concat([df_existing, df], ignore_index=True)
        df.to_excel(excel_path, index=False)

        # ✅ Update user points only if valid
        user = User.query.get(session['user_id'])
        user.points += 10
        db.session.commit()

        return redirect("/view_points")

    return render_template("ecotap.html")
# Prevent caching (optional for dev)
@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store'
    return response

@app.route('/rechargebox')
def rechargebox():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('rechargebox.html')

@app.route('/rechargebox/confirm')
def rechargebox_confirm():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    user.points += 2
    db.session.commit()
    flash("✅ 2 Eco Points added for e-waste logging!")
    return redirect(url_for('view_points'))


@app.route('/about')
def about_ecoverse():
    return render_template('about_ecoverse.html')




# Run the server
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
