from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired


class FeedbackForm(FlaskForm):
    email = StringField('email', validators=[DataRequired()])
    content = TextAreaField("Содержание")
    name = StringField('имя пользователя', validators=[DataRequired()])
    submit = SubmitField('Отправить')
