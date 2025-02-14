from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, make_response, send_file
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User, Product, Order, OrderItem, Service, Appointment
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func
from xhtml2pdf import pisa
from io import BytesIO
import random
import string
from werkzeug.exceptions import HTTPException

main = Blueprint('main', __name__)

@main.route('/')
@main.route('/login', methods=['GET', 'POST'])
def login():
    print("Login route accessed")  # Debug print
    if current_user.is_authenticated:
        print("User already authenticated")  # Debug print
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        print(f"Login attempt - Username: {username}")  # Debug print
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            user.update_last_login()  # Update last login time
            print("Login successful!")  # Debug print
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.dashboard'))
        print("Login failed!")  # Debug print
        flash('Invalid username or password')
    
    try:
        return render_template('login.html')
    except Exception as e:
        print(f"Error rendering template: {e}")  # Debug print
        return str(e), 500

@main.route('/dashboard')
@login_required
def dashboard():
    today = datetime.now().date()
    
    # Today's appointments
    today_appointments = Appointment.query.filter(
        func.date(Appointment.appointment_date) == today
    ).order_by(Appointment.appointment_date).all()
    
    # Upcoming appointments (next 7 days)
    next_week = today + timedelta(days=7)
    upcoming_appointments = Appointment.query.filter(
        Appointment.appointment_date.between(today, next_week),
        Appointment.status == 'scheduled'
    ).order_by(Appointment.appointment_date).all()
    
    # Orders statistics
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    total_orders = Order.query.count()
    
    # Monthly revenue
    start_of_month = today.replace(day=1)
    monthly_orders = Order.query.filter(
        Order.created_at >= start_of_month
    ).all()
    monthly_revenue = sum(order.total_amount for order in monthly_orders)
    
    # Last month revenue for comparison
    last_month = (start_of_month - timedelta(days=1)).replace(day=1)
    last_month_orders = Order.query.filter(
        Order.created_at.between(last_month, start_of_month)
    ).all()
    last_month_revenue = sum(order.total_amount for order in last_month_orders)
    
    # Calculate growth
    revenue_growth = ((monthly_revenue - last_month_revenue) / last_month_revenue * 100 
                     if last_month_revenue > 0 else 0)
    
    # Inventory statistics
    total_products = Product.query.count()
    low_stock_products = Product.query.filter(Product.stock < 10).all()
    low_stock_count = len(low_stock_products)
    
    # Service statistics
    active_services = Service.query.filter_by(is_active=True).count()
    total_services = Service.query.count()
    
    # Revenue chart data - last 30 days
    dates = []
    revenues = []
    for i in range(30, -1, -1):
        date = today - timedelta(days=i)
        daily_orders = Order.query.filter(
            func.date(Order.created_at) == date
        ).all()
        daily_revenue = sum(order.total_amount for order in daily_orders)
        dates.append(date.strftime('%Y-%m-%d'))
        revenues.append(daily_revenue)
    
    return render_template('dashboard.html',
        today_appointments=today_appointments,
        upcoming_appointments=upcoming_appointments,
        recent_orders=recent_orders,
        total_orders=total_orders,
        monthly_revenue=monthly_revenue,
        revenue_growth=revenue_growth,
        total_products=total_products,
        low_stock_products=low_stock_products,
        low_stock_count=low_stock_count,
        active_services=active_services,
        total_services=total_services,
        dates=dates,
        revenues=revenues
    )

@main.route('/inventory', methods=['GET', 'POST'])
@login_required
def inventory():
    if request.method == 'POST':
        name = request.form.get('name')
        brand = request.form.get('brand')
        size = request.form.get('size')
        type = request.form.get('type')
        description = request.form.get('description')
        price = request.form.get('price')
        stock = request.form.get('stock')
        
        if name and price and stock:
            product = Product(
                name=name,
                brand=brand,
                size=size,
                type=type,
                description=description,
                price=float(price),
                stock=int(stock)
            )
            db.session.add(product)
            db.session.commit()
            flash('Product added successfully!', 'success')
            return redirect(url_for('main.inventory'))
        
        flash('Please fill all required fields', 'error')
    
    products = Product.query.order_by(Product.created_at.desc()).all()
    services = Service.query.order_by(Service.name).all()
    return render_template('inventory.html', products=products, services=services)

