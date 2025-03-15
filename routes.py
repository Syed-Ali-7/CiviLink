import os
import random
from datetime import datetime, timedelta
import base64
from io import BytesIO
from flask import render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from app import app, storage
from models import User
from database import get_db
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
            user_type = request.form.get('user_type', 'citizen')
            
            if not is_valid_phone(phone):
                flash('Please enter a valid phone number', 'danger')
                return render_template('login.html')
            
            # Normalize the phone number
            phone = normalize_phone(phone)
            
            # Check if trying to log in as BBMP officer but account doesn't exist
            if user_type in ['officer', 'admin'] and (phone not in storage.users or storage.users[phone].get('role') not in ['officer', 'admin']):
                flash('Access denied. This phone number is not registered as a BBMP officer.', 'danger')
                return render_template('login.html')
            
            # Generate and store OTP
            otp = generate_otp()
            storage.otps[phone] = (otp, datetime.now())
            
            # In a real app, we would send the OTP via SMS
            # For hackathon, we'll just show it
            flash(f'Your OTP is: {otp}', 'info')
            return render_template('login.html', phone=phone, user_type=user_type, show_otp_form=True)
            
        elif action == 'verify_otp':
            phone = request.form.get('phone')
            otp = request.form.get('otp')
            user_type = request.form.get('user_type', 'citizen')
            
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
                return render_template('login.html', phone=phone, user_type=user_type, show_otp_form=True)
            
            # OTP is valid, check if user exists
            if phone in storage.users:
                user_data = storage.users[phone]
                user = User(
                    id=phone,
                    phone=phone,
                    name=user_data.get('name'),
                    ward=user_data.get('ward'),
                    role=user_data.get('role', 'citizen'),
                    employee_id=user_data.get('employee_id'),
                    department=user_data.get('department')
                )
                user.issues_reported = user_data.get('issues_reported', 0)
                user.issues_resolved = user_data.get('issues_resolved', 0)
                user.stars = user_data.get('stars', 0)
            else:
                # Create new user
                user = User(id=phone, phone=phone)
                storage.users[phone] = {
                    'phone': phone,
                    'issues_reported': 0,
                    'issues_resolved': 0,
                    'stars': 0,
                    'role': 'citizen',  # Default role
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
    # Different dashboard views for citizens and officers
    is_officer = current_user.is_officer()
    
    # Get filter parameters
    status_filter = request.args.get('status')
    ward_filter = request.args.get('ward')
    department_filter = request.args.get('department')
    
    # Base issues list
    if is_officer:
        # Officers only see issues from their ward or department by default
        if current_user.ward and not ward_filter:
            ward_filter = current_user.ward
        
        if current_user.department and not department_filter:
            department_filter = current_user.department
                    
        # Get all issues for admins, or filtered by ward/department for other officers
        if current_user.is_admin():
            all_issues = storage.issues  # Admins see all issues
        else:
            # Regular officers see issues from their ward or department
            all_issues = [i for i in storage.issues if 
                         (i.get('ward') == current_user.ward) or 
                         (i.get('department') == current_user.department) or
                         (i.get('assigned_to') == current_user.id)]
    else:
        # Citizens see all issues by default
        all_issues = storage.issues
        
        # But allow them to filter by their ward
        if not ward_filter and current_user.ward:
            ward_filter = current_user.ward
    
    # Sort by recency
    all_issues = sorted(all_issues, key=lambda x: x['timestamp'], reverse=True)
    
    # Apply ward filter if specified
    if ward_filter:
        all_issues = [i for i in all_issues if i.get('ward') == ward_filter]
        
    # Apply department filter if specified (for officers)
    if department_filter and is_officer:
        all_issues = [i for i in all_issues if i.get('department') == department_filter]
    
    # Apply status filter if specified
    if status_filter and status_filter != 'all':
        all_issues = [i for i in all_issues if i['status'] == status_filter]
    
    # Dashboard stats
    stats = {
        'total': len(all_issues),
        'not_resolved': sum(1 for issue in all_issues if issue['status'] == 'not_resolved'),
        'ongoing': sum(1 for issue in all_issues if issue['status'] == 'ongoing'),
        'resolved': sum(1 for issue in all_issues if issue['status'] == 'resolved')
    }
    
    # Additional stats for officers
    if is_officer:
        # Get issues assigned to this officer
        issues_assigned_to_me = [i for i in storage.issues if i.get('assigned_to') == current_user.id]
        stats.update({
            'assigned_to_me': len(issues_assigned_to_me),
            'resolved_by_me': sum(1 for issue in issues_assigned_to_me if issue['status'] == 'resolved')
        })
    
    # Format datetime for display
    for issue in all_issues:
        issue['formatted_time'] = format_datetime(issue['timestamp'])
        if 'assigned_time' in issue:
            issue['formatted_assigned_time'] = format_datetime(issue['assigned_time'])
    
    return render_template('dashboard.html', 
                           issues=all_issues, 
                           stats=stats,
                           is_officer=is_officer,
                           departments=storage.departments if is_officer else [],
                           wards=storage.wards,
                           current_filter=status_filter or 'all',
                           current_ward=ward_filter or '',
                           current_department=department_filter or '',
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
        
        # Get latitude and longitude from form
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        
        if not all([title, category, description, location, ward]):
            flash('Please fill all required fields', 'danger')
            return render_template('report_issue.html')
        
        if not image_data:
            flash('Please upload an image of the issue', 'danger')
            return render_template('report_issue.html')
            
        if not latitude or not longitude:
            flash('Please select a location on the map', 'danger')
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
            'latitude': float(latitude),
            'longitude': float(longitude),
            'image': encoded_image,
            'status': 'not_resolved',
            'timestamp': datetime.now().isoformat(),
            'reviews': [],
            'comments': []
        }
        
        conn = get_db()
        c = conn.cursor()
        c.execute('''
            INSERT INTO issues (
                user_id, user_name, title, category, description, 
                location, ward, latitude, longitude, image, 
                status, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            current_user.id, current_user.name, title, category, description,
            location, ward, float(latitude), float(longitude), encoded_image,
            'not_resolved', datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
        
        # Add issue to storage.issues list
        new_issue = {
            'id': issue_id,
            'user_id': current_user.id,
            'user_name': current_user.name,
            'title': title,
            'category': category,
            'description': description,
            'location': location,
            'ward': ward,
            'latitude': float(latitude),
            'longitude': float(longitude),
            'image': encoded_image,
            'status': 'not_resolved',
            'timestamp': datetime.now().isoformat(),
            'reviews': [],
            'comments': [],
            'department': None,
            'assigned_to': None,
            'assigned_to_name': None,
            'assigned_time': None
        }
        storage.issues.append(new_issue)
        
        # Update user's issues reported count and stars
        if 'issues_reported' not in storage.users[current_user.id]:
            storage.users[current_user.id]['issues_reported'] = 0
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
    
    # Check if user is officer
    is_officer = current_user.is_officer()
    
    # Get list of officers who could be assigned to this issue
    officers = []
    if is_officer:
        # Filter officers by department if issue has a department assigned
        department = issue.get('department')
        if not department and issue.get('category'):
            # Map the issue category to a department if not set
            category_to_dept = {
                'Road Damage': 'Road Infrastructure',
                'Garbage Collection': 'Solid Waste Management',
                'Streetlight Issue': 'Engineering',
                'Water Supply Problem': 'Water Supply',
                'Sewage Overflow': 'Sewage and Drainage',
                'Illegal Construction': 'Town Planning',
                'Park Maintenance': 'Horticulture',
                'Public Toilet Issue': 'Health',
                'Stray Animal Concern': 'Health',
                'Tree Hazard': 'Horticulture'
            }
            department = category_to_dept.get(issue.get('category'))
            
            # Update the issue with the determined department
            if department and not issue.get('department'):
                issue['department'] = department
        
        officers = storage.get_officers_by_department(department)
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_status' and (is_officer or issue['user_id'] == current_user.id):
            new_status = request.form.get('status')
            status_note = request.form.get('status_note', '').strip()
            
            if new_status in ['not_resolved', 'ongoing', 'resolved']:
                # If updating to resolved status, require a photo (only for officers)
                if new_status == 'resolved':
                    if not is_officer:
                        flash('Only BBMP officers can mark issues as resolved', 'danger')
                        return redirect(url_for('issue_details', issue_id=issue_id))
                    
                    resolved_photo = request.files.get('resolved_photo')
                    
                    # Check if the issue already has a resolved photo
                    has_resolved_photo = issue.get('resolved_image') is not None
                    
                    # Require a new photo if one doesn't already exist
                    if not has_resolved_photo and not resolved_photo:
                        flash('Please upload a photo showing the resolved issue', 'danger')
                        return redirect(url_for('issue_details', issue_id=issue_id))
                    
                    # Process the new photo if provided
                    if resolved_photo:
                        compressed_image = compress_image(resolved_photo.read())
                        encoded_image = base64.b64encode(compressed_image).decode('utf-8')
                        issue['resolved_image'] = encoded_image
                        issue['resolved_photo_timestamp'] = datetime.now().isoformat()
                        issue['resolved_by'] = current_user.id
                        issue['resolved_by_name'] = current_user.name
                        
                        # Update officer's resolved issues count
                        if current_user.id in storage.users:
                            storage.users[current_user.id]['issues_resolved'] = storage.users[current_user.id].get('issues_resolved', 0) + 1
                            current_user.issues_resolved += 1
                
                # Update the status and note
                issue['status'] = new_status
                issue['status_updated'] = datetime.now().isoformat()
                issue['status_updated_by'] = current_user.id
                
                # Save the status note if provided
                if status_note:
                    issue['status_note'] = status_note
                
                flash('Issue status updated', 'success')
        
        elif action == 'assign_officer' and is_officer:
            officer_id = request.form.get('officer_id')
            
            if officer_id and officer_id in storage.users:
                officer = storage.users[officer_id]
                # Assign the issue
                issue['assigned_to'] = officer_id
                issue['assigned_to_name'] = officer.get('name')
                issue['assigned_time'] = datetime.now().isoformat()
                issue['assigned_by'] = current_user.id
                
                # Set to ongoing when assigned
                if issue['status'] == 'not_resolved':
                    issue['status'] = 'ongoing'
                    issue['status_updated'] = datetime.now().isoformat()
                
                flash(f'Issue assigned to {officer.get("name")}', 'success')
            else:
                flash('Invalid officer selection', 'danger')
        
        elif action == 'add_department' and is_officer:
            department = request.form.get('department')
            
            if department in storage.departments:
                issue['department'] = department
                flash('Department updated successfully', 'success')
            else:
                flash('Invalid department selection', 'danger')
        
        elif action == 'add_review' and issue['status'] == 'resolved':
            # Only citizens can add reviews
            if is_officer:
                flash('Only citizens can review resolved issues', 'warning')
                return redirect(url_for('issue_details', issue_id=issue_id))
                
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
        
        elif action == 'add_comment':
            comment = request.form.get('comment', '').strip()
            
            if not comment:
                flash('Comment cannot be empty', 'danger')
            else:
                if 'comments' not in issue:
                    issue['comments'] = []
                
                issue['comments'].append({
                    'user_id': current_user.id,
                    'user_name': current_user.name,
                    'role': current_user.role,
                    'text': comment,
                    'timestamp': datetime.now().isoformat()
                })
                
                flash('Comment added successfully', 'success')
    
    # Format datetime for display
    issue['formatted_time'] = format_datetime(issue['timestamp'])
    
    # Format status updated time if it exists
    if 'status_updated' in issue:
        issue['formatted_status_time'] = format_datetime(issue['status_updated'])
    
    # Format assigned time if it exists
    if 'assigned_time' in issue:
        issue['formatted_assigned_time'] = format_datetime(issue['assigned_time'])
    
    # Format resolved photo timestamp if it exists
    if 'resolved_photo_timestamp' in issue:
        issue['formatted_resolved_time'] = format_datetime(issue['resolved_photo_timestamp'])
    
    # Format comment timestamps
    if 'comments' in issue:
        for comment in issue['comments']:
            comment['formatted_time'] = format_datetime(comment['timestamp'])
    
    # Format review timestamps
    for review in issue['reviews']:
        review['formatted_time'] = format_datetime(review['timestamp'])
    
    return render_template('issue_details.html', 
                           issue=issue, 
                           is_officer=is_officer,
                           officers=officers,
                           departments=storage.departments,
                           get_status_color=get_issue_status_color,
                           format_datetime=format_datetime)
