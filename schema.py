from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# Association tables for many-to-many relationships
order_product = db.Table('order_product',
    db.Column('order_id', db.Integer, db.ForeignKey('order.id'), primary_key=True),
    db.Column('product_id', db.Integer, db.ForeignKey('product.id'), primary_key=True),
    db.Column('quantity', db.Integer, nullable=False, default=1),
    db.Column('price_at_purchase', db.Float, nullable=False)
)

product_supplier = db.Table('product_supplier',
    db.Column('product_id', db.Integer, db.ForeignKey('product.id'), primary_key=True),
    db.Column('supplier_id', db.Integer, db.ForeignKey('supplier.id'), primary_key=True)
)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone_no = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    orders = db.relationship('Order', backref='customer', lazy=True)
    
    def __repr__(self):
        return f'<Customer {self.name}>'

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity_in_stock = db.Column(db.Integer, nullable=False, default=0)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    suppliers = db.relationship('Supplier', secondary=product_supplier, 
                               backref=db.backref('products', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Product {self.name}>'

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_method = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Pending')
    
    # Foreign keys
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    
    # Relationships
    products = db.relationship('Product', secondary=order_product, 
                              backref=db.backref('orders', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Order {self.id}>'

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone_no = db.Column(db.String(20), nullable=True)
    role = db.Column(db.String(50), nullable=False)
    salary = db.Column(db.Float, nullable=False)
    hire_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    orders = db.relationship('Order', backref='employee', lazy=True)
    
    def __repr__(self):
        return f'<Employee {self.name}>'

class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone_no = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=True)
    address = db.Column(db.String(200), nullable=True)
    
    def __repr__(self):
        return f'<Supplier {self.name}>'

print("Database schema defined successfully!")