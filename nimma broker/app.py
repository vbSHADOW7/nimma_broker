from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Property, Contact, Admin
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nimma_broker.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
db.init_app(app)

# Initialize database
with app.app_context():
    db.create_all()
    if not Admin.query.first():
        admin = Admin(username='admin', password=generate_password_hash('admin123'))
        db.session.add(admin)
        db.session.commit()

# Public Routes
@app.route('/')
def home():
    properties = Property.query.limit(3).all()
    return render_template('public/index.html', properties=properties)

@app.route('/properties')
def properties():
    properties = Property.query.all()
    return render_template('public/properties.html', properties=properties)

@app.route('/services')
def services():
    return render_template('public/services.html')

@app.route('/about')
def about():
    return render_template('public/about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        contact = Contact(
            name=request.form['name'],
            email=request.form['email'],
            message=request.form['message']
        )
        db.session.add(contact)
        db.session.commit()
        flash('Message sent successfully!')
        return redirect(url_for('contact'))
    return render_template('public/contact.html')

# Admin Routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        admin = Admin.query.filter_by(username=request.form['username']).first()
        if admin and check_password_hash(admin.password, request.form['password']):
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        flash('Invalid credentials')
    return render_template('admin/login.html')

@app.route('/admin')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    properties = Property.query.all()
    contacts = Contact.query.all()
    return render_template('admin/dashboard.html', properties=properties, contacts=contacts)

@app.route('/admin/property/add', methods=['GET', 'POST'])
def add_property():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    if request.method == 'POST':
        file = request.files['image']
        filename = file.filename if file else None
        if filename:
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        property = Property(
            title=request.form['title'],
            description=request.form['description'],
            price=float(request.form['price']),
            location=request.form['location'],
            image=filename
        )
        db.session.add(property)
        db.session.commit()
        flash('Property added successfully!')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/add_property.html')

@app.route('/admin/property/delete/<int:id>', methods=['POST'])
def delete_property(id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    property = Property.query.get_or_404(id)
    db.session.delete(property)
    db.session.commit()
    flash('Property deleted successfully!')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/contact/delete/<int:id>', methods=['POST'])
def delete_contact(id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    contact = Contact.query.get_or_404(id)
    db.session.delete(contact)
    db.session.commit()
    flash('Contact message deleted successfully!')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
