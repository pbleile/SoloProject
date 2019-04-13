from config import app
import routes
from models import User

if __name__=="__main__":
    app.run(debug=True)

# To Do
# Required
# 1. Test Handling duplicate file names
# 2. Enable security
# 3. Fatten Models and Slim contollers
# 4. Modularize
# 5. Replace literals with constants
# Optional (features)
# 1. Album ordering on page
# 2. Drag zoomed in pic around inside div
# 3. Copy Move pictures between albums without re-upload