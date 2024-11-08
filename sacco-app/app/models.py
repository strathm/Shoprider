from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

# User Model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), default='member')  # 'admin' or 'member'
    two_factor_secret = db.Column(db.String(32), nullable=True)  # Secret for MFA
    is_mfa_enabled = db.Column(db.Boolean, default=False)  # Flag for MFA

    # Financial fields
    savings = db.Column(db.Float, default=0.0)  # Total savings by the user
    earnings = db.Column(db.Float, default=0.0)  # Total earnings from interest distributions

    # Relationships
    groups = db.relationship('Group', backref='creator', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)
    messages = db.relationship('Message', backref='sender', lazy=True)
    membership_requests = db.relationship('MembershipRequest', backref='user', lazy=True)
    loan_requests = db.relationship('LoanRequest', backref='member', lazy=True)
    savings_transactions = db.relationship('Savings', backref='member', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'


# MembershipRequest Model
class MembershipRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'admitted', 'rejected'
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())


# LoanRequest Model
class LoanRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)  # Principal loan amount
    interest_rate = db.Column(db.Float, nullable=False, default=0.05)  # Interest rate on the loan (5% default)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'rejected', 'paid'
    total_repayment = db.Column(db.Float, nullable=False)  # Principal + interest
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def calculate_repayment(self):
        return self.amount * (1 + self.interest_rate)

    def __repr__(self):
        return f'<LoanRequest {self.amount}>'


# Savings Model (Tracking individual savings transactions)
class Savings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)  # Amount saved
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f'<Savings {self.amount}>'


# Group Model
class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    admin = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    members = db.relationship('User', secondary='group_members', lazy='subquery',
        backref=db.backref('member_groups', lazy=True))


# Association Table for Group Members
group_members = db.Table('group_members',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('group_id', db.Integer, db.ForeignKey('group.id'), primary_key=True)
)


# Meeting Model
class Meeting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    description = db.Column(db.Text, nullable=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# Notification Model
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


# Message Model for Group Chat
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)


class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    borrower_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # User requesting the loan
    group_id = db.Column(db.Integer, db.ForeignKey('bulkgroup.id'), nullable=False)  # Group associated with the loan
    amount = db.Column(db.Float, nullable=False)  # Loan amount requested
    interest_rate = db.Column(db.Float, nullable=False, default=10.0)  # Default interest rate (can be modified)
    repayment_period = db.Column(db.Integer, nullable=False)  # Repayment period in months
    status = db.Column(db.String(20), nullable=False, default='pending')  # Loan status: pending, approved, rejected, paid
    requested_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)  # Date when loan was requested
    approved_at = db.Column(db.DateTime, nullable=True)  # Date when loan was approved (optional)
    paid_at = db.Column(db.DateTime, nullable=True)  # Date when loan was fully repaid (optional)
    total_paid = db.Column(db.Float, default=0.0)  # Amount paid back by the borrower
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # Administrator who approves/rejects the loan
    
    borrower = db.relationship('User', foreign_keys=[borrower_id], backref='loans')
    group = db.relationship('BulkGroup', backref='loans')
    admin = db.relationship('User', foreign_keys=[admin_id], backref='administered_loans')

    def calculate_total_due(self):
        """Calculate the total amount due with interest."""
        return self.amount * (1 + self.interest_rate / 100)

    def is_fully_paid(self):
        """Check if the loan has been fully paid."""
        return self.total_paid >= self.calculate_total_due()

    def approve(self, admin_id):
        """Approve the loan."""
        self.status = 'approved'
        self.approved_at = datetime.utcnow()
        self.admin_id = admin_id

    def reject(self):
        """Reject the loan."""
        self.status = 'rejected'

    def make_payment(self, amount):
        """Record a payment towards the loan."""
        self.total_paid += amount
        if self.is_fully_paid():
            self.status = 'paid'
            self.paid_at = datetime.utcnow()