@main.route('/inventory/edit/<int:id>', methods=['POST'])
@login_required
def edit_product(id):
    try:
        product = Product.query.get_or_404(id)
        
        # Update product fields
        product.name = request.form.get('name')
        product.brand = request.form.get('brand')
        product.size = request.form.get('size')
        product.type = request.form.get('type')
        product.description = request.form.get('description')
        product.price = float(request.form.get('price'))
        product.stock = int(request.form.get('stock'))
        product.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Product updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating product: {str(e)}', 'danger')
        print(f"Error: {str(e)}")
    
    return redirect(url_for('main.inventory'))

@main.route('/inventory/delete/<int:id>', methods=['POST'])
@login_required
def delete_product(id):
    try:
        product = Product.query.get_or_404(id)
        db.session.delete(product)
        db.session.commit()
        flash('Product deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting product: {str(e)}', 'danger')
        print(f"Error: {str(e)}")
    
    return redirect(url_for('main.inventory'))

@main.route('/services', methods=['GET', 'POST'])
@login_required
def services():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        duration = request.form.get('duration')
        
        if name and price:
            service = Service(
                name=name,
                description=description,
                price=float(price),
                duration=int(duration) if duration else None
            )
            db.session.add(service)
            db.session.commit()
            flash('Service added successfully!', 'success')
            return redirect(url_for('main.services'))
        
        flash('Please fill all required fields', 'error')
    
    services = Service.query.order_by(Service.created_at.desc()).all()
    return render_template('services.html', services=services)

@main.route('/services/edit/<int:id>', methods=['POST'])
@login_required
def edit_service(id):
    service = Service.query.get_or_404(id)
    
    service.name = request.form.get('name', service.name)
    service.description = request.form.get('description', service.description)
    service.price = float(request.form.get('price', service.price))
    service.duration = int(request.form.get('duration')) if request.form.get('duration') else None
    service.is_active = request.form.get('is_active') == 'true'
    service.category = request.form.get('category', service.category)
    
    try:
        db.session.commit()
        flash('Service updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating service', 'danger')
        print(f"Error: {str(e)}")
    
    return redirect(url_for('main.services'))

@main.route('/services/delete/<int:id>', methods=['POST'])
@login_required
def delete_service(id):
    service = Service.query.get_or_404(id)
    
    try:
        db.session.delete(service)
        db.session.commit()
        flash('Service deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting service', 'danger')
        print(f"Error: {str(e)}")
    
    return redirect(url_for('main.services'))

@main.route('/orders')
@login_required
def orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    products = Product.query.all()  # For the create order form
    return render_template('orders.html', orders=orders, products=products)

@main.route('/orders/create', methods=['POST'])
@login_required
def create_order():
    try:
        if not request.is_json:
            return jsonify({'error': 'Content type must be application/json'}), 400

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        customer_name = data.get('customer_name')
        customer_phone = data.get('customer_phone')
        items = data.get('items', [])
        
        if not customer_name or not items:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Calculate total amount and validate items
        total_amount = 0
        order_items = []
        
        for item in items:
            item_type = item.get('type')
            item_id = item.get('id')
            quantity = item.get('quantity', 1)
            
            if item_type == 'product':
                product = Product.query.get(item_id)
                if not product:
                    return jsonify({'error': f'Product {item_id} not found'}), 404
                
                if product.stock < quantity:
                    return jsonify({'error': f'Insufficient stock for {product.name}'}), 400
                
                total_amount += product.price * quantity
                order_items.append({
                    'type': 'product',
                    'item': product,
                    'quantity': quantity,
                    'price': product.price
                })
            
            elif item_type == 'service':
                service = Service.query.get(item_id)
                if not service:
                    return jsonify({'error': f'Service {item_id} not found'}), 404
                
                if not service.is_active:
                    return jsonify({'error': f'Service {service.name} is not available'}), 400
                
                total_amount += service.price * quantity
                order_items.append({
                    'type': 'service',
                    'item': service,
                    'quantity': quantity,
                    'price': service.price
                })
            else:
                return jsonify({'error': f'Invalid item type: {item_type}'}), 400

        # Create order
        order = Order(
            customer_name=customer_name,
            customer_phone=customer_phone,
            total_amount=total_amount,
            status='pending'
        )
        db.session.add(order)
        db.session.flush()

        # Create order items and update stock
        for item in order_items:
            order_item = OrderItem(
                order_id=order.id,
                item_type=item['type'],
                item_id=item['item'].id,
                quantity=item['quantity'],
                price=item['price']
            )
            db.session.add(order_item)
            
            if item['type'] == 'product':
                item['item'].stock -= item['quantity']

        db.session.commit()
        return jsonify({
            'message': 'Order created successfully',
            'order_id': order.id
        })

    except Exception as e:
        db.session.rollback()
        print(f"Error creating order: {str(e)}")  # Add logging
        return jsonify({'error': 'An error occurred while creating the order'}), 500

