import requests
from app.models import *
from flask import flash
from app.tags import *
from app.recently_added import *
from datetime import *
from flask import redirect
def add_book_to_database(data):
    """
    This function adds a new book to the Books table of the database. This is accomplished by querying the Google Books API
    with the data supplied by the user. An attempt is then made to commit the new record to the database. After this, the
    tags specified by the user are added to the database, which calls the add_tags function in the tags.py module.

    :param data: The BookForm object submitted by the user and passed by the add_book endpoint in views.py.
    """

    #Prepare our query to the API.
    url = f'https://www.googleapis.com/books/v1/volumes?q=intitle:{data['title']}+inauthor:{data['author']}&key={BOOK_KEY}'
    response = requests.get(url)

    #Check the response is good, if not flash an error instructing the user to try again.
    if response.status_code == 200:
        info = response.json()

        #Check the item returned is an actual book.
        if 'items' in info and len(info['items']) > 0:
            book = info['items'][0]['volumeInfo']

            #Get the ISBN.
            isbn = book.get('industryIdentifiers', [])
            isbn_13 = next((item['identifier'] for item in isbn if item['type'] == 'ISBN_13'), None)
            isbn_10 = next((item['identifier'] for item in isbn if item['type'] == 'ISBN_10'), None)
            if isbn_10 is None and isbn_13 is None:
                final_isbn = isbn[0]['identifier'] if isbn else None
                print(final_isbn)
            else:
                final_isbn = isbn_13 or isbn_10
            print(info['items'][0]['volumeInfo'])

            #Create the new Books object which will be the record to add to the database.
            new_book = Books(
                        title=book.get('title', data['title']),
                        author=book.get('authors', [data['author']])[0],
                        year=book.get('publishedDate', 'Unknown')[:4],
                        publisher=book.get('publisher', 'Unknown'),
                        isbn=final_isbn,
                        cover=book.get('imageLinks', {}).get('thumbnail', 'default_cover_url'))

            #Check this item does not already exist in the database to avoid record duplication.
            current_book = Books.query.filter_by(title=book.get('title', data['title'])).first()

            #If the item does not already exist, attempt to add it to the database.
            if current_book == None:
                db.session.add(new_book)
                try:
                    db.session.commit()
                    bid = Books.query.filter_by(title=book.get('title', data['title'])).first()
                    add_recent([new_book.title, str("ISBN: " + new_book.isbn), new_book.cover, datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
                    flash(f'Added book to database', 'success')

                    #Call the add_tags function in tags.py to add the tags to the item.
                    add_tags(data, bid.id, "book")
                    redirect('add_book.html)')
                except:
                    #If the new item failed to be added to the database, rollback changes and notify the user.
                    db.session.rollback()
                    flash(f'Failed to add item, please try again.', 'danger')
                    redirect('add_book.html')
            else:
                #If the book is already in the database, still attempt to add the tags specified by the user.
                bid = current_book.id
                add_tags(data, bid, "book")
                flash(f'This item is already in the database. Your tags can still be addded.', 'warning')
        else:
            flash(f'Failed to find item, please try again.', 'danger')
            redirect('add_book.html')
    else:
        flash(f'Failed to find item, please try again.', 'danger')
        redirect('add_book.html')


def add_film_to_database(data):
    """
    This function adds a new film to the Films table of the database, using the information supplied by the user from the
    add_film endpoint. An attempt is then made to commit the new item to the database. After this, the tags specified by
    the user are added to the database, which calls the add_tags function in the tags.py module.

    :param data: The FilmForm object submitted by the user and passed by the add_book endpoint in views.py.
    """

    #Prepeare our query to the API.
    url = f'http://www.omdbapi.com/?i=tt3896198&apikey={FILM_KEY}&t={data['title']}'
    response = requests.get(url)

    #Check the response is good, if not flash an error instructing the user to try again.
    if response.status_code == 200:
        info = response.json()

        #Create the new Films object which will be the record to add to the database.
        new_film = Films(title=info.get('Title'), director=info.get('Director'), year=info.get('Year'),
                         production_company=info.get('Production'), cover=info.get('Poster'))
        current_film = Films.query.filter_by(title=info.get('Title'), director=info.get('Director')).first()

        #If the item does not already exist, attempt to add it to the database.
        if current_film == None:
            db.session.add(new_film)
            try:
                db.session.commit()
                fid = Films.query.filter_by(title=new_film.title).first()
                add_recent([new_film.title, new_film.year, new_film.cover, datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
                flash(f'Added film to database', 'success')

                #Call the add_tags function in tags.py to add the tags to the item.
                add_tags(data, fid.id, "film")
                redirect('add_film.html)')

            except:
                #If the new item failed to be added to the database, rollback changes and notify the user.
                db.session.rollback()
                flash(f'Failed to add item', 'danger')
                redirect('add_game.html)')
        else:
            #If the film is already in the database, still attempt to add the tags specified by the user.
            fid = current_film.id
            add_tags(data, fid, "film")
            flash(f'This item is already in the database. Your tags can still be addded.', 'warning')

    else:
        flash(f"Failed to find item. Please check the title and author and try again.", "danger")
        redirect("add_film.html")


def add_game_to_database(data):
    """
    This function adds a new game to the Games table of the database, using the information supplied by the user from the
    add_game endpoint. An attempt is then made to commit the new item to the database. After this, the tags specified by
    the user are added to the database, which calls the add_tags function in the tags.py module.

    :param data: The GameForm object submitted by the user and passed by the add_game endpoint.
    """

    #Prepare our query to the API.
    oauth = requests.post(f"https://id.twitch.tv/oauth2/token?client_id={CLIENT_ID}&client_secret={S}&grant_type=client_credentials")
    access_token = oauth.json()["access_token"]
    body = f"fields *; search \"{data['title']}\";"
    data_response = requests.post(f"https://api.igdb.com/v4/games", headers={"Client-ID": CLIENT_ID,
                             "Authorization": f"Bearer {access_token}"}, data=body)

    #Check the response is good, if not flash an error instructing the user to try again.
    if data_response.status_code == 200:
        info = data_response.json()
        if info != []:
            for response in info:
                first_release_date = response.get('first_release_date', None)
                if first_release_date is None:
                    continue
                date = datetime.fromtimestamp(first_release_date)
                if str(date.year) != str(data['year']):
                    continue

                # Fetch cover data
                c_data = f'fields *; where id = ({response["cover"]});'
                cover_response = requests.post(
                    "https://api.igdb.com/v4/covers",
                    headers={"Client-ID": CLIENT_ID, "Authorization": f"Bearer {access_token}"},
                    data=c_data
                )

                if cover_response.status_code == 200:
                    c_info = cover_response.json()

                # Fetch involved companies data
                developer_data = f'fields *; where id=({response["involved_companies"][0]});'
                developer_response = requests.post(
                    "https://api.igdb.com/v4/involved_companies",
                    headers={"Client-ID": CLIENT_ID, "Authorization": f"Bearer {access_token}"},
                    data=developer_data
                )

                if developer_response.status_code == 200:
                    involved_info = developer_response.json()

                    # Fetch company data
                    final_company_data = f'fields *; where id=({involved_info[0]["company"]});'
                    final_company_response = requests.post(
                        "https://api.igdb.com/v4/companies",
                        headers={"Client-ID": CLIENT_ID, "Authorization": f"Bearer {access_token}"},
                        data=final_company_data
                    )

                    if final_company_response.status_code == 200:
                        final_info = final_company_response.json()

                        # Create the new Games object which will be the record to add to the database.
                        new_game = Games(
                            title=response['name'],
                            year=date.year,
                            developer=final_info[0]['name'],
                            cover=c_info[0]['url']
                        )
                        current_game = Games.query.filter_by(title=response['name'], year=date.year).first()

                        # If the item does not already exist, attempt to add it to the database.
                        if current_game == None:
                            db.session.add(new_game)
                            try:
                                db.session.commit()
                                add_recent([new_game.title, new_game.year, new_game.cover, datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
                                gid = Games.query.filter_by(title=new_game.title).first()
                                flash('Added game to database', 'success')

                                # Call the add_tags function in tags.py to add the tags to the item.
                                add_tags(data, gid.id, "game")
                                redirect('add_game.html')
                                break
                            except Exception as e:
                                db.session.rollback()
                                flash(f'Failed to add item: {str(e)}', 'danger')
                                redirect('add_game.html')
                        else:
                            # If the game is already in the database, still attempt to add the tags specified by the user.
                            gid = current_game.id
                            add_tags(data, gid, "game")
                            flash(f'This item is already in the database. Your tags can still be addded.', 'warning')

        else:
            flash(f'No games found. Check the title and year and try again!', 'danger')
    else:
        flash('Failed to retrieve data', 'danger')
