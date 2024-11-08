# services.py
from app.models import Group, User, Notification, Meeting, Message, Savings, LoanRequest, MembershipRequest, Loan
from app import db
from flask_login import current_user
from datetime import datetime

class GroupService:
    @staticmethod
    def create_group(name, description):
        group = Group(name=name, description=description, admin=current_user.id)
        db.session.add(group)
        db.session.commit()
        return group

    @staticmethod
    def add_member(group_id, user):
        group = Group.query.get(group_id)
        if user not in group.members:
            group.members.append(user)
            db.session.commit()
            return True
        return False

    @staticmethod
    def schedule_meeting(group_id, title, date, time, description):
        meeting = Meeting(
            title=title,
            date=date,
            time=time,
            description=description,
            group_id=group_id
        )
        db.session.add(meeting)
        db.session.commit()
        return meeting

    @staticmethod
    def promote_user_to_admin(group, user_id):
        group.admin = user_id
        db.session.commit()
        return group

    @staticmethod
    def approve_membership_request(group_id, user_id, approve=True):
        group = Group.query.get(group_id)
        user = User.query.get(user_id)
        if approve:
            if user not in group.members:
                group.members.append(user)
            MembershipRequest.query.filter_by(group_id=group_id, user_id=user_id).delete()
        else:
            MembershipRequest.query.filter_by(group_id=group_id, user_id=user_id).delete()
        db.session.commit()

class NotificationService:
    @staticmethod
    def create_notification(user_id, message):
        notification = Notification(user_id=user_id, message=message)
        db.session.add(notification)
        db.session.commit()

class MessageService:
    @staticmethod
    def send_message(user_id, group_id, content):
        message = Message(user_id=user_id, group_id=group_id, content=content)
        db.session.add(message)
        db.session.commit()
        return message

class SavingsService:
    @staticmethod
    def deposit_savings(user_id, amount):
        savings = Savings(user_id=user_id, amount=amount, date=datetime.utcnow())
        db.session.add(savings)
        db.session.commit()
        return savings

    @staticmethod
    def get_user_savings(user_id):
        savings = Savings.query.filter_by(user_id=user_id).all()
        return savings

class LoanService:
    @staticmethod
    def request_loan(user_id, amount, purpose):
        loan = Loan(user_id=user_id, amount=amount, purpose=purpose, status='pending', date_requested=datetime.utcnow())
        db.session.add(loan)
        db.session.commit()
        return loan

    @staticmethod
    def approve_loan(loan_id, approve=True):
        loan = Loan.query.get(loan_id)
        if approve:
            loan.status = 'approved'
        else:
            loan.status = 'rejected'
        loan.date_approved = datetime.utcnow()
        db.session.commit()
        return loan
