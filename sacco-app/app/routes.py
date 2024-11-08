from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user, logout_user, login_user
from app import app, db
from app.models import Group, Meeting, Notification, Message, User, MembershipRequest, LoanRequest, Savings, Loan
from app.forms import GroupForm, MeetingForm, SavingsForm, RegistrationForm, LoginForm
from flask_socketio import SocketIO, emit
import requests
from config import Config  # Import the Config class for settings
import logging
import pyotp
from flask_mail import Mail, Message


socketio = SocketIO(app)
mail = Mail(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create group
@app.route('/group/create', methods=['GET', 'POST'])
@login_required
def create_group():
    form = GroupForm()
    if form.validate_on_submit():
        group = Group(name=form.name.data, description=form.description.data, admin=current_user.id)
        db.session.add(group)
        db.session.commit()
        flash('Group created successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('create_group.html', form=form)

@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')
# Schedule meeting
@app.route('/group/<int:group_id>/meeting', methods=['GET', 'POST'])
@login_required
def schedule_meeting(group_id):
    form = MeetingForm()
    if form.validate_on_submit():
        meeting = Meeting(
            title=form.title.data,
            date=form.date.data,
            time=form.time.data,
            description=form.description.data,
            group_id=group_id
        )
        db.session.add(meeting)
        db.session.commit()

        # Notify all group members
        group = Group.query.get(group_id)
        for member in group.members:
            create_notification(member.id, f"Meeting scheduled: {meeting.title} on {meeting.date} at {meeting.time}")

        flash('Meeting scheduled and notifications sent!', 'success')
        return redirect(url_for('group', group_id=group_id))
    return render_template('schedule_meeting.html', form=form)

# Group chat
@app.route('/group/<int:group_id>/chat')
@login_required
def group_chat(group_id):
    group = Group.query.get_or_404(group_id)
    return render_template('group_chat.html', group=group)

# WebSocket for chat
@socketio.on('message', namespace='/group/<int:group_id>/chat')
def handle_chat_message(data):
    emit('message', data, broadcast=True)
@app.route('/dashboard')
def dashboard():
    # This is where you can pass in data to the dashboard template if needed
    return render_template('dashboard.html')
# View notifications
@app.route('/notifications', methods=['GET'])
@login_required
def view_notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id).all()
    return render_template('notifications.html', notifications=notifications)

# Admin dashboard
@app.route('/admin/dashboard/<int:group_id>', methods=['GET'])
@login_required
def admin_dashboard(group_id):
    group = Group.query.get_or_404(group_id)
    if group.admin != current_user.id:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('group', group_id=group_id))

    notifications = Notification.query.filter_by(user_id=current_user.id).all()
    return render_template('admin_dashboard.html', group=group, notifications=notifications)

# Promote user to admin
@app.route('/group/<int:group_id>/promote_admin/<int:user_id>', methods=['POST'])
@login_required
def promote_admin(group_id, user_id):
    group = Group.query.get_or_404(group_id)
    if current_user.id == group.admin:  # Only current admin can promote
        if user_id not in [member.id for member in group.members]:
            return jsonify({"error": "User not in group"}), 400
        group.admin = user_id  # Update admin
        db.session.commit()
        flash('User promoted to admin!', 'success')
        return jsonify({"success": True}), 200
    return jsonify({"error": "Unauthorized"}), 403

# Function to create notifications
def create_notification(user_id, message):
    notification = Notification(user_id=user_id, message=message)
    db.session.add(notification)
    db.session.commit()


# Logout Route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

# Savings Route
@app.route('/savings', methods=['GET', 'POST'])
@login_required
def savings():
    form = SavingsForm()
    if form.validate_on_submit():
        amount = form.amount.data
        transaction_id = initiate_mpesa_transaction(current_user.phone_number, amount)

        # Create savings record
        savings_record = Savings(user_id=current_user.id, amount=amount, transaction_id=transaction_id)
        db.session.add(savings_record)
        db.session.commit()

        flash('Savings transaction initiated! Please complete the payment.', 'info')
        return redirect(url_for('savings'))

    # Retrieve current user's savings
    current_savings = Savings.query.filter_by(user_id=current_user.id).all()
    return render_template('savings.html', form=form, savings=current_savings)

def initiate_mpesa_transaction(phone_number, amount):
    headers = {
        'Authorization': f'Bearer {get_mpesa_token()}',
        'Content-Type': 'application/json'
    }
    payload = {
        'amount': amount,
        'phone_number': phone_number,
        'shortcode': Config.MPESA_SHORTCODE,
        'transaction_type': 'CustomerPayBillOnline'
    }
    response = requests.post(Config.MPESA_PAYBILL_URL, json=payload, headers=headers)
    
    if response.status_code == 200:
        transaction_id = response.json().get('transaction_id')
        return transaction_id  # Return the actual transaction ID from M-Pesa
    return None  # Handle error case appropriately

