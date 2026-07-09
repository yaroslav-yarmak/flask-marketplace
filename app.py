import os
from dotenv import load_dotenv
import os

from flask import Flask, render_template, request, redirect, session, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime

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

db = SQLAlchemy(app)


# --- МОДЕЛІ ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # Обов'язково залишаємо!
    role = db.Column(db.String(20), default='buyer')

    # Поле для верифікації продавців
    is_approved = db.Column(db.Boolean, default=False)

    # Поля для статистики та статусу
    joined_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Active')


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f'<Category {self.name}>'


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    desc = db.Column(db.Text)
    category = db.Column(db.String(50))
    image_file = db.Column(db.String(100), default='default.jpg')
    stock = db.Column(db.Integer, default=10) # Залишаємо один раз
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Це основне поле


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Нові поля з твоєї форми Checkout:
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200), nullable=False)

    status = db.Column(db.String(20), default='Pending')
    date_ordered = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship('Product', backref='orders')
    buyer = db.relationship('User', foreign_keys=[buyer_id], backref='my_orders')

# --- МАРШРУТИ ---

@app.route('/')
def home():
    return redirect('/products')

@app.route('/products')
def products():
    selected_category = request.args.get('category', 'all')
    if selected_category == 'all':
        items = Product.query.all()
    else:
        items = Product.query.filter(Product.category.ilike(selected_category)).all()
    return render_template('products.html', items=items, current_category=selected_category)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role_from_form = request.form.get('role')

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            # 1. Якщо це адмін — пускаємо без питань
            if user.role == 'admin':
                session['user_id'] = user.id
                return redirect('/admin/dashboard')

            # 2. Якщо це продавець — ПЕРЕВІРЯЄМО ПІДТВЕРДЖЕННЯ
            if user.role == 'seller':
                if not user.is_approved:
                    flash('Please wait for admin approval.', 'warning')  # Повідомлення англійською
                    return redirect('/login')

                # Якщо підтверджений і роль збігається
                if role_from_form == 'seller':
                    session['user_id'] = user.id
                    return redirect('/dashboard')

            # 3. Якщо це покупець
            if user.role == 'buyer' and role_from_form == 'buyer':
                session['user_id'] = user.id
                return redirect('/products')

        flash('Incorrect email, password or role', 'danger')
        return redirect('/login')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        if User.query.filter_by(email=email).first():
            flash('This Email is already registered!', 'danger')
            return redirect('/register')
        new_user = User(email=email, password=generate_password_hash(password), role=role)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect('/login')
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect('/login')
    products_list = Product.query.filter_by(seller_id=session['user_id']).all()
    return render_template('dashboard.html', products=products_list)

@app.route('/add-product', methods=['GET', 'POST'])
def add_product():
    if 'user_id' not in session: return redirect('/login')
    if request.method == 'POST':
        # ЛОГІКА ФОТО:
        file = request.files.get('image')
        image_filename = 'default.jpg'
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_filename = filename

        new_product = Product(
            title=request.form.get('title'),
            price=float(request.form.get('price')),
            stock=int(request.form.get('stock')),
            desc=request.form.get('desc'),
            category=request.form.get('category'),
            image_file=image_filename, # Зберігаємо фото
            seller_id=session['user_id']
        )
        db.session.add(new_product)
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect('/dashboard')
    return render_template('add_product.html')


