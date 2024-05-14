from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DateField
from wtforms.validators import Length, EqualTo, Email, DataRequired, ValidationError
from anomalyDetector.db.models import User
from anomalyDetector.db.db import session




class RegisterForm(FlaskForm):
    def validate_username(self, username_to_check):
        user = session.query(User).filter(User.username == username_to_check.data).first()
        if user:
            raise ValidationError('Username already exists! Please try a different username')

    def validate_email_address(self, email_address_to_check):
        email_address = session.query(User).filter(User.email_address == email_address_to_check.data).first()
        if email_address:
            raise ValidationError('Email Address already exists! Please try a different email address')

    username = StringField(label='User Name:', validators=[Length(min=2, max=30), DataRequired()])
    email_address = StringField(label='Email Address:', validators=[Email(), DataRequired()])
    password1 = PasswordField(label='Password:', validators=[Length(min=6), DataRequired()])
    password2 = PasswordField(label='Confirm Password:', validators=[EqualTo('password1'), DataRequired()])
    submit = SubmitField(label='Create Account')


class LoginForm(FlaskForm):
    username = StringField(label='User Name:', validators=[DataRequired()])
    password = PasswordField(label='Password:', validators=[DataRequired()])
    submit = SubmitField(label='Sign in') 


class DataIngestionForm(FlaskForm):
    start_date = DateField('Start at')
    end_date = DateField('End at')
    submit = SubmitField('Start data ingestion')

class DataAvailabilityForm(FlaskForm):
    start_date = DateField('Start at')
    end_date = DateField('End at')
    submit = SubmitField('Start checking data availability')

class BaseModelForm(FlaskForm):
    start_date = DateField('Start at')
    end_date = DateField('End at')
    submit = SubmitField('Start detecting anomalies')        