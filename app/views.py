from urllib.parse import urlsplit
from flask import render_template, redirect, url_for, flash, request, session, jsonify
from sqlalchemy import or_
from app import app
from app.forms import *
from app.models import *
from flask_login import current_user, login_user, logout_user, login_required
import numpy
import os
from app.tags import *
from app.add_items import *
from app.recently_added import *
from app.recommender import *
from app.get_info import *
import time

@app.route('/index', methods=["GET", "POST"])
@app.route('/', methods=["GET", "POST"])
def index():
    """
    Serves the / and /index endpoints. Contains the RecommenderForm which can be used by users to generate a knowledge
    graph of recommendations.
    :return: Renders the 'index.html' template.
    """
    form = RecommenderForm()
    if form.validate_on_submit():
        session['form_data'] = request.form
        return redirect(url_for('visualise'))
    return render_template('index.html', form=form)


@app.route('/register', methods=["GET", "POST"])
def register():
    """
    Serves the /register endpoint. Contains a RegistrationForm which the user can use to sign up to the web application.
    :return: Renders the 'register.html' template.
    """
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        new_user = User(username=form.username.data, email=form.email.data,
                        password_hash=generate_password_hash(form.password.data, salt_length=32))
        db.session.add(new_user)
        try:
            db.session.commit()
            flash(f'Registration successful!', 'success')
            return redirect(url_for('index'))
        except:
            db.session.rollback()
            if User.query.filter_by(username=form.username.data):
                form.username.errors.append('This username is already taken. Please choose another')
            if User.query.filter_by(email=form.email.data):
                form.email.errors.append('This email address is already registered. Please choose another')
            flash(f'Registration failed', 'danger')
    return render_template('register.html', title='Register', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """
    Serves the '/login' endpoint. Contains a LoginForm to allow users to log into the application.
    :return: Renders the 'login.html' template.
    """
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        flash(f'Login for {user.username}', 'success')
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Login', form=form)


@app.route('/logout')
def logout():
    """
    Logs out the user.
    :return: Redirects the user to the index endpoint.
    """
    logout_user()
    return redirect(url_for('index'))


@app.route('/about')
def about():
    """
    Serves as the endpoint for the about page.
    :return: Renders the 'about.html' template.
    """
    return render_template('about.html')


@app.route('/visualise', methods=["GET"])
def visualise():
    """
    Serves the '/visualise' endpoint. Generates a knowledge graph of recommendations for users based on the information
    supplied in the form on the index endpoint.
    :return: Renders the 'visualise.html' template.
    """
    form_data = session.get('form_data', None)

    # Get item entry from database. Return an error if the item is not found.
    if form_data['medium'] == "book":
        item = Books.query.filter(Books.title.ilike(f'%{form_data['title']}%')).first()
    elif form_data['medium'] == "film":
        item = Films.query.filter(Films.title.ilike(f'%{form_data['title']}%')).first()
    else:
        item = Games.query.filter(Games.title.ilike(f'%{form_data['title']}%')).first()

    if not item:
        flash("No such item in the database, please add the item and then search for it again", "danger")
        return redirect(url_for('index'))

    # Generate graph based on the found item using the recommender.py module.
    graph = generate_graph(item.id, form_data['medium'], form_data['weighting'], form_data['top_nodes'])

    #Convert data to JSON to be passed to the front end for rendering.
    db_entries = database_info(graph.nodes)
    db_entries = json.dumps(db_entries)
    graph = serialise_graph(graph)
    graph_json = json.dumps(graph)

    return render_template("visualise.html", form_data=form_data,
                           graph=graph_json, db=db_entries)


@app.route('/search_items', methods=["GET", "POST"])
def search_items():
    """
    Serves the '/search_items' endpoint of the website. Contains a SearchForm object allowing the users to specify
    a search term which is used to generate search results by querying the items in the database.
    If this form validates, the user is redirected to the '/search_results' endpoint.
    :return: Renders the 'search_items.html' template.
    """
    form = SearchForm()
    if form.validate_on_submit():
        search_terms = form.query.data
        return redirect(url_for('search_results', query=search_terms))
    return render_template('search_items.html', title='Search', form=form)


@app.route('/search_results', methods=["GET", "POST"])
def search_results():
    """
    Serves the '/search_results' endpoint of the website. Generates a list of search results which are then passed to the
    front-end to be rendered for the user.
    :return: Renders the 'search_results.html' template.
    """

    #Get the search term requested by the user.
    query = request.args.get('query')

    #Create an instance of the TagsForm which will be used to allow users to update tags on items while browsing search results.
    form = TagsForm()
    if form.validate_on_submit():
        add_tags(form.data, form.id.data, form.type.data)
        redirect(url_for('search_results'))

    #Use queries to generate search results.
    books = Books.query.filter(or_(Books.title.ilike(f'%{query}%'), Books.author.ilike(f'%{query}%'))).all()
    films = Films.query.filter(or_(Films.title.ilike(f'%{query}%'), Films.director.ilike(f'%{query}%'))).all()
    games = Games.query.filter(or_(Games.title.ilike(f'%{query}%'), Games.developer.ilike(f'%{query}%'))).all()

    #Search based on potential tags
    for word in query.split(" "):
        tags = Tags.query.filter(Tags.tag.ilike(f'%{word}%')).all()
        for tag in tags:
            item_tag = ItemTags.query.filter_by(tag_id=tag.tag_id).all()
            for itag in item_tag:
                if itag:
                    if itag.item_type == "book":
                        book = Books.query.filter_by(id=itag.item_id).first()
                        if book not in books:
                            books.append(book)
                    elif itag.item_type == "film":
                        film = Films.query.filter_by(id=itag.item_id).first()
                        if film not in films:
                            films.append(film)
                    else:
                        game = Games.query.filter_by(id=itag.item_id).first()
                        if game not in games:
                            games.append(game)
    search_results = []

    #Serialise results to be passed to the front end.
    for book in books:
        tags = db.session.query(Tags.tag, ItemTags.count, Tags.tag_id).join(ItemTags).filter(ItemTags.item_id == book.id, ItemTags.item_type == 'book').all()
        search_results.append({
            'type': 'book',
            'item': {'id': book.id, 'title': book.title, 'author': book.author, 'isbn': book.isbn, 'cover': book.cover, 'type': 'book'},
            'tags': [{'tag': tag[0], 'count': tag[1], 'id': tag[2]} for tag in tags],
        })

    for film in films:
        tags = db.session.query(Tags.tag, ItemTags.count, Tags.tag_id).join(ItemTags).filter(ItemTags.item_id == film.id, ItemTags.item_type == 'film').all()
        search_results.append({
            'type': 'film',
            'item': {'id': film.id, 'title': film.title, 'director': film.director, 'year': film.year, 'cover': film.cover, 'type': 'film'},
            'tags': [{'tag': tag[0], 'count': tag[1], 'id': tag[2]} for tag in tags],
        })

    for game in games:
        tags = db.session.query(Tags.tag, ItemTags.count, Tags.tag_id).join(ItemTags).filter(ItemTags.item_id == game.id, ItemTags.item_type == 'game').all()
        search_results.append({
            'type': 'game',
            'item': {'id': game.id, 'title': game.title, 'developer': game.developer, 'year': game.year, 'cover': game.cover, 'type': 'game'},
            'tags': [{'tag': tag[0], 'count': tag[1], 'id': tag[2]} for tag in tags],
        })
    return render_template('search_results.html', search_results=search_results, query=query, books=books,
                           films=films, games=games, current_user=current_user, form=form)


@app.route('/add_book', methods=["GET", "POST"])
@login_required
def add_book():
    """
    Serves the '/add_book' endpoint of the website. Contains an instance of the BookForm() which the user can fill in
    to add a new book item and tags to the database.
    :return: Renders the 'add_book.html' template.
    """
    form = BookForm()
    if form.validate_on_submit():
        add_book_to_database(form.data)
    return render_template('add_book.html', book_form=form)

@app.route('/add_film', methods=["GET", "POST"])
def add_film():
    """
    Serves the '/add_film' endpoint of the website. Contains an instance of the FilmForm() which the user can fill in
    to add a new film item and tags to the database.
    :return: Renders the 'add_film.html' template.
    """
    form = FilmForm()
    if form.validate_on_submit():
        add_film_to_database(form.data)
    return render_template('add_film.html', film_form=form)


@app.route('/add_game', methods=["GET", "POST"])
@login_required
def add_game():
    """
    Serves the '/add_game' endpoint of the website. Contains an instance of the GameForm() which the user can fill in
    to add a new game item and tags to the database.
    :return: Renders the 'add_game.html' template.
    """
    form = GameForm()
    if form.validate_on_submit():
        add_game_to_database(form.data)
    else:
        print("NO")
    return render_template('add_game.html', game_form=form)


@app.route('/update_tag', methods=["GET", "POST"])
@login_required
def update_tag():
    """
    Serves the '/update_tag' endpoint of the website. THis is called by the JS code on the 'search_results.html' page.
    This provides the functionality for users to upvote and remove tags they have added to items by clicking on the
    tags buttons present on the search results.
    :return: Response to the request by the client in the JSON format.
    """

    #Retrieve request from front end.
    data = request.json

    #Check if the user has upvoted this tag.
    updated = UserUpvotes.query.filter_by(user_id=data['user_id'], item_id=data['item_id'], item_type=data['item_type'],
                                          tag_id=data['tag_id']).first()

    #If the user has upvoted this tag, decrement the count. If the count is 0, remove the tag.
    if updated:
        db.session.delete(updated)
        itag = ItemTags.query.filter_by(item_id=data['item_id'], item_type=data['item_type'], tag_id=data['tag_id']).first()
        itag.count -= 1
        if itag.count == 0:
            db.session.delete(itag)

    #Otherwise, the user has not upvoted this tag. Increment the count and create a record that the user has upvoted this tag.
    else:
        updated = UserUpvotes(user_id=data['user_id'], item_id=data['item_id'], item_type=data['item_type'],
                              tag_id=data['tag_id'], timestamp=int(time.time()))
        db.session.add(updated)
        itag = ItemTags.query.filter_by(item_id=data['item_id'], item_type=data['item_type'], tag_id=data['tag_id']).first()
        itag.count += 1
    try:
        db.session.commit()
        return jsonify({'status': 'success', 'new_count': itag.count})
    except:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': 'Update failed'})


@app.errorhandler(413)
def error_413(error):
    return render_template('errors/413.html'), 413


@app.errorhandler(400)
def error_400(error):
    return render_template('errors/400.html'), 400


@app.errorhandler(403)
def error_403(error):
    return render_template('errors/403.html'), 403


@app.errorhandler(404)
def error_404(error):
    return render_template('errors/404.html'), 404