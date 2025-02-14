from flask import Flask
from app import create_app, db
from app.models import User
from flask.cli import with_appcontext
import click

app = create_app()

@click.command('create_db')
@with_appcontext
def create_db_command():
    """Create the database tables."""
    db.drop_all()
    db.create_all()
    
    # Create admin user
    admin = User(
        username="admin",
        full_name="Administrator",
        position="admin"
    )
    admin.set_password("admin123")
    db.session.add(admin)
    db.session.commit()
    print("Database initialized!")

# Add the command to the CLI
app.cli.add_command(create_db_command)

if __name__ == '__main__':
    app.run() 