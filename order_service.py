from models import Order, db
from product_service import reduce_stock


def _get_customer_details(form_data):
    customer_data = {
        'full_name': form_data.get('full_name', '').strip() if form_data else '',
        'phone': form_data.get('phone', '').strip() if form_data else '',
        'address': form_data.get('address', '').strip() if form_data else '',
    }

    missing_fields = [field for field, value in customer_data.items() if not value]
    if missing_fields:
        raise ValueError('Please provide your full name, phone number, and address.')

    return customer_data


def create_checkout_order(product, buyer_id, form_data):
    if product.stock <= 0:
        raise ValueError('Out of stock!')

    customer_data = _get_customer_details(form_data)
    new_order = Order(
        product_id=product.id,
        buyer_id=buyer_id,
        seller_id=product.seller_id,
        status='Pending',
        **customer_data
    )

    reduce_stock(product)
    db.session.add(new_order)
    db.session.commit()
    return new_order


def place_purchase_order(product, buyer_id, form_data=None):
    if product.stock <= 0:
        raise ValueError('Out of stock!')

    customer_data = _get_customer_details(form_data)
    new_order = Order(
        product_id=product.id,
        buyer_id=buyer_id,
        seller_id=product.seller_id,
        status='Pending',
        **customer_data
    )

    reduce_stock(product)
    db.session.add(new_order)
    db.session.commit()
    return new_order


def get_buyer_orders(buyer_id):
    return Order.query.filter_by(buyer_id=buyer_id).order_by(Order.date_ordered.desc()).all()


def get_seller_orders(seller_id):
    return Order.query.filter_by(seller_id=seller_id).order_by(Order.date_ordered.desc()).all()


def update_order_status(order_id, seller_id, status):
    order = Order.query.get_or_404(order_id)
    if order.seller_id != seller_id:
        return False

    order.status = status
    db.session.commit()
    return True


def get_all_orders():
    return Order.query.order_by(Order.date_ordered.desc()).all()
