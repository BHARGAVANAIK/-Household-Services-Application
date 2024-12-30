from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, flash, get_flashed_messages
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
from flask import send_from_directory

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')

db = SQLAlchemy(app)

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    pincode = db.Column(db.String(20), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)

class Professional(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    pincode = db.Column(db.String(20), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    service = db.relationship('Service', backref=db.backref('professionals', lazy=True))
    document = db.Column(db.String(120), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    is_rejected = db.Column(db.Boolean, default=False)

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)  
    servicename = db.Column(db.String(255), unique=True, nullable=False)  
    description = db.Column(db.String(10000), nullable=False)  
    baseprice = db.Column(db.Integer, nullable=False) 

class Booking(db.Model):
    __tablename__ = 'booking'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('professional.id'), nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String, nullable=False)
    customer = db.relationship('Customer', backref=db.backref('bookings', lazy=True))
    professional = db.relationship('Professional', backref=db.backref('bookings', lazy=True))
    review = db.relationship('Review', back_populates='booking', uselist=False)

class Review(db.Model):
    __tablename__ = 'review'
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.String(1000), nullable=True)
    booking = db.relationship('Booking', backref=db.backref('reviews', lazy=True))
    customer = db.relationship('Customer', backref=db.backref('reviews', lazy=True))

with app.app_context():
    db.create_all()
    
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if email is None or password is None:
            return "Email and Password are required."
        if email == "admin@example.com" and password == "admin123":
            session['user_type'] = 'admin'
            session['user_email'] = email
            return redirect(url_for('admin_dashboard'))
        customer = Customer.query.filter_by(email=email, password=password).first()
        if customer:
            session['user_type'] = 'customer'
            session['user_email'] = customer.email
            return redirect(url_for('customer_dashboard'))
        professional = Professional.query.filter_by(email=email, password=password).first()
        if professional:
            session['user_type'] = 'professional'
            session['user_email'] = professional.email
            return redirect(url_for('professional_dashboard'))
        return "Invalid login credentials. Please try again."
    return render_template('login.html')

@app.route('/customer_dashboard', methods=['GET'])
def customer_dashboard():
    if 'user_type' in session and session['user_type'] == 'customer':
        customer = Customer.query.filter_by(email=session['user_email']).first()
        confirmed_bookings = Booking.query.filter_by(customer_id=customer.id, status='Confirmed').all()
        return render_template('customer_dashbaord.html', customer=customer, bookings=confirmed_bookings)

@app.route('/professional_dashboard', methods=['GET'])
def professional_dashboard():
    if 'user_type' in session and session['user_type'] == 'professional':
        professional = Professional.query.filter_by(email=session['user_email']).first()
        if not professional.is_approved:
            flash('Your account is not yet approved by the admin.Please wait for some more time for verification Thank you', 'danger')
            return redirect(url_for('login'))
        bookings = Booking.query.filter_by(professional_id=professional.id).all()
        reviews = Review.query.filter(Review.booking.has(professional_id=professional.id)).all()
        return render_template('professional_dashboard.html', professional=professional, bookings=bookings, reviews=reviews)
    return redirect(url_for('login'))

@app.route('/admin_dashboard', methods=['GET'])
def admin_dashboard():
    if 'user_type' in session and session['user_type'] == 'admin':
        pending_professionals = Professional.query.filter_by(is_approved=False, is_rejected=False).all()
        return render_template('admin_dashbaord.html', pending_professionals=pending_professionals)
    return redirect(url_for('login'))

@app.route('/approve_professional/<int:professional_id>', methods=['POST'])
def approve_professional(professional_id):
    if 'user_type' in session and session['user_type'] == 'admin':
        professional = Professional.query.get_or_404(professional_id)
        professional.is_approved = True
        db.session.commit()
        flash(f'{professional.name} has been approved.', 'success')
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('login'))

@app.route('/reject_professional/<int:professional_id>', methods=['POST'])
def reject_professional(professional_id):
    if 'user_type' in session and session['user_type'] == 'admin':
        professional = Professional.query.get_or_404(professional_id)
        professional.is_rejected = True 
        db.session.commit()
        flash(f'{professional.name} has been rejected.', 'danger')
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('login'))

@app.route('/admin_transaction', methods=['GET'])
def admin_transaction():
    bookings = Booking.query.all()
    return render_template('admin_transaction.html', bookings=bookings)

