from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from schema import db, Customer, Product, Order, Employee, Supplier, order_product, product_supplier
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_for_testing')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///apparel_inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User model for authentication
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)
    
    employee = db.relationship('Employee', backref='user', uselist=False)
    customer = db.relationship('Customer', backref='user', uselist=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create a function to create tables and initialize data
def create_tables():
    with app.app_context():
        db.create_all()
        # Create admin user if not exists
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()

# Call the function after app initialization
with app.app_context():
    create_tables()

# Routes
@app.route('/')
def index():
    return render_template('landing.html')

@app.route('/store')
def store_redirect():
    return redirect(url_for('shop'))

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        
        flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get counts for dashboard
    customer_count = Customer.query.count()
    product_count = Product.query.count()
    order_count = Order.query.count()
    low_stock_count = Product.query.filter(Product.quantity_in_stock < 10).count()
    
    # Get recent orders
    recent_orders = Order.query.order_by(Order.date.desc()).limit(5).all()
    
    return render_template('dashboard.html', 
                          customer_count=customer_count,
                          product_count=product_count,
                          order_count=order_count,
                          low_stock_count=low_stock_count,
                          recent_orders=recent_orders)

# Customer routes
@app.route('/customers')
@login_required
def customers():
    customers_list = Customer.query.all()
    return render_template('customers.html', customers=customers_list)

@app.route('/customers/add', methods=['GET', 'POST'])
@login_required
def add_customer():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address')
        
        # Validate data
        if not name or not email:
            flash('Name and email are required', 'danger')
            return redirect(url_for('add_customer'))
        
        # Check if email already exists
        if Customer.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return redirect(url_for('add_customer'))
        
        customer = Customer(name=name, email=email, phone_no=phone, address=address)
        db.session.add(customer)
        db.session.commit()
        
        flash('Customer added successfully', 'success')
        return redirect(url_for('customers'))
    
    return render_template('add_customer.html')

@app.route('/customers/edit/<int:customer_id>', methods=['GET', 'POST'])
@login_required
def edit_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address')
        
        # Validate data
        if not name or not email:
            flash('Name and email are required', 'danger')
            return redirect(url_for('edit_customer', customer_id=customer_id))
        
        # Check if email already exists and is not the current customer's email
        existing_customer = Customer.query.filter_by(email=email).first()
        if existing_customer and existing_customer.id != customer_id:
            flash('Email already exists', 'danger')
            return redirect(url_for('edit_customer', customer_id=customer_id))
        
        customer.name = name
        customer.email = email
        customer.phone_no = phone
        customer.address = address
        
        db.session.commit()
        flash('Customer updated successfully', 'success')
        return redirect(url_for('customers'))
    
    return render_template('edit_customer.html', customer=customer)

@app.route('/customers/delete/<int:customer_id>', methods=['POST'])
@login_required
def delete_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    
    # Check if customer has orders
    if customer.orders:
        flash('Cannot delete customer with existing orders', 'danger')
        return redirect(url_for('customers'))
    
    db.session.delete(customer)
    db.session.commit()
    
    flash('Customer deleted successfully', 'success')
    return redirect(url_for('customers'))

# Product routes
@app.route('/products')
@login_required
def products():
    products_list = Product.query.all()
    return render_template('products.html', products=products_list)

@app.route('/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price')
        quantity = request.form.get('quantity')
        category = request.form.get('category')
        description = request.form.get('description')
        
        # Validate data
        if not name or not price or not quantity or not category:
            flash('All fields except description are required', 'danger')
            return redirect(url_for('add_product'))
        
        try:
            price = float(price)
            quantity = int(quantity)
        except ValueError:
            flash('Price must be a number and quantity must be an integer', 'danger')
            return redirect(url_for('add_product'))
        
        product = Product(name=name, price=price, quantity_in_stock=quantity, 
                         category=category, description=description)
        db.session.add(product)
        db.session.commit()
        
        flash('Product added successfully', 'success')
        return redirect(url_for('products'))
    
    return render_template('add_product.html')

@app.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price')
        quantity = request.form.get('quantity')
        category = request.form.get('category')
        description = request.form.get('description')
        
        # Validate data
        if not name or not price or not quantity or not category:
            flash('All fields except description are required', 'danger')
            return redirect(url_for('edit_product', product_id=product_id))
        
        try:
            price = float(price)
            quantity = int(quantity)
        except ValueError:
            flash('Price must be a number and quantity must be an integer', 'danger')
            return redirect(url_for('edit_product', product_id=product_id))
        
        product.name = name
        product.price = price
        product.quantity_in_stock = quantity
        product.category = category
        product.description = description
        
        db.session.commit()
        flash('Product updated successfully', 'success')
        return redirect(url_for('products'))
    
    return render_template('edit_product.html', product=product)

@app.route('/products/delete/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Check if product is in any orders
    if product.orders.count() > 0:
        flash('Cannot delete product that has been ordered', 'danger')
        return redirect(url_for('products'))
    
    db.session.delete(product)
    db.session.commit()
    
    flash('Product deleted successfully', 'success')
    return redirect(url_for('products'))

# Order routes
@app.route('/orders')
@login_required
def orders():
    orders_list = Order.query.all()
    return render_template('orders.html', orders=orders_list)

@app.route('/orders/add', methods=['GET', 'POST'])
@login_required
def add_order():
    if request.method == 'POST':
        customer_id = request.form.get('customer_id')
        payment_method = request.form.get('payment_method')
        
        # Validate data
        if not customer_id or not payment_method:
            flash('All fields are required', 'danger')
            return redirect(url_for('add_order'))
        
        # Get product IDs and quantities from form
        product_ids = request.form.getlist('product_id[]')
        quantities = request.form.getlist('quantity[]')
        
        if not product_ids or not quantities or len(product_ids) != len(quantities):
            flash('Please add at least one product with quantity', 'danger')
            return redirect(url_for('add_order'))
        
        # Calculate total amount
        total_amount = 0
        for i in range(len(product_ids)):
            product = Product.query.get(product_ids[i])
            if not product:
                flash(f'Product with ID {product_ids[i]} not found', 'danger')
                return redirect(url_for('add_order'))
            
            quantity = int(quantities[i])
            if quantity > product.quantity_in_stock:
                flash(f'Not enough stock for {product.name}', 'danger')
                return redirect(url_for('add_order'))
            
            total_amount += product.price * quantity
        
        # Create order
        order = Order(
            customer_id=customer_id,
            employee_id=current_user.employee_id if current_user.employee_id else 1,
            payment_method=payment_method,
            amount=total_amount,
            date=datetime.utcnow()
        )
        
        db.session.add(order)
        db.session.flush()  # Get order ID without committing
        
        # Add products to order and update stock
        for i in range(len(product_ids)):
            product = Product.query.get(product_ids[i])
            quantity = int(quantities[i])
            
            # Add to order_product table
            stmt = order_product.insert().values(
                order_id=order.id,
                product_id=product.id,
                quantity=quantity,
                price_at_purchase=product.price
            )
            db.session.execute(stmt)
            
            # Update stock
            product.quantity_in_stock -= quantity
        
        db.session.commit()
        flash('Order added successfully', 'success')
        return redirect(url_for('orders'))
    
    customers_list = Customer.query.all()
    products_list = Product.query.filter(Product.quantity_in_stock > 0).all()
    return render_template('add_order.html', customers=customers_list, products=products_list)

@app.route('/orders/view/<int:order_id>')
@login_required
def view_order(order_id):
    order = Order.query.get_or_404(order_id)
    
    # Get order items
    order_items = db.session.query(
        Product.id, 
        Product.name, 
        order_product.c.quantity, 
        order_product.c.price_at_purchase
    ).join(
        order_product, 
        Product.id == order_product.c.product_id
    ).filter(
        order_product.c.order_id == order_id
    ).all()
    
    return render_template('view_order.html', order=order, order_items=order_items)

@app.route('/orders/update-status/<int:order_id>', methods=['POST'])
@login_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    
    status = request.form.get('status')
    if status in ['Pending', 'Processing', 'Completed', 'Cancelled']:
        order.status = status
        db.session.commit()
        flash('Order status updated successfully', 'success')
    else:
        flash('Invalid status', 'danger')
    
    return redirect(url_for('view_order', order_id=order_id))

# Employee routes
@app.route('/employees')
@login_required
def employees():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    employees_list = Employee.query.all()
    return render_template('employees.html', employees=employees_list)

@app.route('/employees/add', methods=['GET', 'POST'])
@login_required
def add_employee():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        role = request.form.get('role')
        salary = request.form.get('salary')
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Validate data
        if not name or not email or not role or not salary or not username or not password:
            flash('All fields except phone are required', 'danger')
            return redirect(url_for('add_employee'))
        
        try:
            salary = float(salary)
        except ValueError:
            flash('Salary must be a number', 'danger')
            return redirect(url_for('add_employee'))
        
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('add_employee'))
        
        # Create employee
        employee = Employee(name=name, email=email, phone_no=phone, role=role, salary=salary)
        db.session.add(employee)
        db.session.flush()  # Get employee ID without committing
        
        # Create user account
        user = User(username=username, employee_id=employee.id)
        user.set_password(password)
        db.session.add(user)
        
        db.session.commit()
        flash('Employee added successfully', 'success')
        return redirect(url_for('employees'))
    
    return render_template('add_employee.html')

@app.route('/employees/edit/<int:employee_id>', methods=['GET', 'POST'])
@login_required
def edit_employee(employee_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    employee = Employee.query.get_or_404(employee_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        role = request.form.get('role')
        salary = request.form.get('salary')
        
        # Validate data
        if not name or not email or not role or not salary:
            flash('All fields except phone are required', 'danger')
            return redirect(url_for('edit_employee', employee_id=employee_id))
        
        try:
            salary = float(salary)
        except ValueError:
            flash('Salary must be a number', 'danger')
            return redirect(url_for('edit_employee', employee_id=employee_id))
        
        # Check if email already exists and is not the current employee's email
        existing_employee = Employee.query.filter_by(email=email).first()
        if existing_employee and existing_employee.id != employee_id:
            flash('Email already exists', 'danger')
            return redirect(url_for('edit_employee', employee_id=employee_id))
        
        employee.name = name
        employee.email = email
        employee.phone_no = phone
        employee.role = role
        employee.salary = salary
        
        db.session.commit()
        flash('Employee updated successfully', 'success')
        return redirect(url_for('employees'))
    
    return render_template('edit_employee.html', employee=employee)

@app.route('/employees/delete/<int:employee_id>', methods=['POST'])
@login_required
def delete_employee(employee_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    employee = Employee.query.get_or_404(employee_id)
    
    # Check if employee has orders
    if employee.orders:
        flash('Cannot delete employee with associated orders', 'danger')
        return redirect(url_for('employees'))
    
    # Check if employee has a user account
    user = User.query.filter_by(employee_id=employee_id).first()
    if user:
        db.session.delete(user)
    
    db.session.delete(employee)
    db.session.commit()
    
    flash('Employee deleted successfully', 'success')
    return redirect(url_for('employees'))

# Supplier routes
@app.route('/suppliers')
@login_required
def suppliers():
    suppliers_list = Supplier.query.all()
    return render_template('suppliers.html', suppliers=suppliers_list)

@app.route('/suppliers/add', methods=['GET', 'POST'])
@login_required
def add_supplier():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        address = request.form.get('address')
        
        # Validate data
        if not name or not phone:
            flash('Name and phone are required', 'danger')
            return redirect(url_for('add_supplier'))
        
        supplier = Supplier(name=name, phone_no=phone, email=email, address=address)
        db.session.add(supplier)
        db.session.commit()
        
        flash('Supplier added successfully', 'success')
        return redirect(url_for('suppliers'))
    
    return render_template('add_supplier.html')

@app.route('/suppliers/edit/<int:supplier_id>', methods=['GET', 'POST'])
@login_required
def edit_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        address = request.form.get('address')
        
        # Validate data
        if not name or not phone:
            flash('Name and phone are required', 'danger')
            return redirect(url_for('edit_supplier', supplier_id=supplier_id))
        
        supplier.name = name
        supplier.phone_no = phone
        supplier.email = email
        supplier.address = address
        
        db.session.commit()
        flash('Supplier updated successfully', 'success')
        return redirect(url_for('suppliers'))
    
    return render_template('edit_supplier.html', supplier=supplier)

@app.route('/suppliers/delete/<int:supplier_id>', methods=['POST'])
@login_required
def delete_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    
    # Check if supplier has products
    if supplier.products.count() > 0:
        flash('Cannot delete supplier with associated products', 'danger')
        return redirect(url_for('suppliers'))
    
    db.session.delete(supplier)
    db.session.commit()
    
    flash('Supplier deleted successfully', 'success')
    return redirect(url_for('suppliers'))

# API routes for AJAX requests
@app.route('/api/products/<int:product_id>')
@login_required
def get_product(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify({
        'id': product.id,
        'name': product.name,
        'price': product.price,
        'quantity_in_stock': product.quantity_in_stock
    })


@app.route('/')
def landing():
    return render_template('landing.html')


# Client-side routes
@app.route('/shop')
def shop():
    category = request.args.get('category')
    search = request.args.get('search')
    
    # Base query
    query = Product.query.filter(Product.quantity_in_stock > 0)
    
    # Apply filters
    if category:
        query = query.filter_by(category=category)
    
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))
    
    # Get products
    products = query.all()
    
    # Get all categories for sidebar
    categories = db.session.query(Product.category).distinct().all()
    categories = [category[0] for category in categories]
    
    return render_template('shop/index.html', 
                          products=products, 
                          categories=categories, 
                          current_category=category,
                          search_query=search)

@app.route('/shop/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Get related products (same category)
    related_products = Product.query.filter(
        Product.category == product.category,
        Product.id != product.id,
        Product.quantity_in_stock > 0
    ).limit(4).all()
    
    return render_template('shop/product_detail.html', 
                          product=product, 
                          related_products=related_products)

@app.route('/shop/register', methods=['GET', 'POST'])
def shop_register():
    if current_user.is_authenticated:
        return redirect(url_for('shop'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        address = request.form.get('address')
        
        # Validate data
        if not name or not email or not password:
            flash('Name, email and password are required', 'danger')
            return redirect(url_for('shop_register'))
        
        # Check if email already exists
        if Customer.query.filter_by(email=email).first() or User.query.filter_by(username=email).first():
            flash('Email already exists', 'danger')
            return redirect(url_for('shop_register'))
        
        # Create customer
        customer = Customer(name=name, email=email, phone_no=phone, address=address)
        db.session.add(customer)
        db.session.flush()  # Get customer ID without committing
        
        # Create user account
        user = User(username=email, customer_id=customer.id)
        user.set_password(password)
        db.session.add(user)
        
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('shop_login'))
    
    return render_template('shop/register.html')

@app.route('/shop/login', methods=['GET', 'POST'])
def shop_login():
    if current_user.is_authenticated:
        return redirect(url_for('shop'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=email).first()
        if user and user.check_password(password) and user.customer_id:
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('shop'))
        
        flash('Invalid email or password', 'danger')
    
    return render_template('shop/login.html')

@app.route('/shop/cart')
def cart():
    cart_items = []
    total = 0
    
    if 'cart' in session:
        for product_id, quantity in session['cart'].items():
            product = Product.query.get(int(product_id))
            if product:
                subtotal = product.price * quantity
                cart_items.append({
                    'product': product,
                    'quantity': quantity,
                    'subtotal': subtotal
                })
                total += subtotal
    
    return render_template('shop/cart.html', cart_items=cart_items, total=total)

@app.route('/shop/cart/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    quantity = int(request.form.get('quantity', 1))
    
    if quantity > product.quantity_in_stock:
        flash(f'Only {product.quantity_in_stock} items available in stock', 'warning')
        quantity = product.quantity_in_stock
    
    if 'cart' not in session:
        session['cart'] = {}
    
    if str(product_id) in session['cart']:
        session['cart'][str(product_id)] += quantity
    else:
        session['cart'][str(product_id)] = quantity
    
    session.modified = True
    flash(f'{product.name} added to cart', 'success')
    
    return redirect(request.referrer or url_for('shop'))

@app.route('/shop/cart/update/<int:product_id>', methods=['POST'])
def update_cart(product_id):
    if 'cart' not in session:
        return redirect(url_for('cart'))
    
    quantity = int(request.form.get('quantity', 0))
    if quantity <= 0:
        if str(product_id) in session['cart']:
            del session['cart'][str(product_id)]
    else:
        product = Product.query.get_or_404(product_id)
        if quantity > product.quantity_in_stock:
            quantity = product.quantity_in_stock
            flash(f'Quantity adjusted to match available stock ({quantity})', 'warning')
        
        session['cart'][str(product_id)] = quantity
    
    session.modified = True
    return redirect(url_for('cart'))

@app.route('/shop/cart/remove/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    if 'cart' in session and str(product_id) in session['cart']:
        del session['cart'][str(product_id)]
        session.modified = True
    
    return redirect(url_for('cart'))

@app.route('/shop/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    if 'cart' not in session or not session['cart']:
        flash('Your cart is empty', 'warning')
        return redirect(url_for('shop'))
    
    if not current_user.customer_id:
        flash('Please log in as a customer to checkout', 'warning')
        return redirect(url_for('shop_login'))
    
    cart_items = []
    total = 0
    
    for product_id, quantity in session['cart'].items():
        product = Product.query.get(int(product_id))
        if product:
            subtotal = product.price * quantity
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': subtotal
            })
            total += subtotal
    
    if request.method == 'POST':
        payment_method = request.form.get('payment_method')
        
        if not payment_method:
            flash('Please select a payment method', 'danger')
            return redirect(url_for('checkout'))
        
        # Create order
        order = Order(
            customer_id=current_user.customer_id,
            employee_id=1,  # Default to first employee
            payment_method=payment_method,
            amount=total,
            date=datetime.utcnow(),
            status='Pending'
        )
        
        db.session.add(order)
        db.session.flush()  # Get order ID without committing
        
        # Add products to order and update stock
        for item in cart_items:
            product = item['product']
            quantity = item['quantity']
            
            # Check if still in stock
            if quantity > product.quantity_in_stock:
                flash(f'Not enough stock for {product.name}', 'danger')
                return redirect(url_for('checkout'))
            
            # Add to order_product table
            stmt = order_product.insert().values(
                order_id=order.id,
                product_id=product.id,
                quantity=quantity,
                price_at_purchase=product.price
            )
            db.session.execute(stmt)
            
            # Update stock
            product.quantity_in_stock -= quantity
        
        db.session.commit()
        
        # Clear cart
        session.pop('cart', None)
        
        flash('Order placed successfully!', 'success')
        return redirect(url_for('order_confirmation', order_id=order.id))
    
    # Get customer info
    customer = Customer.query.get(current_user.customer_id)
    
    return render_template('shop/checkout.html', 
                          cart_items=cart_items, 
                          total=total,
                          customer=customer)

@app.route('/shop/order-confirmation/<int:order_id>')
@login_required
def order_confirmation(order_id):
    order = Order.query.get_or_404(order_id)
    
    # Security check - only allow viewing own orders
    if order.customer_id != current_user.customer_id:
        flash('Access denied', 'danger')
        return redirect(url_for('shop'))
    
    # Get order items
    order_items = db.session.query(
        Product.id, 
        Product.name, 
        order_product.c.quantity, 
        order_product.c.price_at_purchase
    ).join(
        order_product, 
        Product.id == order_product.c.product_id
    ).filter(
        order_product.c.order_id == order_id
    ).all()
    
    return render_template('shop/order_confirmation.html', 
                          order=order, 
                          order_items=order_items)

@app.route('/shop/my-orders')
@login_required
def my_orders():
    if not current_user.customer_id:
        flash('Access denied', 'danger')
        return redirect(url_for('shop'))
    
    orders = Order.query.filter_by(customer_id=current_user.customer_id).order_by(Order.date.desc()).all()
    
    return render_template('shop/my_orders.html', orders=orders)

@app.route('/shop/my-orders/<int:order_id>')
@login_required
def my_order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    
    # Security check - only allow viewing own orders
    if order.customer_id != current_user.customer_id:
        flash('Access denied', 'danger')
        return redirect(url_for('my_orders'))
    
    # Get order items
    order_items = db.session.query(
        Product.id, 
        Product.name, 
        order_product.c.quantity, 
        order_product.c.price_at_purchase
    ).join(
        order_product, 
        Product.id == order_product.c.product_id
    ).filter(
        order_product.c.order_id == order_id
    ).all()
    
    return render_template('shop/my_order_detail.html', 
                          order=order, 
                          order_items=order_items)

if __name__ == '__main__':
    app.run(debug=True)

print("Flask application setup complete!")