@app.route('/delete-product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    if 'user_id' not in session: return redirect('/login')
    product = Product.query.get(product_id)
    if product.user_id == session['user_id']:
        db.session.delete(product)
        db.session.commit()
    return redirect('/dashboard')

@app.route('/edit-product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if 'user_id' not in session: return redirect('/login')
    product = Product.query.get(product_id)
    if request.method == 'POST':
        product.title = request.form.get('title')
        product.price = request.form.get('price')
        db.session.commit()
        return redirect('/dashboard')
    return render_template('edit_product.html', product=product)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/login')

@app.route('/checkout/<int:product_id>', methods=['GET', 'POST'])
def checkout(product_id):
    if 'user_id' not in session:
        flash('Please log in to buy products', 'warning')
        return redirect('/login')

    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        # Збираємо дані з твоєї форми (image_000953.png)
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        address = request.form.get('address')

        if product.stock <= 0:
            flash('Out of stock!', 'danger')
            return redirect('/products')

        # Створюємо замовлення
        new_order = Order(
            product_id=product.id,
            buyer_id=session['user_id'],
            seller_id=product.seller_id,
            full_name=full_name,
            phone=phone,
            address=address,
            status='Pending'
        )

        product.stock -= 1
        db.session.add(new_order)
        db.session.commit()

        flash('Order confirmed! Seller will contact you.', 'success')
        return redirect('/products')

    return render_template('checkout.html', product=product)


@app.route('/admin/dashboard')
def admin_dashboard():
    # ПЕРЕВІРКА: чи це справді адмін?
    if 'user_id' not in session:
        return redirect('/login')

    current_user = User.query.get(session['user_id'])
    if not current_user or current_user.role != 'admin':
        flash('У вас немає доступу до цієї сторінки!', 'danger')
        return redirect('/')

    # ЗБІР СТАТИСТИКИ
    stats = {
        'total_products': Product.query.count(),
        'total_sellers': User.query.filter_by(role='seller').count(),
        'total_users': User.query.count(),
        'pending_sellers': User.query.filter_by(role='seller', is_approved=False).count()
    }

    return render_template('admin_dashboard.html', stats=stats)


@app.route('/make-me-admin/<email>')
def make_me_admin(email):
    user = User.query.filter_by(email=email).first()
    if user:
        user.role = 'admin'
        user.is_approved = True # Адмін автоматично схвалений
        db.session.commit()
        return f"Користувач {email} тепер Адміністратор!"
    return "Користувача не знайдено", 404


@app.route('/admin/requests')
def admin_requests():
    if 'user_id' not in session:
        return redirect('/login')

    admin = User.query.get(session['user_id'])
    if not admin or admin.role != 'admin':
        # Якщо сесія підмінилася іншим юзером - просимо перелогінитися
        flash('Session expired or access denied. Please login as Admin.', 'danger')
        return redirect('/login')

    pending_sellers = User.query.filter_by(role='seller', is_approved=False).all()
    return render_template('admin_requests.html', sellers=pending_sellers)


@app.route('/admin/approve/<int:user_id>')
def approve_seller(user_id):
    # Перевірка на адміна для безпеки
    admin = User.query.get(session.get('user_id'))
    if not admin or admin.role != 'admin':
        return redirect('/login')

    user = User.query.get_or_404(user_id)
    user.is_approved = True
    db.session.commit()
    flash(f'Seller {user.email} approved successfully!', 'success')
    # ПРАВИЛЬНИЙ РЕДИРЕКТ: повертаємо адміна назад до списку заявок
    return redirect('/admin/requests')

@app.route('/admin/reject/<int:user_id>')
def reject_seller(user_id):
    admin = User.query.get(session.get('user_id'))
    if not admin or admin.role != 'admin':
        return redirect('/login')

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f'Request from {user.email} rejected and account deleted.', 'warning')
    # ПРАВИЛЬНИЙ РЕДИРЕКТ: повертаємо адміна назад до списку заявок
    return redirect('/admin/requests')


@app.route('/buy/<int:product_id>')
def buy_product(product_id):
    if 'user_id' not in session:
        flash('Please log in to make a purchase.', 'warning')
        return redirect('/login')

    user = User.query.get(session['user_id'])
    if user.role != 'buyer':
        flash('Only buyers can purchase products.', 'danger')
        return redirect('/')

    product = Product.query.get_or_404(product_id)

    # Перевірка наявності
    if product.stock <= 0:
        flash('Sorry, this product is out of stock.', 'danger')
        return redirect('/products')

    # Створення замовлення
    new_order = Order(
        product_id=product.id,
        buyer_id=user.id,
        seller_id=product.seller_id,
        status='Pending'
    )

    # Зменшуємо кількість товару на складі
    product.stock -= 1

    db.session.add(new_order)
    db.session.commit()

    flash('Order placed successfully! Check your dashboard.', 'success')
    return redirect('/products')


@app.route('/orders')
def seller_orders():
    # Перевірка, чи користувач залогінений
    if 'user_id' not in session:
        return redirect('/login')

    user = User.query.get(session['user_id'])

    # Перевірка, чи це продавець
    if not user or user.role != 'seller':
        flash('Access denied. Sellers only.', 'danger')
        return redirect('/products')

    # Отримуємо замовлення, де seller_id збігається з id поточного користувача
    orders = Order.query.filter_by(seller_id=user.id).order_by(Order.date_ordered.desc()).all()

    return render_template('seller_orders.html', orders=orders)


@app.route('/update_order/<int:order_id>/<string:status>')
def update_order_status(order_id, status):
    if 'user_id' not in session:
        return redirect('/login')

    order = Order.query.get_or_404(order_id)

    # Дозволяємо змінювати статус тільки власнику товару (продавцю)
    if order.seller_id == session['user_id']:
        order.status = status
        db.session.commit()
        flash(f'Order #{order.id} status updated to {status}!', 'success')
    else:
        flash('You are not authorized to update this order.', 'danger')

    return redirect('/orders')


@app.route('/my-orders')
def my_orders():
    if 'user_id' not in session:
        return redirect('/login')

    # Шукаємо замовлення, де buyer_id збігається з поточним користувачем
    orders = Order.query.filter_by(buyer_id=session['user_id']).order_by(Order.date_ordered.desc()).all()
    return render_template('my_orders.html', orders=orders)


@app.route('/admin/orders')
def admin_all_orders():
    if 'user_id' not in session:
        return redirect('/login')

    user = User.query.get(session['user_id'])

    # Перевірка на роль адміна (припускаємо, що у тебе є роль 'admin')
    if not user or user.role != 'admin':
        flash('Access denied. Admins only.', 'danger')
        return redirect('/products')

    # Отримуємо всі замовлення, сортуємо за новизною
    all_orders = Order.query.order_by(Order.date_ordered.desc()).all()

    return render_template('admin_orders.html', orders=all_orders)

@app.route('/admin/users')
def admin_users():
    # Припускаємо, що твоя модель користувача називається User
    all_users = User.query.all()
    return render_template('admin_users.html', users=all_users)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)