@app.route('/customer_register', methods=['GET', 'POST'])
def customer_register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        name = request.form['name']
        address = request.form['address']
        pincode = request.form['pincode']
        phone_number = request.form['phone_number']
        new_customer = Customer(email=email, password=password, name=name, address=address, pincode=pincode,phone_number=phone_number)
        db.session.add(new_customer)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('customer_reg.html')

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/professional_register', methods=['GET', 'POST'])
def professional_register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        name = request.form['name']
        address = request.form['address']
        pincode = request.form['pincode']
        service_name = request.form['service']
        document = request.files['document']
        phone_number = request.form['phone_number']
        existing_professional = Professional.query.filter_by(email=email).first()
        if existing_professional:
            flash('Email is already registered. Please use a different email.', 'danger')
            return redirect(url_for('professional_register'))
        service = Service.query.filter_by(servicename=service_name).first()
        if document and allowed_file(document.filename):
            document_path = os.path.join(app.config['UPLOAD_FOLDER'], document.filename)
            document.save(document_path)
            new_professional = Professional(email=email, password=password, name=name, address=address, pincode=pincode, service=service, document=document.filename,phone_number=phone_number)
            db.session.add(new_professional)
            db.session.commit()
        return redirect(url_for('login'))
    services = Service.query.all()
    return render_template('professional_reg.html', services=services)

@app.route('/add_service', methods=['GET', 'POST'])
def new_service():
    if request.method == 'POST':
        servicename = request.form['servicename']
        description = request.form['description']
        baseprice = request.form['baseprice']
        new_service = Service(servicename=servicename,description=description,baseprice=baseprice)
        db.session.add(new_service)
        db.session.commit()
        return redirect(url_for('new_service')) 
    return render_template('new_service.html')

@app.route('/search', methods=['GET', 'POST'])
def admin_search():
    results = None
    user_type = None
    if request.method == 'POST':
        user_type = request.form.get('entityType')  
        search_by = request.form.get('searchBy')
        search_input = request.form.get('searchInput')
        if not user_type or not search_by or not search_input:
            return "All fields are required.", 400
        if user_type == 'customer':
            if search_by == 'name':
                results = Customer.query.filter(Customer.name.ilike(f'%{search_input}%')).all()
            elif search_by == 'address':
                results = Customer.query.filter(Customer.address.ilike(f'%{search_input}%')).all()
            elif search_by == 'pincode':
                results = Customer.query.filter_by(pincode=search_input).all()
        elif user_type == 'professional':
            if search_by == 'name':
                results = Professional.query.filter(Professional.name.ilike(f'%{search_input}%')).all()
            elif search_by == 'service':
                results = Professional.query.join(Service).filter(Service.servicename.ilike(f'%{search_input}%')).all()
            elif search_by == 'address':
                results = Professional.query.filter(Professional.address.ilike(f'%{search_input}%')).all()
            elif search_by == 'pincode':
                results = Professional.query.filter_by(pincode=search_input).all()
        if not results:
            return render_template('admin_search.html', message="No results found.", user_type=user_type)
    return render_template('admin_search.html', results=results, user_type=user_type)

@app.route('/customer_search', methods=['GET', 'POST'])
def customer_search():
    results = None
    reviews_data = {}  
    if request.method == 'POST':
        search_by = request.form['searchBy']
        search_input = request.form['searchinput']
        if search_by == 'service_name':
            results = Professional.query.join(Service).filter(Service.servicename.ilike(f'%{search_input}%'),Professional.is_approved == True).all()
        elif search_by == 'pincode':
            results = Professional.query.filter_by(pincode=search_input,is_approved=True).all()
        for professional in results:
            reviews = Review.query.filter(
                Review.booking.has(professional_id=professional.id)).all()
            reviews_data[professional.id] = reviews
    return render_template('customer_search.html', results=results, reviews_data=reviews_data)

@app.route('/professional_search', methods=['GET', 'POST'])
def professional_search():
    results = None
    if request.method == 'POST':
        search_by = request.form['searchBy']
        search_input = request.form['searchinput']
        if search_by == 'Location name': 
            results = Customer.query.filter_by(address=search_input).all()
        elif search_by == 'pincode':
            results = Customer.query.filter_by(pincode=search_input).all() 
        elif search_by == 'date':
            pass
    return render_template('professional_search.html', results=results)

