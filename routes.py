import os
import random
from datetime import datetime, timedelta
import base64
from io import BytesIO
from flask import render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from app import app, storage
from models import User
from utils import (
    generate_otp, is_valid_phone, normalize_phone, 
    compress_image, get_issue_status_color, 
    calculate_stars, format_datetime
)

# Home page route
@app.route('/')
def index():
    # Get latest 3 issues for display
    recent_issues = sorted(
        storage.issues, 
        key=lambda x: x['timestamp'], 
        reverse=True
    )[:3]
    
    # Count issues by status
    stats = {
        'total': len(storage.issues),
        'not_resolved': sum(1 for issue in storage.issues if issue['status'] == 'not_resolved'),
        'ongoing': sum(1 for issue in storage.issues if issue['status'] == 'ongoing'),
        'resolved': sum(1 for issue in storage.issues if issue['status'] == 'resolved')
    }
    
    return render_template('index.html', 
                           recent_issues=recent_issues, 
                           stats=stats, 
                           get_status_color=get_issue_status_color,
                           format_datetime=format_datetime)

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'send_otp':
            phone = request.form.get('phone')
            
            if not is_valid_phone(phone):
                flash('Please enter a valid phone number', 'danger')
                return render_template('login.html')
            
            # Normalize the phone number
            phone = normalize_phone(phone)
            
            # Generate and store OTP
            otp = generate_otp()
            storage.otps[phone] = (otp, datetime.now())
            
            # In a real app, we would send the OTP via SMS
            # For hackathon, we'll just show it
            flash(f'Your OTP is: {otp}', 'info')
            return render_template('login.html', phone=phone, show_otp_form=True)
            
        elif action == 'verify_otp':
            phone = request.form.get('phone')
            otp = request.form.get('otp')
            
            if phone not in storage.otps:
                flash('Please request a new OTP', 'danger')
                return render_template('login.html')
            
            stored_otp, timestamp = storage.otps[phone]
            
            # Check if OTP is expired (5 minutes validity)
            if datetime.now() - timestamp > timedelta(minutes=5):
                flash('OTP has expired. Please request a new one', 'danger')
                del storage.otps[phone]
                return render_template('login.html')
            
            if otp != stored_otp:
                flash('Invalid OTP. Please try again', 'danger')
                return render_template('login.html', phone=phone, show_otp_form=True)
            
            # OTP is valid, check if user exists
            if phone in storage.users:
                user = User(
                    id=phone,
                    phone=phone,
                    name=storage.users[phone].get('name'),
                    ward=storage.users[phone].get('ward')
                )
                user.issues_reported = storage.users[phone].get('issues_reported', 0)
                user.stars = storage.users[phone].get('stars', 0)
            else:
                # Create new user
                user = User(id=phone, phone=phone)
                storage.users[phone] = {
                    'phone': phone,
                    'issues_reported': 0,
                    'stars': 0,
                    'created_at': datetime.now().isoformat()
                }
            
            # Log in the user
            login_user(user)
            del storage.otps[phone]
            
            # If user doesn't have name/ward, redirect to complete profile
            if not storage.users[phone].get('name') or not storage.users[phone].get('ward'):
                flash('Please complete your profile', 'info')
                return redirect(url_for('profile'))
            
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
    
    return render_template('login.html')

# Signup route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'send_otp':
            phone = request.form.get('phone')
            
            if not is_valid_phone(phone):
                flash('Please enter a valid phone number', 'danger')
                return render_template('signup.html')
            
            # Normalize the phone number
            phone = normalize_phone(phone)
            
            # Check if user already exists
            if phone in storage.users:
                flash('User with this phone number already exists. Please login.', 'warning')
                return redirect(url_for('login'))
            
            # Generate and store OTP
            otp = generate_otp()
            storage.otps[phone] = (otp, datetime.now())
            
            # In a real app, we would send the OTP via SMS
            # For hackathon, we'll just show it
            flash(f'Your OTP is: {otp}', 'info')
            return render_template('signup.html', phone=phone, show_otp_form=True)
            
        elif action == 'verify_otp':
            phone = request.form.get('phone')
            otp = request.form.get('otp')
            
            if phone not in storage.otps:
                flash('Please request a new OTP', 'danger')
                return render_template('signup.html')
            
            stored_otp, timestamp = storage.otps[phone]
            
            # Check if OTP is expired (5 minutes validity)
            if datetime.now() - timestamp > timedelta(minutes=5):
                flash('OTP has expired. Please request a new one', 'danger')
                del storage.otps[phone]
                return render_template('signup.html')
            
            if otp != stored_otp:
                flash('Invalid OTP. Please try again', 'danger')
                return render_template('signup.html', phone=phone, show_otp_form=True)
            
            # OTP is valid, show profile completion form
            del storage.otps[phone]
            return render_template('signup.html', phone=phone, show_profile_form=True)
            
        elif action == 'complete_profile':
            phone = request.form.get('phone')
            name = request.form.get('name')
            ward = request.form.get('ward')
            
            if not name or not ward:
                flash('Please fill all required fields', 'danger')
                return render_template('signup.html', phone=phone, show_profile_form=True)
            
            # Create new user
            storage.users[phone] = {
                'phone': phone,
                'name': name,
                'ward': ward,
                'issues_reported': 0,
                'stars': 0,
                'created_at': datetime.now().isoformat()
            }
            
            user = User(id=phone, phone=phone, name=name, ward=ward)
            login_user(user)
            
            flash('Account created successfully!', 'success')
            return redirect(url_for('dashboard'))
    
    return render_template('signup.html')

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

