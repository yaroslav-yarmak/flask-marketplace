from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session

from models import Order, Product, User, db
from order_service import get_seller_orders as get_seller_orders_service
from order_service import update_order_status as update_order_status_service
from product_service import create_product as create_seller_product_service
from product_service import delete_product as delete_seller_product_service
from product_service import get_seller_products as get_seller_products_service
from product_service import update_product as update_seller_product_service

seller_bp = Blueprint('seller', __name__)


def seller_required(view_func):
    @wraps(view_func)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')

        current_user = User.query.get(session['user_id'])
        if not current_user or current_user.role != 'seller':
            flash('Access denied. Sellers only.', 'danger')
            return redirect('/products')

        if not current_user.is_approved:
            flash('Please wait for admin approval.', 'warning')
            return redirect('/login')

        return view_func(*args, **kwargs)

    decorated_function.__name__ = view_func.__name__
    return decorated_function


def get_seller_products(seller_id):
    return get_seller_products_service(seller_id)


def create_seller_product(seller_id, form_data, image_filename):
    return create_seller_product_service(seller_id, form_data, image_filename)


def delete_seller_product(product_id, seller_id):
    return delete_seller_product_service(product_id, seller_id)


def update_seller_product(product, form_data):
    return update_seller_product_service(product, form_data)


def get_seller_orders(seller_id):
    return get_seller_orders_service(seller_id)


def update_order_status(order_id, seller_id, status):
    return update_order_status_service(order_id, seller_id, status)


@seller_bp.route('/dashboard')
@seller_required
def dashboard():
    products_list = get_seller_products(session['user_id'])
    return render_template('dashboard.html', products=products_list)


@seller_bp.route('/add-product', methods=['GET', 'POST'])
@seller_required
def add_product():
    if request.method == 'POST':
        image_filename = 'default.jpg'
        file = request.files.get('image')
        if file and file.filename:
            from app import allowed_file
            from werkzeug.utils import secure_filename
            import os
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join('static/uploads', filename))
                image_filename = filename

        create_seller_product(session['user_id'], request.form, image_filename)
        flash('Product added successfully!', 'success')
        return redirect('/dashboard')

    return render_template('add_product.html')


@seller_bp.route('/delete-product/<int:product_id>', methods=['POST'])
@seller_required
def delete_product(product_id):
    deleted = delete_seller_product(product_id, session['user_id'])
    if deleted:
        flash('Product deleted successfully!', 'success')
    return redirect('/dashboard')


@seller_bp.route('/edit-product/<int:product_id>', methods=['GET', 'POST'])
@seller_required
def edit_product(product_id):
    product = Product.query.get(product_id)
    if request.method == 'POST':
        update_seller_product(product, request.form)
        return redirect('/dashboard')
    return render_template('edit_product.html', product=product)


@seller_bp.route('/orders')
@seller_required
def seller_orders():
    orders = get_seller_orders(session['user_id'])
    return render_template('seller_orders.html', orders=orders)


@seller_bp.route('/update_order/<int:order_id>/<string:status>')
@seller_required
def update_order_status_route(order_id, status):
    updated = update_order_status(order_id, session['user_id'], status)
    if updated:
        flash(f'Order #{order_id} status updated to {status}!', 'success')
    else:
        flash('You are not authorized to update this order.', 'danger')
    return redirect('/orders')
