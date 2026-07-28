from models import Product, db


def get_products_by_category(selected_category='all', search=None, sort=None, in_stock_only=False, availability='all', min_price=None, max_price=None):
    query = Product.query

    # Category filter
    if selected_category != 'all':
        query = query.filter(Product.category.ilike(selected_category))

    # Title search (case-insensitive, trimmed)
    if search:
        query = query.filter(Product.title.ilike(f'%{search.strip()}%'))

    # In-stock filter (legacy param)
    if in_stock_only:
        query = query.filter(Product.stock > 0)

    # Availability filter (new, replaces in_stock_only in sidebar)
    if availability == 'in_stock':
        query = query.filter(Product.stock > 0)
    elif availability == 'out_of_stock':
        query = query.filter(Product.stock == 0)

    # Price range filter — safely validated
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    # Sorting — allowlist only
    ALLOWED_SORTS = {
        'price_asc': Product.price.asc(),
        'price_desc': Product.price.desc(),
    }
    if sort in ALLOWED_SORTS:
        query = query.order_by(ALLOWED_SORTS[sort])

    return query.all()


def get_product_by_id(product_id):
    return Product.query.get_or_404(product_id)


def create_product(seller_id, form_data, image_filename):
    new_product = Product(
        title=form_data.get('title'),
        price=float(form_data.get('price')),
        stock=int(form_data.get('stock')),
        desc=form_data.get('desc'),
        category=form_data.get('category'),
        image_file=image_filename,
        seller_id=seller_id
    )
    db.session.add(new_product)
    db.session.commit()
    return new_product


def update_product_stock(product, quantity_change):
    product.stock += quantity_change
    db.session.commit()
    return product


def reduce_stock(product):
    return update_product_stock(product, -1)


def get_seller_products(seller_id):
    return Product.query.filter_by(seller_id=seller_id).all()


def delete_product(product_id, seller_id):
    product = Product.query.get(product_id)
    if product and product.seller_id == seller_id:
        db.session.delete(product)
        db.session.commit()
        return True
    return False


def update_product(product, form_data):
    product.title = form_data.get('title')
    product.price = form_data.get('price')
    db.session.commit()
    return product
