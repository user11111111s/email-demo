from app import create_app, db
from app.models import User

app = create_app()
with app.app_context():
    if User.query.count() == 0:
        admin = User(username='admin')
        admin.set_password('admin')
        db.session.add(admin)
        db.session.commit()
        print("Default user admin/admin created.")
    else:
        print("User table not empty.")
