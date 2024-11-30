from flask import Blueprint, render_template, jsonify, request, abort, send_file
from flask_login import login_required, current_user
from functools import wraps
from models import db, User, FormData
import csv
from io import StringIO
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/admin/export')
@login_required
@admin_required
def export_data():
    # Create a string buffer to write CSV data
    si = StringIO()
    writer = csv.writer(si)
    
    # Write headers
    writer.writerow([
        'Date Submitted', 'Student Name', 'Date of Birth', 'Address',
        'Parent/Guardian', 'Parent Cell', 'Home Phone', 'Emergency Contact',
        'Emergency Phone', 'Medical Info', 'Doctor Info', 'Insurance',
        'Payment Status'
    ])
    
    # Get all form submissions
    forms = FormData.query.all()
    
    # Write data rows
    for form in forms:
        writer.writerow([
            form.date_submitted.strftime('%Y-%m-%d'),
            form.student_name,
            form.date_of_birth,
            f"{form.street}, {form.city}, {form.zip_code}",
            form.parent_guardian,
            form.parent_cell_phone,
            form.home_phone,
            form.emergency_contact,
            form.emergency_phone,
            f"Treatment: {'Yes' if form.current_treatment else 'No'}, Details: {form.treatment_details or 'N/A'}",
            f"Doctor: {form.family_doctor}, Phone: {form.doctor_phone}",
            f"Company: {form.insurance_company}, Policy: {form.policy_number}",
            'Paid' if form.payment_status else 'Pending'
        ])
    
    # Create the response
    output = si.getvalue()
    si.close()
    
    # Generate filename with current date
    filename = f"registrations_{datetime.now().strftime('%Y%m%d')}.csv"
    
    # Create response with CSV data
    return send_file(
        StringIO(output),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )

@admin_bp.route('/admin/dashboard')
@login_required
@admin_required
def dashboard():
    registrations = FormData.query.all()
    return render_template('admin/dashboard.html', registrations=registrations)

@admin_bp.route('/admin/users')
@login_required
@admin_required
def user_management():
    users = User.query.all()
    return render_template('admin/user_management.html', users=users)

@admin_bp.route('/admin/user/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
@admin_required
def toggle_admin(user_id):
    if user_id == current_user.id:
        return jsonify({'success': False, 'message': 'Cannot modify your own admin status'}), 400
    
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    try:
        user.is_admin = data['is_admin']
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/admin/user/<int:user_id>/forms')
@login_required
@admin_required
def user_forms(user_id):
    user = User.query.get_or_404(user_id)
    forms = FormData.query.filter_by(user_id=user_id).all()
    return render_template('admin/user_forms_partial.html', forms=forms, user=user)

@admin_bp.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    if user_id == current_user.id:
        return jsonify({'success': False, 'message': 'Cannot delete your own account'}), 400
    
    user = User.query.get_or_404(user_id)
    
    try:
        # Delete associated forms first
        FormData.query.filter_by(user_id=user_id).delete()
        db.session.delete(user)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
