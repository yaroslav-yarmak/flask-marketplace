import os
from dotenv import load_dotenv

from flask import Flask, render_template, request, redirect, session, flash, url_for
from flask_migrate import Migrate
from werkzeug.utils import secure_filename

from auth_service import authenticate_user, login_user, logout_user, register_user
from models import db, Product, User, Order

load_dotenv()

app = Flask(__name__)

# --- КОНФІГУРАЦІЯ ---
app.secret_key = os.getenv("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Налаштування папки для фото
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Створюємо папку, якщо її немає
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

db.init_app(app)
migrate = Migrate(app, db)

from buyer import buyer_bp
from seller import seller_bp
from admin import admin_bp
from product_service import create_product, delete_product, get_product_by_id, get_products_by_category, get_seller_products, reduce_stock, update_product

app.register_blueprint(buyer_bp)
app.register_blueprint(seller_bp)
app.register_blueprint(admin_bp)

# --- МАРШРУТИ ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role_from_form = request.form.get('role')

        user = authenticate_user(email, password)
        if user:
            redirect_path, error_message = login_user(user, role_from_form)
            if error_message:
                flash(error_message, 'warning' if 'approval' in error_message.lower() else 'danger')
                return redirect('/login')
            return redirect(redirect_path)

        flash('Incorrect email, password or role', 'danger')
        return redirect('/login')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        try:
            register_user(email, password, role)
        except ValueError as exc:
            flash(str(exc), 'danger')
            return redirect('/register')

        flash('Registration successful! Please log in.', 'success')
        return redirect('/login')
    return render_template('register.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect('/login')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)