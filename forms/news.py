from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms import BooleanField, SubmitField
from wtforms.validators import DataRequired


class SectionForm(FlaskForm):
    title = StringField('Название', validators=[DataRequired()])
    about = TextAreaField("Немного о разделе")
    submit = SubmitField('Применить')