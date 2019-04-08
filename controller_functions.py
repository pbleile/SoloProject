from flask import session,redirect,render_template,request,flash,send_from_directory
from config import EMAIL_REGEX,bcrypt
from models import User,Album,Picture,album_has_pictures
import os,sys
from werkzeug.utils import secure_filename

def logout_user():
    session.clear()
    return redirect('/')

def show_register_and_login():
    print("in show_form")
    return render_template('register.html')

#app.add_url_rule('/register',view_func=register_user,methods=["POST"])
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
            os.mkdir('UserFiles/'+request.form['email_address'])
            Album.new(user_id,'Default')
            return redirect('/success')
    return redirect('/')

def login_user():
    user_info=User.validate_login(request.form)
    if user_info:
        session['MyWebsite_user_id']=user_info.id
        session['user_name']=user_info.first_name+" "+user_info.last_name
        session['login_session']=bcrypt.generate_password_hash(str(user_info.created_at))
        if user_info.user_level==9:
            return redirect('/admin')
        else:
            return redirect('/user')
    flash("Login failed: email or password is incorrect",'login')
    return redirect('/')

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
    if not 'MyWebsite_user_id' in session.keys():
        return redirect('/')
    if User.is_logged_in(session['MyWebsite_user_id'],session['login_session']):
        print("user login_success")
        user=User.get_one(session['MyWebsite_user_id'])
        return render_template('dashboard.html',albums=user.albums)

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

def upload():
    user=User.get_one(session['MyWebsite_user_id'])
    f=request.files['new_pic']
    filename=secure_filename(f.filename)
    ALLOWED_EXTENSIONS = ('bmp','png', 'jpg', 'jpeg', 'gif')
    if '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS:
        print(filename)
        # Save pic to the filesystem
        f.save('UserFiles/'+user.email+'/'+filename)
        # Add pic to the pictures db
        pic=Picture.new(user.id,user.email+'/'+filename,filename)
        # Add pic to the active album
        Album.add_pic(user,pic)
    else:
        print('invalid file extension.')
    return redirect('/dashboard')

def get_pics(filepath):
    print(filepath)
    return send_from_directory('UserFiles', filepath)