@app.route('/edit_customer_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_email' not in session or session.get('user_type') != 'customer':
        return redirect(url_for('login'))
    customer = Customer.query.filter_by(email=session['user_email']).first()
    if request.method == 'POST':
        customer.name = request.form['name']
        customer.address = request.form['address']
        customer.pincode = request.form['pincode']
        customer.phone_number = request.form['phone_number']
        customer.password = request.form['password']
        db.session.commit()
        return redirect(url_for('customer_dashboard'))
    return render_template('edit_customer_profile.html', customer=customer)

@app.route('/edit_professional_profile', methods=['GET', 'POST'])
def edit_professional_profile():
    if 'user_email' not in session or session.get('user_type') != 'professional':
        return redirect(url_for('login'))
    professional = Professional.query.filter_by(email=session['user_email']).first()
    if request.method == 'POST':
        professional.name = request.form['name']
        professional.address = request.form['address']
        professional.pincode = request.form['pincode']
        professional.phone_number = request.form['phone_number']
        professional.password = request.form['password']
        db.session.commit()
        return redirect(url_for('professional_dashboard'))
    return render_template('edit_professional_profile.html', professional=professional)

@app.route('/book_professional/<int:professional_id>', methods=['GET', 'POST'])
def book_professional(professional_id):
    professional = Professional.query.get_or_404(professional_id)
    service = professional.service
    if request.method == 'POST':
        customer = Customer.query.filter_by(email=session['user_email']).first()
        if customer:
            new_booking = Booking(customer_id=customer.id, professional_id=professional.id, status='Pending')
            db.session.add(new_booking)
            db.session.commit()
            return redirect(url_for('customer_dashboard')) 
    return render_template('book_professional.html', professional=professional,service=service)

@app.route('/accept_booking/<int:booking_id>', methods=['POST'])
def accept_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.professional.email == session.get('user_email'):
        booking.status = 'Confirmed'
        db.session.commit()
        return redirect(url_for('professional_dashboard'))
    return "Unauthorized", 403

@app.route('/complete_booking/<int:booking_id>', methods=['POST'])
def complete_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.professional.email == session.get('user_email'):
        booking.status = 'Completed'
        db.session.commit()
        return redirect(url_for('professional_dashboard'))
    return "Unauthorized", 403

@app.route('/cancel_booking/<int:booking_id>', methods=['POST'])
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.professional.email == session.get('user_email'):
        booking.status = 'Cancelled'
        db.session.commit()
        return redirect(url_for('professional_dashboard'))
    return "Unauthorized", 403

@app.route('/submit_review/<int:booking_id>', methods=['GET', 'POST'])
def submit_review(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.status != 'Confirmed':
        return "Review cannot be submitted for this booking.", 403
    if request.method == 'POST':
        customer = Customer.query.filter_by(email=session['user_email']).first()
        if not customer:
            return "Customer not found.", 404
        existing_review = Review.query.filter_by(booking_id=booking.id, customer_id=customer.id).first()
        if existing_review:
            return "You have already submitted a review for this booking.", 403
        rating = request.form['rating']
        comment = request.form.get('comment', '')
        new_review = Review(booking_id=booking.id, customer_id=customer.id, rating=rating, comment=comment)
        db.session.add(new_review)
        db.session.commit()
        return redirect(url_for('customer_dashboard'))
    return render_template('submit_review.html', booking=booking)

@app.route('/customer_summary', methods=['GET'])
def customer_summary():
    customer = Customer.query.filter_by(email=session['user_email']).first()
    bookings = Booking.query.filter_by(customer_id=customer.id).all()
    confirmed_bookings = [booking for booking in bookings if booking.status == 'Confirmed']
    cancelled_bookings = [booking for booking in bookings if booking.status == 'Cancelled']
    ratings = []
    for booking in bookings:
        if booking.reviews:
            for review in booking.reviews:
                ratings.append({'professional': booking.professional, 'value': review.rating})
    return render_template('customer_summary.html', customer=customer, bookings=bookings, ratings=ratings, confirmed_bookings=confirmed_bookings,cancelled_bookings=cancelled_bookings)

@app.route('/professional_summary', methods=['GET'])
def professional_summary():
    professional = Professional.query.filter_by(email=session['user_email']).first()
    bookings = Booking.query.filter_by(professional_id=professional.id).all()
    ratings = []
    for booking in bookings:
        if booking.reviews:
            for review in booking.reviews:
                ratings.append(review.rating)
    confirmed_bookings = [booking for booking in bookings if booking.status == 'Confirmed']  
    cancelled_bookings = [booking for booking in bookings if booking.status == 'Cancelled']  
    return render_template('professional_summary.html', professional=professional, bookings=bookings, ratings=ratings, confirmed_bookings=confirmed_bookings,cancelled_bookings=cancelled_bookings)

@app.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)