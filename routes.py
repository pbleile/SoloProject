from config import app
from controller_functions import *

app.add_url_rule('/',view_func=show_register_and_login)
app.add_url_rule('/register',view_func=register_user,methods=["POST"])
app.add_url_rule('/login',view_func=login_user,methods=['POST'])
app.add_url_rule('/logout',view_func=logout_user)

app.add_url_rule('/success',view_func=show_login_success)
# app.add_url_rule('/user',view_func=show_user_page)
app.add_url_rule('/user',view_func=show_user_dashboard)
app.add_url_rule('/dashboard',view_func=show_user_dashboard)
app.add_url_rule('/admin',view_func=show_admin_page)

app.add_url_rule('/remove/<user_id>',view_func=remove_user)
app.add_url_rule('/make_admin/<user_id>',view_func=make_admin)
app.add_url_rule('/make_user/<user_id>',view_func=make_user)
app.add_url_rule('/danger',view_func=show_danger)


app.add_url_rule('/upload',view_func=upload,methods=["POST"])
app.add_url_rule('/UserFiles/<path:filepath>',view_func=get_pics)
app.add_url_rule('/photos/<picture_id>',view_func=view_pic)
app.add_url_rule('/delete/<picture_id>',view_func=delete_pic)
app.add_url_rule('/create_album',view_func=create_album,methods=["POST"])
app.add_url_rule('/update_profile',view_func=update_profile,methods=["POST"])
app.add_url_rule('/reorder_album',view_func=reorder_album,methods=["POST"])