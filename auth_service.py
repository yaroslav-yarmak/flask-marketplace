from flask import session
from werkzeug.security import check_password_hash, generate_password_hash


def get_user_model_and_db():
    from models import User, db
    return User, db


def authenticate_user(email, password):
    User, _ = get_user_model_and_db()
    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password, password):
        return user
    return None


def login_user(user, role_from_form):
    if user.role == 'admin':
        session['user_id'] = user.id
        return '/admin/dashboard', None

    if user.role == 'seller':
        if not user.is_approved:
            return None, 'Please wait for admin approval.'
        if role_from_form == 'seller':
            session['user_id'] = user.id
            return '/dashboard', None
        return None, 'Incorrect email, password or role'

    if user.role == 'buyer' and role_from_form == 'buyer':
        session['user_id'] = user.id
        return '/products', None

    return None, 'Incorrect email, password or role'


def register_user(email, password, role):
    User, db = get_user_model_and_db()
    if User.query.filter_by(email=email).first():
        raise ValueError('This Email is already registered!')

    new_user = User(email=email, password=generate_password_hash(password), role=role)
    db.session.add(new_user)
    db.session.commit()
    return new_user


def logout_user():
    session.pop('user_id', None)
