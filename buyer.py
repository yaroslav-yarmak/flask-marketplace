from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session

from models import Product, User
from order_service import create_checkout_order as create_checkout_order_service
from order_service import get_buyer_orders as get_buyer_orders_service
from order_service import place_purchase_order as place_purchase_order_service
from product_service import get_product_by_id, get_products_by_category

buyer_bp = Blueprint('buyer', __name__)


def buyer_required(view_func):
    @wraps(view_func)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to buy products', 'warning')
            return redirect('/login')

        current_user = User.query.get(session['user_id'])
        if not current_user or current_user.role != 'buyer':
            flash('Access denied. Buyers only.', 'danger')
            return redirect('/products')

        return view_func(*args, **kwargs)

    decorated_function.__name__ = view_func.__name__
    return decorated_function


def create_checkout_order(product, buyer_id, form_data):
    return create_checkout_order_service(product, buyer_id, form_data)


def place_purchase_order(product, buyer_id, form_data=None):
    return place_purchase_order_service(product, buyer_id, form_data=form_data)


def get_buyer_orders(buyer_id):
    return get_buyer_orders_service(buyer_id)


@buyer_bp.route('/')
def home():
    return redirect('/products')


@buyer_bp.route('/products')
def products():
    selected_category = request.args.get('category', 'all')
    items = get_products_by_category(selected_category)
    return render_template('products.html', items=items, current_category=selected_category)


@buyer_bp.route('/my-orders')
@buyer_required
def my_orders():
    orders = get_buyer_orders(session['user_id'])
    return render_template('my_orders.html', orders=orders)


@buyer_bp.route('/checkout/<int:product_id>', methods=['GET', 'POST'])
@buyer_required
def checkout(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        try:
            create_checkout_order(product, session['user_id'], request.form)
        except ValueError as exc:
            flash(str(exc), 'danger')
            return redirect('/products')

        flash('Order confirmed! Seller will contact you.', 'success')
        return redirect('/products')

    return render_template('checkout.html', product=product)


@buyer_bp.route('/buy/<int:product_id>')
@buyer_required
def buy_product(product_id):
    product = Product.query.get_or_404(product_id)

    flash('Please complete checkout to place your order.', 'info')
    return redirect(f'/checkout/{product_id}')
