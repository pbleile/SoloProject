from flask import session,redirect,render_template,request,flash,send_from_directory,jsonify,json
from config import EMAIL_REGEX,bcrypt
from models import User,Album,Picture,album_has_pictures,Album_to_Pic
import os,sys
import os.path
from os import path
from werkzeug.utils import secure_filename
import exifread
import json
from PIL import Image
from datetime import datetime

def show_welcome_page():
    return render_template("welcome.html")

def logout_user():
    session.clear()
    return redirect('/')

def show_register_and_login():
    print("in show_form")
    return render_template('register.html')

def register_user():
    errors=User.validate_new(request.form)
    for error in errors:
        flash(error[0],error[1])
    if len(errors)==0:
        user_id=User.register_new(request.form)
        if user_id>0:
            session['MyWebsite_user_id']=user_id
            session['user_name']=request.form['first_name']+" "+request.form['last_name']
            session['login_session']=User.get_session_key(user_id)
            session['email_address']=request.form['email_address']
            # Note: email sanitization checked in User.validate_new(request.form)
            os.mkdir('UserFiles/'+request.form['email_address'])
            os.mkdir('UserFiles/thumbnails/'+request.form['email_address'])
            album=Album.new(user_id,'Default')
            user=User.get_one(user_id)
            user.set_active_album(album.id)
            return redirect('/user')
    return redirect('/signin')

def login_user():
    user_info=User.validate_login(request.form)
    if user_info:
        session['MyWebsite_user_id']=user_info.id
        session['user_name']=user_info.first_name+" "+user_info.last_name
        session['login_session']=bcrypt.generate_password_hash(str(user_info.created_at))
        session['email_address']=request.form['email_address']
        if user_info.user_level==9:
            return redirect('/admin')
        else:
            return redirect('/user')
    flash("Login failed: email or password is incorrect",'login')
    return redirect('/signin')

def show_login_success():
    if not 'MyWebsite_user_id' in session.keys():
        return redirect('/')
    if User.is_logged_in(session['MyWebsite_user_id'],session['login_session']):
        print("user login_success")
        return render_template('welcome.html')

def show_user_page():
    if not 'MyWebsite_user_id' in session.keys():
        return redirect('/')
    if User.is_logged_in(session['MyWebsite_user_id'],session['login_session']):
        print("user login_success")
        return render_template('welcome.html')

def show_user_dashboard():
    # render the main dashboard page
    if not 'MyWebsite_user_id' in session.keys():
        return redirect('/')
    if not User.is_logged_in(session['MyWebsite_user_id'],session['login_session']):
        return redirect('/danger')    
    print("user login_success")
    user=User.get_one(session['MyWebsite_user_id'])
    if user.profile_picture==0:
        profile_pic="/static/funny_smile_emoticons_vector_icon_522939.jpg"
    else:
        profile_pic='/UserFiles/'+ Picture.query.get(user.profile_picture).file_path
    print(profile_pic)
    return render_template('dashboard.html',albums=user.albums,profile_pic=profile_pic)

def show_admin_page():
    if not 'MyWebsite_user_id' in session.keys():
        return redirect('/')
    if User.is_logged_in_as_admin(session['MyWebsite_user_id'],session['login_session']):
        print("admin login_success")
        users=User.get_all()
        return render_template('admin.html',users=users)
    return redirect('/danger')

def remove_user(user_id):
    if not 'MyWebsite_user_id' in session.keys():
        return redirect('/')
    if not User.is_logged_in_as_admin(session['MyWebsite_user_id'],session['login_session']):
        return redirect('/danger')
    print('remove user')
    User.remove(user_id)
    return redirect('/admin')

def make_admin(user_id):
    if not 'MyWebsite_user_id' in session.keys():
        return redirect('/')
    if not User.is_logged_in_as_admin(session['MyWebsite_user_id'],session['login_session']):
        return redirect('/danger')
    print('make admin')
    User.make_admin_level(user_id)
    return redirect('/admin')

def make_user(user_id):
    if not 'MyWebsite_user_id' in session.keys():
        return redirect('/')
    if not User.is_logged_in_as_admin(session['MyWebsite_user_id'],session['login_session']):
        return redirect('/danger')
    print('remove admin')
    User.make_user_level(user_id)
    return redirect('/admin')

def show_danger():
    return render_template('danger.html',hacker_ip=request.remote_addr)

# **************** Photobomb specific ************************* #

