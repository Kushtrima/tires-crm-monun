from app import create_app, db
from app.models import User, Product, Order, OrderItem, Service
from flask_migrate import Migrate
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = create_app()
migrate = Migrate(app, db)

def init_db():
    with app.app_context():
        try:
            # Create tables directly without migrations
            db.create_all()
            logger.info("Database tables created successfully")
            
            # Only create admin user if it doesn't exist
            if not User.query.filter_by(username='admin').first():
                admin = User(
                    username='admin',
                    full_name='Administrator',
                    position='admin'
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                logger.info("Admin user created successfully")
                
                # Create sample data only for fresh database
                from app.sample_data import create_sample_data
                create_sample_data()
                logger.info("Sample data created successfully")
        except Exception as e:
            logger.error(f"Error during database initialization: {e}")
            raise

if __name__ == '__main__':
    try:
        init_db()
        # Use threaded=False to avoid socket connection issues
        app.run(
            debug=True,
            host='127.0.0.1',  # Use localhost instead of 0.0.0.0
            port=5001,
            threaded=False,
            use_reloader=True
        )
    except Exception as e:
        logger.error(f"Application error: {e}") 