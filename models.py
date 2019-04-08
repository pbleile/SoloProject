from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask import flash
from config import bcrypt, EMAIL_REGEX,db
from sqlalchemy.sql import func, and_,or_

album_has_pictures=db.Table('album_has_pictures',
    db.Column('picture_id',db.Integer,db.ForeignKey('pictures.id',ondelete="cascade"),primary_key=True),
    db.Column('album_id'  ,db.Integer,db.ForeignKey('albums.id'  ,ondelete="cascade"),primary_key=True),
    db.Column('created_at',db.DateTime, server_default=func.now()),
    db.Column('updated_at',db.DateTime, server_default=func.now(), onupdate=func.now())
    )

class Picture(db.Model):
    __tablename__="pictures"
    id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey('users.id'),nullable=False)
    name=db.Column(db.String(255))
    description=db.Column(db.Text)
    file_path=db.Column(db.String(255))
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())
    in_albums=db.relationship('Album',secondary=album_has_pictures)
    user=db.relationship('User', foreign_keys=[user_id],  backref=db.backref("pictures",cascade="all,delete-orphan"))
    @classmethod
    def new(cls,user_id,file_path,name):
        new_pic=Picture(user_id=user_id,name=name,description="",file_path=file_path)
        db.session.add(new_pic)
        db.session.commit()
        return new_pic

class Album(db.Model):
    __tablename__="albums"
    id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey('users.id'),nullable=False)
    name=db.Column(db.String(255))
    description=db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())
    pictures=db.relationship('Picture',secondary=album_has_pictures)
    user=db.relationship('User',foreign_keys=[user_id],backref=db.backref("albums",cascade="all,delete-orphan"))
    @classmethod
    def new(cls,user_id,name):
        new_album=Album(user_id=user_id,name=name)
        db.session.add(new_album)
        db.session.commit()
    @classmethod
    def get_for_user(cls,user_id):
        user=User.query.get(user_id)
        albums=Album.query.filter(user)
        return albums
    @classmethod
    def get_active(cls,user):
        active_album=cls.query.filter(cls.user_id==user.id,cls.id==user.active_album).first()
        return active_album
    @classmethod
    def add_pic(cls,user,picture):
        album=Album.get_active(user)
        album.pictures.append(picture)
        db.session.commit()

class User(db.Model):
    __tablename__="users"
    id=db.Column(db.Integer,primary_key=True)
    first_name=db.Column(db.String(255))
    last_name=db.Column(db.String(255))
    email=db.Column(db.String(255))
    password=db.Column(db.String(255))
    user_level=db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())
    active_album = db.Column(db.Integer)

    @classmethod
    def get_existing(cls,first_name,last_name):
        user=cls.query.filter_by(first_name=first_name, last_name=last_name).all()
        return user

    @classmethod
    def get_session_key(cls,user_id):
        user=cls.query.get(user_id)
        session_key=bcrypt.generate_password_hash(str(user.created_at))
        return session_key

    @classmethod
    def validate_new(cls,form):
        errors=[]
        if len(form['first_name'])==0 or len(form['last_name'])==0:
            errors.append(("Please enter your first and last names.",'registration'))
        if not (form['first_name'].isalpha() and form['last_name'].isalpha()):
            errors.append(("Names must be alphabet characters only!",'registration'))
        existing_users=User.query.filter_by(first_name=form['first_name'],last_name=form['last_name']).count()
        if (existing_users)>0:
            errors.append(("This user's first and last name is already registered!",'registration'))
        if len(form['password'])<5:
            errors.append(("Password must be at least 5 characters long!",'registration'))
        if form['password']!=form['confirm_password']:
            errors.append(("Passwords don't match!",'registration'))
        if not EMAIL_REGEX.match(form['email_address']):    # test whether a field matches the pattern
            errors.append(("Invalid email address!",'registration'))
        existing_users=User.query.filter_by(email=form['email_address']).count()
        if (existing_users)>0:
            errors.append(("This email address is currently in use by another user!",'registration'))
        return errors

    @classmethod
    def register_new(cls,form):
        hashed_pwd=bcrypt.generate_password_hash(form['password'])
        new_user=cls(first_name=form['first_name'],last_name=form['last_name'],email=form['email_address'],password=hashed_pwd)
        db.session.add(new_user)
        db.session.commit()
        return new_user.id

    @classmethod
    def validate_login(cls,form):
        user=cls.query.filter_by(email=form['email_address']).first()
        print(user)
        if user:
            if bcrypt.check_password_hash(user.password,form['password']):
                return user
        return None

    @classmethod
    def is_logged_in(cls,user_id,login_session):
        user=cls.query.get(user_id)
        result=False
        if user:
            if bcrypt.check_password_hash(login_session,str(user.created_at)):
                result=True
        return result

    @classmethod
    def is_logged_in_as_admin(cls,admin_id,login_session):
        user=cls.query.get(admin_id)
        result=False
        if user:
            if bcrypt.check_password_hash(login_session,str(user.created_at)):
                if user.user_level==9:
                    print("admin login_success")
                    result=True
        return result

    @classmethod
    def get_one(cls,user_id):
        user=cls.query.get(user_id)
        return user

    @classmethod
    def remove(cls,user_id):
        user=cls.query.get(user_id)
        db.session.delete(user)
        db.session.commit()

    @classmethod
    def make_admin_level(cls,user_id):
        user=cls.query.get(user_id)
        user.user_level=9
        db.session.update(user)
        db.session.commit()

    @classmethod
    def make_user_level(cls,user_id):
        user=cls.query.get(user_id)
        user.user_level=0
        db.session.update(user)
        db.session.commit()

    @classmethod
    def get_all(cls):
        users=cls.query.all()
        return users

