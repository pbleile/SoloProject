from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask import flash
from config import bcrypt, EMAIL_REGEX,db
from sqlalchemy.sql import func, and_,or_
from sqlalchemy.ext.automap import automap_base

def rankDefault(context):
    return context.get_current_parameters()['picture_id']

album_has_pictures=db.Table('album_has_pictures',
    db.Column('picture_id',db.Integer,db.ForeignKey('pictures.id',ondelete="cascade"),primary_key=True),
    db.Column('album_id'  ,db.Integer,db.ForeignKey('albums.id'  ,ondelete="cascade"),primary_key=True),
    db.Column('created_at',db.DateTime, server_default=func.now()),
    db.Column('updated_at',db.DateTime, server_default=func.now(), onupdate=func.now()),
    db.Column('rank',db.Integer, default=rankDefault)
    )
# To directly query album_has_pictures like this (returns a list of tuples [(1,),(2,)...(10,)]):
# q=db.session.query(album_has_pictures.columns.rank).filter(album_has_pictures.columns.album_id==2).all()

class Album_to_Pic:
    # This class is a workaround to access the extra data in the album_has_pictures many to many Table.
    # This was not the best solution to this.  See the section on Association Object:
    # https://docs.sqlalchemy.org/en/latest/orm/basic_relationships.html#relationships-many-to-many
    Base = automap_base()
    engine=db.session.get_bind()
    Base.prepare(engine, reflect=True)
    table=Base.classes.album_has_pictures
    def __init__(self):
        pass
    def get_all(self):
        return db.session.query(self.table).all()
    def get_by_album(self,album_id):
        # Return a list of pictures (Picture) belonging to an album, ordered by rank (int).
        return db.session.query(Picture).join(self.table,self.table.picture_id==Picture.id).filter(self.table.album_id==album_id).order_by(self.table.rank).all()
    def get_one(self,album_id,picture_id):
        # Return one record using the composite primary key (user_id + album_id).
        return db.session.query(self.table).filter(self.table.album_id==album_id).filter(self.table.picture_id==picture_id).first()
    def commit(self):
        db.session.commit()
    def get_order(self, album_id):
        # Returns the picture order of an album as a list of picture_id (int).
        table=db.session.query(self.table).filter(self.table.album_id==album_id).order_by(self.table.rank).all()
        picture_id_order=[]
        for record in table:
            picture_id_order.append(record.picture_id)
        return picture_id_order
    def set_order(self, ordering_dict):
        # Ordering_list is a dict containing a list of picture_id in the desired order.
        # eg. {'album_id': '2', 'ordering': ['6', '2', '1', '3', '5', '4', '7', '8', '9', '10']}
        for index,picture_id in enumerate(ordering_dict["ordering"],1):
            # print(index, picture_id)
            record=album_order.get_one(ordering_dict["album_id"],picture_id)
            record.rank=index
            db.session.commit()

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
        """
        Add a new file to the Picture table.
        new(user_id,file_path,name)
        """
        new_pic=Picture(user_id=user_id,name=name,description="",file_path=file_path)
        db.session.add(new_pic)
        db.session.commit()
        return new_pic
    @classmethod
    def delete(cls,picture_id):
        pic=Picture.query.get(picture_id)
        db.session.delete(pic)
        db.session.commit()
    @classmethod
    def update_info(cls,picture_info):
        pic=Picture.query.get(picture_info['picture_id'])
        if "picture_description" in picture_info.keys():
            pic.description=picture_info['picture_description']
        if "picture_name" in picture_info.keys():
            pic.name=picture_info['picture_name']
        db.session.commit()

class Album(db.Model):
    __tablename__="albums"
    id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey('users.id'),nullable=False)
    name=db.Column(db.String(255))
    description=db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())
    pictures=db.relationship('Picture',secondary=album_has_pictures,order_by='album_has_pictures.columns.rank')
    user=db.relationship('User',foreign_keys=[user_id],backref=db.backref("albums",cascade="all,delete-orphan"))
    @classmethod
    def new(cls,user_id,name,description=""):
        # Create a new album (Album) record.
        new_album=Album(user_id=user_id,name=name,description=description)
        if name=="search_results":
            return "Error: cannot use this name"
        if len(name)>1:
            db.session.add(new_album)
            db.session.commit()
            return None
        else:
            return new_album
    @classmethod
    def get_for_user(cls,user_id):
        # Return a list of albums (as Album objs) for Int user_id.
        user=User.query.get(user_id)
        albums=Album.query.filter(user)
        return albums
    @classmethod
    def get_active(cls,user):
        # Return the active album for user (User).
        active_album=cls.query.filter(cls.user_id==user.id,cls.id==user.active_album).first()
        return active_album
    @classmethod
    def add_pic(cls,user,picture,album_id):
        # Add a picture (Picture) to the active album (by user (User)) or to the album of album_id (int).
        if not album_id:
            album=Album.get_active(user)
        else:
            album=Album.query.get(album_id)
        album.pictures.append(picture)
        db.session.commit()
    @classmethod
    def update_info(cls,album_info):
        # Update the name /and or description of an album.
        # Album_info in the form of {'album_id':'1','album_name':'asdf',album_description':'asf'}.
        album=Album.query.get(album_info['album_id'])
        if album.name=="search_results":
            return
        if "album_description" in album_info.keys():
            album.description=album_info['album_description']
        if "album_name" in album_info.keys():
            album.name=album_info['album_name']
        db.session.commit()
    @classmethod
    def search(cls,user_id,search_str):
        # Use a speacial album named "search_results" to store pictures with name or query matching search_str.
        # If no album named search_results exists, it is created.  If it does exist, it's contents are replaced.
        album=cls.query.filter(cls.user_id==user_id).filter(cls.name=="search_results").first()
        if not album:
            album=cls(user_id=user_id,name="search_results",description="Search results for: "+search_str)
            db.session.add(album)
            db.session.commit()
        else:
            for picture in album.pictures:
                # Remove picture from search_results album, but not from db.
                album.pictures.remove(picture)
                db.session.commit()
        found_pictures=Picture.query.filter(or_(Picture.name.like("%"+search_str+"%"),Picture.description.like("%"+search_str+"%"))).all()
        for picture in found_pictures:
            album.pictures.append(picture)
        db.session.commit()
        return album


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
    profile_picture=db.Column(db.Integer,default=0)
    def set_active_album(self,album_id):
        # Store the user's active album_id (int).
        self.active_album=album_id
        db.session.commit()
        return self
    def update_email(self,new_email):
        # Update email.
        self.email=new_email
        db.session.commit()
        return self
    def update_profile_pic(self,pic_id):
        # Store a picture_id (int) to use as profile picture.
        self.profile_picture=pic_id
        db.session.commit()
        return self
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

