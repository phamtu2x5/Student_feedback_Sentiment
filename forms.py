from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from models import User

class RegistrationForm(FlaskForm):
    username = StringField('Tên đăng nhập', validators=[
        DataRequired(message='Vui lòng nhập tên đăng nhập'),
        Length(min=3, max=20, message='Tên đăng nhập phải từ 3-20 ký tự')
    ])
    
    password = PasswordField('Mật khẩu', validators=[
        DataRequired(message='Vui lòng nhập mật khẩu'),
        Length(min=6, message='Mật khẩu phải có ít nhất 6 ký tự')
    ])
    
    confirm_password = PasswordField('Xác nhận mật khẩu', validators=[
        DataRequired(message='Vui lòng xác nhận mật khẩu'),
        EqualTo('password', message='Mật khẩu xác nhận không khớp')
    ])
    
    submit = SubmitField('Đăng ký')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Tên đăng nhập đã tồn tại. Vui lòng chọn tên khác.')

class LoginForm(FlaskForm):
    username = StringField('Tên đăng nhập', validators=[
        DataRequired(message='Vui lòng nhập tên đăng nhập')
    ])
    
    password = PasswordField('Mật khẩu', validators=[
        DataRequired(message='Vui lòng nhập mật khẩu')
    ])
    
    submit = SubmitField('Đăng nhập')

class FeedbackForm(FlaskForm):
    text = TextAreaField('Feedback của bạn', validators=[
        DataRequired(message='Vui lòng nhập feedback'),
        Length(min=10, max=1000, message='Feedback phải từ 10-1000 ký tự')
    ])
    
    submit = SubmitField('Phân Tích Feedback')
