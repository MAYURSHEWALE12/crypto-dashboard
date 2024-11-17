from app import db, User
from werkzeug.security import generate_password_hash

# Create a new admin user
admin = User(username='admin', email='admin@gmail.com', 
             password=generate_password_hash('admin'))

# Set the admin flag
admin.is_admin = True

# Add and commit to the database
db.session.add(admin)
db.session.commit()

print("Admin user added successfully.")
