from config import app
import routes
from models import User

if __name__=="__main__":
    app.run(debug=True)

# To Do
# 1. Album renaming
# 2. Picture ordering in album
# 3. Set default album (and move to top)
# 4. Set View Picture to window size
# 5.    Display Picture info
# 6.    Picture renaming
# 7. Search-> match one picture, and switch to View
# 8. Move through pictures in View
# 9. Handle duplicate file names
# 10.Enable security
# 11.Replace literals with constants