def get_mpesa_token():
    auth = requests.auth.HTTPBasicAuth(Config.MPESA_CONSUMER_KEY, Config.MPESA_CONSUMER_SECRET)
    response = requests.get(Config.MPESA_TOKEN_URL, auth=auth)
    return response.json().get('access_token')  # Return the access token for M-Pesa API

@app.route('/mpesa/callback', methods=['POST'])
def mpesa_callback():
    data = request.json
    transaction_id = data['transaction_id']
    status = data['status']

    # Update savings record based on transaction status
    savings_record = Savings.query.filter_by(transaction_id=transaction_id).first()
    if savings_record:
        savings_record.payment_status = status
        db.session.commit()
        if status == 'completed':
            flash('Savings successfully updated!', 'success')
        else:
            flash('Payment not completed. Please try again.', 'danger')
    return jsonify({"status": "ok"})

# Admin Approve Loans
@app.route('/admin/approve_loans', methods=['GET'])
@login_required
def approve_loans():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))

    loan_requests = LoanRequest.query.filter_by(status='pending').all()
    return render_template('approve_loans.html', loan_requests=loan_requests)

@app.route('/admin/approve_loan/<int:loan_id>', methods=['POST'])
@login_required
def approve_loan(loan_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))

    loan_request = LoanRequest.query.get_or_404(loan_id)
    loan_request.status = 'approved'
    db.session.commit()
    flash('Loan request approved successfully.', 'success')
    return redirect(url_for('approve_loans'))

@app.route('/admin/reject_loan/<int:loan_id>', methods=['POST'])
@login_required
def reject_loan(loan_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))

    loan_request = LoanRequest.query.get_or_404(loan_id)
    loan_request.status = 'rejected'
    db.session.commit()
    flash('Loan request rejected successfully.', 'danger')
    return redirect(url_for('approve_loans'))

@app.route('/admin/admit_members', methods=['GET'])
@login_required
def admit_members():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))

    membership_requests = MembershipRequest.query.filter_by(status='pending').all()
    return render_template('admit_members.html', membership_requests=membership_requests)

@app.route('/admin/admit_member/<int:user_id>', methods=['POST'])
@login_required
def admit_member(user_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))

    membership_request = MembershipRequest.query.filter_by(user_id=user_id, status='pending').first_or_404()
    membership_request.status = 'admitted'
    db.session.commit()
    flash('Member admitted successfully.', 'success')
    return redirect(url_for('admit_members'))

@app.route('/admin/reject_membership/<int:user_id>', methods=['POST'])
@login_required
def reject_membership(user_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))

    membership_request = MembershipRequest.query.filter_by(user_id=user_id, status='pending').first_or_404()
    membership_request.status = 'rejected'
    db.session.commit()
    flash('Membership request rejected successfully.', 'danger')
    return redirect(url_for('admit_members'))

if __name__ == '__main__':
    socketio.run(app, debug=True)


# Function to send verification email
def send_verification_email(user):
    verification_code = pyotp.random_base32()  # Generate a random verification code
    user.two_factor_secret = verification_code
    db.session.commit()
    
    # Send the verification email
    msg = Message('Account Verification', sender=Config.MAIL_DEFAULT_SENDER, recipients=[user.email])
    msg.body = f"Your verification code is: {verification_code}"
    mail.send(msg)
    logger.info(f"Sent verification email to {user.email}")

# Registration Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = form.password.data  # Ensure to hash the password
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()

        logger.info(f"User {user.username} registered successfully.")
        send_verification_email(user)  # Send verification code

        flash('Registration successful! A verification code has been sent to your email.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

# Verify account with MFA
@app.route('/verify_account', methods=['GET', 'POST'])
def verify_account():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    if request.method == 'POST':
        verification_code = request.form.get('verification_code')
        if verification_code == current_user.two_factor_secret:
            current_user.is_mfa_enabled = True  # Enable MFA
            db.session.commit()
            flash('Account verified successfully! You can now log in with MFA enabled.', 'success')
            logger.info(f"User {current_user.username} verified their account.")
            return redirect(url_for('login'))
        else:
            flash('Invalid verification code. Please try again.', 'danger')
            logger.warning(f"Failed verification attempt for user {current_user.username}.")

    return render_template('verify_account.html')

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.password == form.password.data:  # Use hashed password check
            if user.is_mfa_enabled:
                # MFA verification process here
                return redirect(url_for('mfa_verification'))  # Redirect to MFA page
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Login unsuccessful. Please check email and password.', 'danger')
            logger.warning(f"Failed login attempt for email: {form.email.data}")

    return render_template('login.html', form=form)

# MFA Verification Route
@app.route('/mfa_verification', methods=['GET', 'POST'])
@login_required
def mfa_verification():
    if request.method == 'POST':
        mfa_code = request.form.get('mfa_code')
        totp = pyotp.TOTP(current_user.two_factor_secret)
        if totp.verify(mfa_code):
            login_user(current_user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid MFA code. Please try again.', 'danger')
            logger.warning(f"Failed MFA verification for user {current_user.username}.")
    
    return render_template('mfa_verification.html')