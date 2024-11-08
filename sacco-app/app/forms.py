from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, DateField, TimeField, DecimalField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, NumberRange

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=150)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=150)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class GroupForm(FlaskForm):
    name = StringField('Group Name', validators=[DataRequired(), Length(min=2, max=150)])
    description = TextAreaField('Description', validators=[Length(max=500)])
    submit = SubmitField('Create Group')

class MeetingForm(FlaskForm):
    title = StringField('Meeting Title', validators=[DataRequired(), Length(min=2, max=150)])
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])
    time = TimeField('Time', format='%H:%M', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Length(max=500)])
    submit = SubmitField('Schedule Meeting')

class MessageForm(FlaskForm):
    content = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Send Message')

# New form for savings deposits
class SavingsForm(FlaskForm):
    amount = DecimalField('Amount', validators=[DataRequired(), NumberRange(min=0, message="Amount must be positive")])
    submit = SubmitField('Deposit')

# New form for loan requests
class LoanRequestForm(FlaskForm):
    amount = DecimalField('Loan Amount', validators=[DataRequired(), NumberRange(min=1, message="Loan amount must be positive")])
    purpose = TextAreaField('Purpose of Loan', validators=[DataRequired(), Length(max=500)])
    submit = SubmitField('Request Loan')

# New form for membership requests
class MembershipRequestForm(FlaskForm):
    group_id = SelectField('Select Group', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Request Membership')

# Admin form to admit/reject members
class MembershipApprovalForm(FlaskForm):
    action = SelectField('Action', choices=[('approve', 'Approve'), ('reject', 'Reject')], validators=[DataRequired()])
    submit = SubmitField('Submit Decision')

