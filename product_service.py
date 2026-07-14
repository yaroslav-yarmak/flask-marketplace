from models import Product, db


def get_products_by_category(selected_category='all'):
    if selected_category == 'all':
        return Product.query.all()
    return Product.query.filter(Product.category.ilike(selected_category)).all()


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
