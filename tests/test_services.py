import pytest
from flask import session

import app as app_module
from auth_service import authenticate_user, login_user, logout_user, register_user
from order_service import create_checkout_order, get_all_orders, get_buyer_orders, place_purchase_order, update_order_status


@pytest.fixture()
def app_context():
    app_module.app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI='sqlite:///:memory:')
    assert app_module.app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///:memory:'
    assert app_module.app.config['TESTING'] is True
    with app_module.app.app_context():
        app_module.db.drop_all()
        app_module.db.create_all()
        yield
        app_module.db.session.remove()
        app_module.db.drop_all()


def create_user(email, role='buyer', approved=False):
    user = app_module.User(email=email, password='hashed-password', role=role, is_approved=approved)
    app_module.db.session.add(user)
    app_module.db.session.commit()
    return user


def create_product(seller_id, stock=3):
    product = app_module.Product(
        title='Test Product',
        price=19.99,
        stock=stock,
        desc='A test product',
        category='tools',
        seller_id=seller_id,
    )
    app_module.db.session.add(product)
    app_module.db.session.commit()
    return product


def test_create_checkout_order_creates_order_and_reduces_stock(app_context):
    seller = create_user('seller@example.com', role='seller')
    buyer = create_user('buyer@example.com', role='buyer')
    product = create_product(seller.id, stock=2)

    order = create_checkout_order(
        product,
        buyer.id,
        {'full_name': 'Jane Doe', 'phone': '123456', 'address': 'Main Street'},
    )

    assert order.product_id == product.id
    assert order.buyer_id == buyer.id
    assert order.full_name == 'Jane Doe'
    assert app_module.Order.query.count() == 1
    app_module.db.session.refresh(product)
    assert product.stock == 1


def test_create_checkout_order_raises_when_out_of_stock(app_context):
    seller = create_user('seller2@example.com', role='seller')
    buyer = create_user('buyer2@example.com', role='buyer')
    product = create_product(seller.id, stock=0)

    with pytest.raises(ValueError):
        create_checkout_order(
            product,
            buyer.id,
            {'full_name': 'Jane Doe', 'phone': '123456', 'address': 'Main Street'},
        )

    assert app_module.Order.query.count() == 0


def test_place_purchase_order_creates_order_and_reduces_stock(app_context):
    seller = create_user('seller3@example.com', role='seller')
    buyer = create_user('buyer3@example.com', role='buyer')
    product = create_product(seller.id, stock=5)

    order = place_purchase_order(
        product,
        buyer.id,
        {'full_name': 'Jane Doe', 'phone': '123456', 'address': 'Main Street'},
    )

    assert order.seller_id == seller.id
    assert order.buyer_id == buyer.id
    assert order.full_name == 'Jane Doe'
    assert order.phone == '123456'
    assert order.address == 'Main Street'
    app_module.db.session.refresh(product)
    assert product.stock == 4


def test_update_order_status_allows_seller_and_blocks_unauthorized_change(app_context):
    seller = create_user('seller4@example.com', role='seller')
    buyer = create_user('buyer4@example.com', role='buyer')
    product = create_product(seller.id, stock=1)
    order = place_purchase_order(
        product,
        buyer.id,
        {'full_name': 'Jane Doe', 'phone': '123456', 'address': 'Main Street'},
    )

    assert update_order_status(order.id, seller.id, 'Shipped') is True
    app_module.db.session.refresh(order)
    assert order.status == 'Shipped'
    assert update_order_status(order.id, buyer.id, 'Cancelled') is False


def test_get_buyer_and_seller_orders_return_expected_lists(app_context):
    seller = create_user('seller5@example.com', role='seller')
    buyer = create_user('buyer5@example.com', role='buyer')
    product = create_product(seller.id, stock=2)
    place_purchase_order(
        product,
        buyer.id,
        {'full_name': 'Jane Doe', 'phone': '123456', 'address': 'Main Street'},
    )

    assert len(get_buyer_orders(buyer.id)) == 1
    assert len(get_all_orders()) == 1
    assert len(get_buyer_orders(999)) == 0


def test_authenticate_user_returns_user_for_valid_credentials(app_context):
    register_user('auth@example.com', 'secret123', 'buyer')

    user = authenticate_user('auth@example.com', 'secret123')

    assert user is not None
    assert user.email == 'auth@example.com'


def test_authenticate_user_returns_none_for_invalid_credentials(app_context):
    register_user('bad@example.com', 'password', 'buyer')

    assert authenticate_user('bad@example.com', 'wrong-password') is None


def test_login_user_sets_session_for_buyer_and_returns_redirect_path(app_context):
    with app_module.app.test_request_context():
        user = register_user('login@example.com', 'secret', 'buyer')

        redirect_path, error_message = login_user(user, 'buyer')

        assert redirect_path == '/products'
        assert error_message is None
        assert session['user_id'] == user.id


def test_login_user_rejects_unapproved_seller(app_context):
    with app_module.app.test_request_context():
        user = create_user('seller-pending@example.com', role='seller', approved=False)

        redirect_path, error_message = login_user(user, 'seller')

        assert redirect_path is None
        assert error_message == 'Please wait for admin approval.'


def test_login_user_allows_admin_and_returns_redirect_path_with_no_error(app_context):
    with app_module.app.test_request_context():
        user = create_user('admin-login@example.com', role='admin', approved=True)

        redirect_path, error_message = login_user(user, 'admin')

        assert redirect_path == '/admin/dashboard'
        assert error_message is None
        assert session['user_id'] == user.id


def test_register_user_rejects_duplicate_email(app_context):
    register_user('dup@example.com', 'pass', 'buyer')

    with pytest.raises(ValueError):
        register_user('dup@example.com', 'pass', 'buyer')


def test_logout_user_clears_session(app_context):
    with app_module.app.test_request_context():
        session['user_id'] = 123
        logout_user()
        assert 'user_id' not in session