def upload():
    # upload one or more pictures to the filesystem and register it/them in the database
    if not 'MyWebsite_user_id' in session.keys():
        return redirect('/')
    if not User.is_logged_in(session['MyWebsite_user_id'],session['login_session']):
        return redirect('/danger')    
    user=User.get_one(session['MyWebsite_user_id'])
    album_id=request.form['active_album']
    # f=request.files['new_pic']
    files=request.files.getlist('new_pic')
    for eachfile in files:
        filename=secure_filename(eachfile.filename)
        ALLOWED_EXTENSIONS = ('bmp','png', 'jpg', 'jpeg', 'gif')
        if '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS:
            print(filename)
            if path.exists('UserFiles/'+user.email+'/'+filename):
                # Album.add_pic(user,pic,album_id)
                filename=filename.rsplit('.',1)
                filename[0]=filename[0]+str(round(datetime.timestamp(datetime.now())))
                filename='.'.join(filename)

            # Save pic to the filesystem
            eachfile.save('UserFiles/'+user.email+'/'+filename)
            # Add pic to the pictures db
            pic=Picture.new(user.id,user.email+'/'+filename,filename)
            # Add pic to the active album
            Album.add_pic(user,pic,album_id)
            # Create thumbnail image using PIL
            im=Image.open('UserFiles/'+user.email+'/'+filename)
            im.thumbnail((100,100),Image.ANTIALIAS)
            im.save('UserFiles/thumbnails/'+user.email+'/'+filename)
            user.set_active_album(album_id)
        else:
            print('invalid file extension.')
    return redirect('/dashboard')

def get_pics(filepath):
    # responds to url requests by sending the file to the requestor
    if not 'MyWebsite_user_id' in session.keys():
        return redirect('/')
    if not User.is_logged_in(session['MyWebsite_user_id'],session['login_session']):
        return redirect('/danger')
    user=User.get_one(session['MyWebsite_user_id'])
    # SECURITY CHECK:  VERIFY THAT FILEPATH REQUEST BELONGS TO REQUESTING USER
    if (os.path.dirname(filepath)!=user.email) and (os.path.dirname(filepath)!='thumbnails/'+user.email):
         print('Filepath DANGER:',filepath)
         return redirect('/danger')
    return send_from_directory('UserFiles', filepath)

def view_pic(picture_id,album_id):
    # render page that displays the picture in large format with details
    if not 'MyWebsite_user_id' in session.keys():
        return redirect('/')
    if not User.is_logged_in(session['MyWebsite_user_id'],session['login_session']):
        return redirect('/danger')
    # SECURITY CHECK:  VERIFY THAT PICTURE BELONGS TO REQUESTING USER
    pic=Picture.query.get(picture_id)
    if pic.user.id!=session['MyWebsite_user_id']:
        return redirect('/danger')
    # Open image file for reading (binary mode)
    f = open('UserFiles/'+pic.file_path, 'rb')
    # Return Exif tags
    tags = exifread.process_file(f)
    # print(tags)
    # find prev and next pics in the album
    album=Album.query.get(album_id)
    return render_template('view.html',album=album, picture_id=picture_id,picture=pic,exif_data=tags)

def delete_pic(picture_id):
    #delete the picture from the database, and file system
    if not 'MyWebsite_user_id' in session.keys():
        return redirect('/')
    if not User.is_logged_in(session['MyWebsite_user_id'],session['login_session']):
        return redirect('/danger')    
    pic=Picture.query.get(picture_id)
    # SECURITY CHECK:  VERIFY THAT PICTURE BELONGS TO REQUESTING USER
    if pic.user.id!=session['MyWebsite_user_id']:
        return redirect('/danger')
    print("deleting: ",pic)
    if os.path.exists('UserFiles/'+pic.file_path):
        os.remove('UserFiles/'+pic.file_path)
        if os.path.exists('UserFiles/thumbnails'+pic.file_path):
            os.remove('UserFiles/thumbnails/'+pic.file_path)
        Picture.delete(picture_id)
        print("delete success: ", pic)
    else:
        print("delete fail: ",pic)
    return redirect ('/dashboard')

def create_album():
    if not 'MyWebsite_user_id' in session.keys():
        return redirect('/')
    if not User.is_logged_in(session['MyWebsite_user_id'],session['login_session']):
        return redirect('/danger')    
    # print(request.form)
    new_album=Album.new(session['MyWebsite_user_id'],request.form['name'],request.form['description'])
    if new_album==None:
        # handle error
        pass
    return redirect ('/dashboard')

