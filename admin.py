from functools import wraps

from flask import Blueprint, flash, redirect, render_template, session

from models import Product, User, db
from order_service import get_all_orders

admin_bp = Blueprint('admin', __name__)


def admin_required(view_func):
    @wraps(view_func)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')

        current_user = User.query.get(session['user_id'])
        if not current_user or current_user.role != 'admin':
            flash('Access denied. Admins only.', 'danger')
            return redirect('/products')

        return view_func(*args, **kwargs)

    decorated_function.__name__ = view_func.__name__
    return decorated_function


def get_admin_stats():
    return {
        'total_products': Product.query.count(),
        'total_sellers': User.query.filter_by(role='seller').count(),
        'total_users': User.query.count(),
        'pending_sellers': User.query.filter_by(role='seller', is_approved=False).count()
    }


def get_pending_sellers():
    return User.query.filter_by(role='seller', is_approved=False).all()


def approve_seller(user_id):
    user = User.query.get_or_404(user_id)
    user.is_approved = True
    db.session.commit()
    return user


def reject_seller(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return user


@admin_bp.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    stats = get_admin_stats()
    return render_template('admin_dashboard.html', stats=stats)


@admin_bp.route('/admin/requests')
@admin_required
def admin_requests():
    pending_sellers = get_pending_sellers()
    return render_template('admin_requests.html', sellers=pending_sellers)


@admin_bp.route('/admin/approve/<int:user_id>')
@admin_required
def approve_seller_route(user_id):
    user = approve_seller(user_id)
    flash(f'Seller {user.email} approved successfully!', 'success')
    return redirect('/admin/requests')


@admin_bp.route('/admin/reject/<int:user_id>')
@admin_required
def reject_seller_route(user_id):
    user = reject_seller(user_id)
    flash(f'Request from {user.email} rejected and account deleted.', 'warning')
    return redirect('/admin/requests')


@admin_bp.route('/make-me-admin/<email>')
def make_me_admin(email):
    user = User.query.filter_by(email=email).first()
    if user:
        user.role = 'admin'
        user.is_approved = True
        db.session.commit()
        return f"Користувач {email} тепер Адміністратор!"
    return "Користувача не знайдено", 404


@admin_bp.route('/admin/orders')
@admin_required
def admin_all_orders():
    all_orders = get_all_orders()
    return render_template('admin_orders.html', orders=all_orders)


@admin_bp.route('/admin/users')
@admin_required
def admin_users():
    all_users = User.query.all()
    return render_template('admin_users.html', users=all_users)
