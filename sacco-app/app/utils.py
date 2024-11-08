# utils.py
from datetime import datetime
from flask import flash
from app.models import Notification, Message, Savings, LoanRequest, MembershipRequest
from app import db

def create_notification(user_id, message):
    """Create a notification for a user."""
    notification = Notification(user_id=user_id, message=message)
    db.session.add(notification)
    db.session.commit()

def send_group_message(user_id, group_id, content):
    """Send a message to a group chat."""
    message = Message(user_id=user_id, group_id=group_id, content=content)
    db.session.add(message)
    db.session.commit()
    return message

def create_savings_notification(user_id, amount):
    """Notify a user of successful savings deposit."""
    message = f"Your savings of {amount} has been successfully deposited."
    create_notification(user_id, message)

def create_loan_notification(user_id, loan_status):
    """Notify a user of their loan request status."""
    message = f"Your loan request has been {loan_status}."
    create_notification(user_id, message)

def create_membership_notification(user_id, group_name, status):
    """Notify a user of their membership request status."""
    message = f"Your membership request to join {group_name} has been {status}."
    create_notification(user_id, message)

def flash_error(message):
    """Flash an error message."""
    flash(message, 'danger')

def flash_success(message):
    """Flash a success message."""
    flash(message, 'success')

def format_date(date):
    """Format a date for display."""
    return date.strftime('%Y-%m-%d')

def format_time(time):
    """Format a time for display."""
    return time.strftime('%H:%M')

def log_action(action, user_id):
    """Log user actions (for future implementation of logging)."""
    # You could implement logging here if needed
    print(f"{datetime.now()}: User {user_id} performed action: {action}")