def delete_album():
    if not 'MyWebsite_user_id' in session.keys():
        return redirect('/')
    if not User.is_logged_in(session['MyWebsite_user_id'],session['login_session']):
        return redirect('/danger')
    print ("Delete Album: ",request.form['json'])
    deleting_album=json.loads(request.form['json'])
    album_id=deleting_album['album_id']
    Album.delete(album_id)
    return redirect ('/dashboard')

def update_profile():
    if not 'MyWebsite_user_id' in session.keys():
        return redirect('/')
    if not User.is_logged_in(session['MyWebsite_user_id'],session['login_session']):
        return redirect('/danger')    
    # need email validations
    user=User.get_one(session['MyWebsite_user_id'])
    if user.email!=request.form['email_address']:
        user.update_email(request.form['email_address'])
    f=request.files['profile_pic']
    filename=secure_filename(f.filename)
    ALLOWED_EXTENSIONS = ('bmp','png', 'jpg', 'jpeg', 'gif')
    if '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS:
        # Save pic to the filesystem
        f.save('UserFiles/'+user.email+'/'+filename)
        # Add pic to the pictures db
        pic=Picture.new(user.id,user.email+'/'+filename,filename)
        # set user's picture to what they just uploaded.
        user.update_profile_pic(pic.id)
    return redirect ('/dashboard')

def reorder_album():
    if not 'MyWebsite_user_id' in session.keys():
        return redirect('/')
    if not User.is_logged_in(session['MyWebsite_user_id'],session['login_session']):
        return redirect('/danger')    
    python_obj = json.loads(request.form['json'])
    album_order=Album_to_Pic()
    # This section to be replaced by album_order.set_order(python_obj)
    old_order=album_order.get_order(python_obj["album_id"])
    album=Album.query.get(python_obj["album_id"])
    # Remove pictures from album if they are no longer in the list
    for picture_id in old_order:
        if picture_id not in python_obj["ordering"]:
            picture=Picture.query.get(picture_id)
            album.pictures.remove(picture)
            album_order.commit()
    # Rewrite all the rank values in the db table using the index value of the list
    for rank,picture_id in enumerate(python_obj["ordering"],1):
        # print(rank, picture_id)
        if picture_id.isnumeric():
            # if the list contains a picture that is not in the album, then add it
            picture=Picture.query.get(picture_id)
            if picture not in album.pictures:
                Album.add_pic(user=None,picture=picture,album_id=album.id)
            record=album_order.get_one(python_obj["album_id"],picture_id)
            record.rank=rank
    album_order.commit()
    # print(album_order.get_order(python_obj["album_id"]))
    return redirect('/dashboard')

def reorder_albums():
    if not 'MyWebsite_user_id' in session.keys():
        return redirect('/')
    if not User.is_logged_in(session['MyWebsite_user_id'],session['login_session']):
        return redirect('/danger')
    album_order=json.loads(request.form['json'])
    # print('Album order',album_order['ordering'])
    for rank,album_id in enumerate(album_order['ordering'],1):
        # print(album_id,rank)
        Album.set_rank(album_id,rank)
    return redirect('/dashboard')

def update_photo_info():
    if not 'MyWebsite_user_id' in session.keys():
        return redirect('/')
    if not User.is_logged_in(session['MyWebsite_user_id'],session['login_session']):
        return redirect('/danger')    
    photo_info=json.loads(request.form['json'])
    # print("Photo Info",photo_info)
    Picture.update_info(photo_info)
    return "Thank You"

def update_album_info():
    if not 'MyWebsite_user_id' in session.keys():
        return redirect('/')
    if not User.is_logged_in(session['MyWebsite_user_id'],session['login_session']):
        return redirect('/danger')    
    album_info=json.loads(request.form['json'])
    # print("Album Info",album_info)
    Album.update_info(album_info)
    return "Thank You"

def set_active_album():
    if not 'MyWebsite_user_id' in session.keys():
        return redirect('/')
    if not User.is_logged_in(session['MyWebsite_user_id'],session['login_session']):
        return redirect('/danger')    
    active_album=json.loads(request.form['json'])
    # print("Active Album", active_album)
    session['active_album']=active_album['album_id']
    user=User.get_one(session['MyWebsite_user_id'])
    user.set_active_album(active_album['album_id'])
    return "Thank You"

def picture_search():
    if not 'MyWebsite_user_id' in session.keys():
        return redirect('/')
    if not User.is_logged_in(session['MyWebsite_user_id'],session['login_session']):
        return redirect('/danger')    
    # print(request.form['search_str'])
    search_result_album=Album.search(session['MyWebsite_user_id'],request.form['search_str'])
    # print("search results:",search_result_album)
    return render_template("search_results.html",album=search_result_album)