# Dashboard route
@app.route('/dashboard')
@login_required
def dashboard():
    # Get all issues, sorted by recency
    all_issues = sorted(
        storage.issues, 
        key=lambda x: x['timestamp'], 
        reverse=True
    )
    
    # Stats for dashboard
    stats = {
        'total': len(all_issues),
        'not_resolved': sum(1 for issue in all_issues if issue['status'] == 'not_resolved'),
        'ongoing': sum(1 for issue in all_issues if issue['status'] == 'ongoing'),
        'resolved': sum(1 for issue in all_issues if issue['status'] == 'resolved')
    }
    
    # Filter by status if requested
    status_filter = request.args.get('status')
    if status_filter and status_filter != 'all':
        filtered_issues = [i for i in all_issues if i['status'] == status_filter]
    else:
        filtered_issues = all_issues
    
    # Format datetime for display
    for issue in filtered_issues:
        issue['formatted_time'] = format_datetime(issue['timestamp'])
    
    return render_template('dashboard.html', 
                           issues=filtered_issues, 
                           stats=stats,
                           current_filter=status_filter or 'all',
                           get_status_color=get_issue_status_color)

# Profile route
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        name = request.form.get('name')
        ward = request.form.get('ward')
        
        if not name or not ward:
            flash('Please fill all required fields', 'danger')
            return render_template('profile.html')
        
        # Update user profile
        storage.users[current_user.id]['name'] = name
        storage.users[current_user.id]['ward'] = ward
        current_user.name = name
        current_user.ward = ward
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    
    # Get user's reported issues
    user_issues = [issue for issue in storage.issues if issue['user_id'] == current_user.id]
    user_issues.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Format datetime for display
    for issue in user_issues:
        issue['formatted_time'] = format_datetime(issue['timestamp'])
    
    return render_template('profile.html', 
                           user=current_user, 
                           issues=user_issues,
                           get_status_color=get_issue_status_color)

# Report issue route
@app.route('/report', methods=['GET', 'POST'])
@login_required
def report_issue():
    if request.method == 'POST':
        title = request.form.get('title')
        category = request.form.get('category')
        description = request.form.get('description')
        location = request.form.get('location')
        ward = request.form.get('ward')
        image_data = request.files.get('image')
        
        if not all([title, category, description, location, ward]):
            flash('Please fill all required fields', 'danger')
            return render_template('report_issue.html')
        
        if not image_data:
            flash('Please upload an image of the issue', 'danger')
            return render_template('report_issue.html')
        
        # Compress and encode the image
        compressed_image = compress_image(image_data.read())
        encoded_image = base64.b64encode(compressed_image).decode('utf-8')
        
        # Create new issue
        issue_id = storage.issue_counter
        storage.issue_counter += 1
        
        new_issue = {
            'id': issue_id,
            'user_id': current_user.id,
            'user_name': current_user.name,
            'title': title,
            'category': category,
            'description': description,
            'location': location,
            'ward': ward,
            'image': encoded_image,
            'status': 'not_resolved',
            'timestamp': datetime.now().isoformat(),
            'reviews': []
        }
        
        storage.issues.append(new_issue)
        
        # Update user's issues reported count and stars
        storage.users[current_user.id]['issues_reported'] += 1
        current_user.issues_reported += 1
        
        # Calculate stars based on issues reported
        new_stars = calculate_stars(current_user.issues_reported)
        storage.users[current_user.id]['stars'] = new_stars
        current_user.stars = new_stars
        
        flash('Issue reported successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('report_issue.html')

# Issue details route
@app.route('/issue/<int:issue_id>', methods=['GET', 'POST'])
@login_required
def issue_details(issue_id):
    # Find the issue by ID
    issue = next((i for i in storage.issues if i['id'] == issue_id), None)
    
    if not issue:
        flash('Issue not found', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_status':
            new_status = request.form.get('status')
            if new_status in ['not_resolved', 'ongoing', 'resolved']:
                issue['status'] = new_status
                issue['status_updated'] = datetime.now().isoformat()
                flash('Issue status updated', 'success')
        
        elif action == 'add_review' and issue['status'] == 'resolved':
            rating = int(request.form.get('rating', 0))
            comment = request.form.get('comment', '')
            
            if not 1 <= rating <= 5:
                flash('Please provide a valid rating', 'danger')
            else:
                review = {
                    'user_id': current_user.id,
                    'user_name': current_user.name,
                    'rating': rating,
                    'comment': comment,
                    'timestamp': datetime.now().isoformat()
                }
                
                issue['reviews'].append(review)
                flash('Review added successfully!', 'success')
    
    # Format datetime for display
    issue['formatted_time'] = format_datetime(issue['timestamp'])
    
    # Format review timestamps
    for review in issue['reviews']:
        review['formatted_time'] = format_datetime(review['timestamp'])
    
    return render_template('issue_details.html', 
                           issue=issue, 
                           get_status_color=get_issue_status_color)