@main.route('/orders/<int:id>/status', methods=['POST'])
@login_required
def update_order_status(id):
    order = Order.query.get_or_404(id)
    status = request.form.get('status')
    
    if status not in ['pending', 'completed', 'cancelled']:
        flash('Invalid status', 'error')
        return redirect(url_for('main.orders'))
    
    order.status = status
    db.session.commit()
    flash('Order status updated successfully', 'success')
    return redirect(url_for('main.orders'))

@main.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_profile':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if not current_user.check_password(current_password):
                flash('Current password is incorrect', 'danger')
            elif new_password != confirm_password:
                flash('New passwords do not match', 'danger')
            elif len(new_password) < 6:
                flash('Password must be at least 6 characters', 'danger')
            else:
                current_user.set_password(new_password)
                db.session.commit()
                flash('Password updated successfully', 'success')
        
        elif action == 'update_preferences':
            # Save preferences to user settings
            theme = request.form.get('theme', 'light')
            language = request.form.get('language', 'en')
            email_notifications = 'email_notifications' in request.form
            
            # You might want to add these fields to your User model
            current_user.theme = theme
            current_user.language = language
            current_user.email_notifications = email_notifications
            db.session.commit()
            flash('Preferences updated successfully', 'success')
    
    return render_template('settings.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@main.route('/test')
def test():
    return 'Flask server is running!'

@main.route('/protected-test')
@login_required
def protected_test():
    if current_user.is_authenticated:
        return f'Protected route accessed by: {current_user.username}'
    return 'Not authenticated'

@main.route('/orders/<int:id>/items')
@login_required
def get_order_items(id):
    order = Order.query.get_or_404(id)
    items_data = []
    
    for item in order.items:
        if item.item_type == 'product':
            product = Product.query.get(item.item_id)
            name = f"{product.brand} {product.name} - {product.size}"
        else:
            service = Service.query.get(item.item_id)
            name = service.name
        
        items_data.append({
            'type': item.item_type,
            'name': name,
            'quantity': item.quantity,
            'price': item.price
        })
    
    return jsonify({'items': items_data})

@main.route('/appointments')
@login_required
def appointments():
    # Get search query
    search = request.args.get('search', '').strip()
    
    # Get date range for filter
    start_date = request.args.get('start_date', datetime.today().strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', '')
    
    # Base query
    query = Appointment.query
    
    # Apply search filter
    if search:
        query = query.filter(
            db.or_(
                Appointment.customer_name.ilike(f'%{search}%'),
                Appointment.customer_phone.ilike(f'%{search}%'),
                Appointment.vehicle_model.ilike(f'%{search}%')
            )
        )
    
    # Apply date filter
    if start_date:
        query = query.filter(Appointment.appointment_date >= start_date)
    if end_date:
        query = query.filter(Appointment.appointment_date <= end_date + ' 23:59:59')
    
    # Get appointments
    appointments = query.order_by(Appointment.appointment_date).all()
    
    # Get all services for the appointment form
    services = Service.query.filter_by(is_active=True).all()
    
    return render_template('appointments.html', 
                         appointments=appointments,
                         services=services,
                         today=datetime.today(),
                         len=len)

@main.route('/appointments/create', methods=['POST'])
@login_required
def create_appointment():
    try:
        # Get form data
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        customer_name = f"{first_name} {last_name}"  # Combine names
        customer_phone = request.form.get('customer_phone')
        vehicle_brand = request.form.get('vehicle_brand')
        vehicle_model = request.form.get('vehicle_model')
        vehicle_year = request.form.get('vehicle_year')
        service_id = request.form.get('service_id')
        appointment_date = request.form.get('appointment_date')
        appointment_time = request.form.get('appointment_time')
        notes = request.form.get('notes')

        # Validate required fields
        if not all([first_name, last_name, customer_phone, vehicle_model, service_id, 
                   appointment_date, appointment_time]):
            flash('Please fill in all required fields', 'error')
            return redirect(url_for('main.appointments'))

        # Create new appointment
        appointment = Appointment(
            customer_name=customer_name,  # Use combined name
            customer_phone=customer_phone,
            vehicle_model=f"{vehicle_brand} {vehicle_model} ({vehicle_year})",  # Combine vehicle info
            service_id=service_id,
            appointment_date=datetime.strptime(f"{appointment_date} {appointment_time}", '%Y-%m-%d %H:%M'),
            notes=notes,
            status='scheduled'
        )

        db.session.add(appointment)
        db.session.commit()
        flash('Appointment created successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        flash('Error creating appointment', 'error')
        print(f"Error: {str(e)}")

    return redirect(url_for('main.appointments'))

@main.route('/appointments/<int:id>/status', methods=['POST'])
@login_required
def update_appointment_status(id):
    appointment = Appointment.query.get_or_404(id)
    status = request.form.get('status')
    
    if status in ['scheduled', 'completed', 'cancelled']:
        appointment.status = status
        db.session.commit()
        flash('Appointment status updated successfully', 'success')
    else:
        flash('Invalid status', 'error')
    
    return redirect(url_for('main.appointments'))

@main.route('/appointments/delete/<int:id>', methods=['POST'])
@login_required
def delete_appointment(id):
    appointment = Appointment.query.get_or_404(id)
    
    try:
        db.session.delete(appointment)
        db.session.commit()
        flash('Appointment deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting appointment', 'danger')
        print(f"Error: {str(e)}")
    
    return redirect(url_for('main.appointments'))

@main.route('/appointments/reschedule/<int:id>', methods=['POST'])
@login_required
def reschedule_appointment(id):
    appointment = Appointment.query.get_or_404(id)
    new_date = request.form.get('new_date')
    new_time = request.form.get('new_time')
    
    try:
        appointment_datetime = datetime.strptime(
            f"{new_date} {new_time}",
            '%Y-%m-%d %H:%M'
        )
        appointment.appointment_date = appointment_datetime
        db.session.commit()
        flash('Appointment rescheduled successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error rescheduling appointment', 'danger')
        print(f"Error: {str(e)}")
    
    return redirect(url_for('main.appointments'))

@main.route('/orders/cancel/<int:id>', methods=['POST'])
@login_required
def cancel_order(id):
    order = Order.query.get_or_404(id)
    
    if order.status == 'completed':
        flash('Cannot cancel completed order', 'danger')
        return redirect(url_for('main.orders'))
    
    try:
        # Restore product stock for cancelled order
        for item in order.items:
            if item.item_type == 'product':
                product = Product.query.get(item.item_id)
                if product:
                    product.stock += item.quantity
        
        order.status = 'cancelled'
        db.session.commit()
        flash('Order cancelled successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error cancelling order', 'danger')
        print(f"Error: {str(e)}")
    
    return redirect(url_for('main.orders'))

@main.route('/orders/edit/<int:id>', methods=['POST'])
@login_required
def edit_order(id):
    try:
        order = Order.query.get_or_404(id)
        
        order.customer_name = request.form.get('customer_name')
        order.customer_phone = request.form.get('customer_phone')
        order.total_amount = float(request.form.get('total_amount'))
        order.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Order updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating order: {str(e)}', 'danger')
        print(f"Error: {str(e)}")
    
    return redirect(url_for('main.orders'))

@main.route('/orders/delete/<int:id>', methods=['POST'])
@login_required
def delete_order(id):
    try:
        order = Order.query.get_or_404(id)
        
        # Delete associated order items first
        OrderItem.query.filter_by(order_id=order.id).delete()
        
        # Then delete the order
        db.session.delete(order)
        db.session.commit()
        flash('Order deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting order: {str(e)}', 'danger')
        print(f"Error: {str(e)}")
    
    return redirect(url_for('main.orders'))

@main.route('/orders/<int:id>/invoice')
@login_required
def view_invoice(id):
    try:
        order = Order.query.get_or_404(id)
        products = {p.id: p for p in Product.query.all()}
        services = {s.id: s for s in Service.query.all()}
        
        if request.args.get('download') == 'pdf':
            try:
                # Generate HTML
                html = render_template('invoice.html', 
                                     order=order, 
                                     products=products, 
                                     services=services,
                                     timedelta=timedelta)
                
                # Create PDF
                pdf_buffer = BytesIO()
                pisa.CreatePDF(html, dest=pdf_buffer)
                
                # Create response
                pdf_buffer.seek(0)
                response = make_response(pdf_buffer.getvalue())
                response.headers['Content-Type'] = 'application/pdf'
                response.headers['Content-Disposition'] = f'attachment; filename=invoice_{order.id}.pdf'
                return response
                
            except Exception as e:
                print(f"PDF Generation Error: {str(e)}")
                flash('Error generating PDF. Please try again.', 'danger')
                return redirect(url_for('main.orders'))
        
        return render_template('invoice.html', 
                             order=order, 
                             products=products, 
                             services=services,
                             timedelta=timedelta)
                             
    except Exception as e:
        print(f"Invoice View Error: {str(e)}")
        flash('Error viewing invoice', 'danger')
        return redirect(url_for('main.orders'))

@main.route('/appointments/edit/<int:id>', methods=['POST'])
@login_required
def edit_appointment(id):
    try:
        appointment = Appointment.query.get_or_404(id)
        
        # Get form data
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        customer_name = f"{first_name} {last_name}"
        
        appointment.customer_name = customer_name
        appointment.customer_phone = request.form.get('customer_phone')
        appointment.vehicle_model = request.form.get('vehicle_model')
        appointment.service_id = request.form.get('service_id')
        
        # Combine date and time
        date = request.form.get('appointment_date')
        time = request.form.get('appointment_time')
        appointment.appointment_date = datetime.strptime(f"{date} {time}", '%Y-%m-%d %H:%M')
        
        appointment.notes = request.form.get('notes')
        
        db.session.commit()
        flash('Appointment updated successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Error updating appointment', 'error')
        print(f"Error: {str(e)}")
    
    return redirect(url_for('main.appointments'))

@main.route('/settings/add_staff', methods=['POST'])
@login_required
def add_staff():
    if current_user.position != 'admin':
        flash('You do not have permission to add staff members.', 'danger')
        return redirect(url_for('main.settings'))
        
    if request.form['password'] != request.form['confirm_password']:
        flash('Passwords do not match.', 'danger')
        return redirect(url_for('main.settings'))
        
    try:
        new_user = User(
            username=request.form['username'],
            full_name=request.form['full_name'],
            position=request.form['position']
        )
        new_user.set_password(request.form['password'])
        db.session.add(new_user)
        db.session.commit()
        flash('Staff member added successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error adding staff member. Username might be taken.', 'danger')
        
    return redirect(url_for('main.settings'))

@main.route('/settings/toggle_user/<int:user_id>', methods=['POST'])
@login_required
def toggle_user_status(user_id):
    if current_user.position != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
        
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        return jsonify({'error': 'Cannot deactivate your own account'}), 400
        
    user.is_active = not user.is_active
    db.session.commit()
    
    return jsonify({
        'success': True,
        'is_active': user.is_active
    })

@main.route('/settings/reset_password/<int:user_id>', methods=['POST'])
@login_required
def reset_password(user_id):
    if current_user.position != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
        
    user = User.query.get_or_404(user_id)
    new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
    user.set_password(new_password)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'password': new_password
    })

@main.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@main.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

@main.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, HTTPException):
        return render_template(f'errors/{e.code}.html'), e.code
    return render_template('errors/500.html'), 500 