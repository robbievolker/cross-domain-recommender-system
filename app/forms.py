from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, BooleanField, TextAreaField, DecimalField, IntegerRangeField
from wtforms.fields.choices import SelectField
from wtforms.fields.simple import HiddenField
from wtforms.validators import DataRequired, EqualTo, Email, Optional, NumberRange


class RecommenderForm(FlaskForm):
    """
    A user form used on the index endpoint. This form allows the user to specify a title which will serve as the initial node
    on the knowledge graph generated by the recommender system.

    :param: title: The title of the item.
    :param: medium: Whether the item is a book, film or game.
    :param: weighting: The strength of recommendations requested by the user.
    :param: top_nodes: The size of the graph.
    """
    title = StringField('Title', validators=[DataRequired()])
    medium = SelectField('Medium', choices=[('film', 'Film'), ('game', 'Game'), ('book', 'Book')], validators=[DataRequired()])
    weighting = DecimalField('Enter weighting value between 1-10 (a higher value means items with a stronger similarity will be recommended)', validators=[NumberRange(min=0, max=10)])
    top_nodes = IntegerField('Maximum graph size (number between 1-10)', default=5, validators=[DataRequired(), NumberRange(min=1, max=10)])
    submit = SubmitField('Visualise Results')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match.')])
    submit = SubmitField('Create Account')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password')
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')


class BookForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    author = StringField('Author', validators=[Optional()])
    publisher = StringField('Publisher (optional)', validators=[Optional()])
    tags = TextAreaField('Please enter any tags (space separated)', validators=[DataRequired()],  render_kw={"placeholder": "eg. sci-fi action"})
    submit = SubmitField('Add Book')


class FilmForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    director = StringField('Director', validators=[Optional()])
    year = IntegerField('Year (optional)', validators=[Optional()])
    production_company = StringField('Production Company (optional)', validators=[Optional()])
    tags = TextAreaField('Please enter any tags (space separated)', validators=[DataRequired()], render_kw={"placeholder": "eg. sci-fi action"})
    submit = SubmitField('Add Film')


class GameForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    year = IntegerField('Year', validators=[DataRequired()])
    developer = StringField(' (optional)', validators=[Optional()])
    tags = TextAreaField('Please enter any tags (space separated)', validators=[DataRequired()], render_kw={"placeholder": "eg. sci-fi action"})
    submit = SubmitField('Add Game')


class SearchForm(FlaskForm):
    query = StringField('Search Term', validators=[DataRequired()])
    submit = SubmitField('Search')


class TagsForm(FlaskForm):
    id = HiddenField("id")
    type = HiddenField("type")
    tags = TextAreaField('Please enter any tags (space separated)', validators=[DataRequired()], render_kw={"placeholder": "eg. sci-fi action"})
    submit = SubmitField('Add Tags')
