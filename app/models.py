from sqlalchemy import PrimaryKeyConstraint, ForeignKeyConstraint

from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
    username = db.Column(db.String(20), nullable=False, unique=True, index=True)
    email = db.Column(db.String(64), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, salt_length=32)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return str(self.user_id)

    def __repr__(self):
        return f"user(id='{self.user_id}', '{self.username}', '{self.email}')"

@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))


class Books(db.Model):
    __tablename__ = "books"
    id = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
    title = db.Column(db.String(50), nullable=False, unique=True, index=True)
    author = db.Column(db.String(30), nullable=False, index=True)
    year = db.Column(db.String(4), nullable=False, index=True)
    publisher = db.Column(db.String(30), nullable=True)
    isbn = db.Column(db.String(30), nullable=False)
    cover = db.Column(db.String(100), nullable=True)

class Films(db.Model):
    __tablename__ = "films"
    id = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
    title = db.Column(db.String(50), nullable=False, unique=True, index=True)
    director = db.Column(db.String(30), nullable=False, index=True)
    year = db.Column(db.String(4), nullable=False, index=True)
    production_company = db.Column(db.String(30), nullable=True)
    cover = db.Column(db.String(100), nullable=True)

class Games(db.Model):
    __tablename__ = "games"
    id = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
    title = db.Column(db.String(50), nullable=False, unique=True, index=True)
    developer = db.Column(db.String(30), nullable=False, index=True)
    year = db.Column(db.String(4), nullable=False, index=True)
    cover = db.Column(db.String(100), nullable=True)

class Tags(db.Model):
    __tablename__ = "tags"
    tag_id = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
    tag = db.Column(db.String(50), unique=True, nullable=False)

class ItemTags(db.Model):
    __tablename__ = "item_tags"
    item_id = db.Column(db.Integer, nullable=False)
    item_type = db.Column(db.Enum('book', 'film', 'game'), nullable=False)
    tag_id = db.Column(db.Integer, db.ForeignKey('tags.tag_id'), nullable=False)
    count = db.Column(db.Integer, nullable=False, default=1)

    PrimaryKeyConstraint(item_id, item_type, tag_id, name="item_tags_key")

class UserUpvotes(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    item_id = db.Column(db.Integer, nullable=False)
    item_type = db.Column(db.Enum('book', 'film', 'game'), nullable=False)
    tag_id = db.Column(db.Integer, db.ForeignKey('tags.tag_id'), nullable=False)
    timestamp = db.Column(db.Integer, nullable=False)

    PrimaryKeyConstraint(user_id, tag_id, item_type, item_id, name="upvotes_key")
    ForeignKeyConstraint(['item_id', 'item_type', 'tag_id'],
            ['item_tags.item_id', 'item_tags.item_type', 'item_tags.tag_id'],
            name="upvotes_fk"
        )
