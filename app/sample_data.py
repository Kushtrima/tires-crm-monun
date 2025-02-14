from app import db
from app.models import Product, Order, Service
from datetime import datetime, timedelta
import random

def create_sample_data():
    # Create sample tire products
    products = [
        Product(
            name='Michelin Pilot Sport 4',
            brand='Michelin',
            size='225/45R17',
            type='Summer',
            description='High-performance summer tire with excellent grip',
            price=299.90,
            stock=12
        ),
        Product(
            name='Continental WinterContact',
            brand='Continental',
            size='205/55R16',
            type='Winter',
            description='Premium winter tire for Swiss conditions',
            price=259.90,
            stock=20
        ),
        Product(
            name='Pirelli Cinturato All Season',
            brand='Pirelli',
            size='215/55R17',
            type='All-Season',
            description='Versatile all-season tire',
            price=189.90,
            stock=15
        ),
        Product(
            name='Goodyear UltraGrip 9',
            brand='Goodyear',
            size='195/65R15',
            type='Winter',
            description='Reliable winter tire for compact cars',
            price=169.90,
            stock=25
        ),
    ]
    
    db.session.add_all(products)
    db.session.commit()

    # Create sample services
    services = [
        Service(
            name='Tire Installation',
            description='Complete tire installation including balancing',
            price=79.90,
            duration=45,
            category='Installation'
        ),
        Service(
            name='Tire Rotation',
            description='Rotate tires to ensure even wear',
            price=49.90,
            duration=30,
            category='Maintenance'
        ),
        Service(
            name='Wheel Balancing',
            description='Professional wheel balancing service',
            price=39.90,
            duration=30,
            category='Maintenance'
        ),
        Service(
            name='Flat Tire Repair',
            description='Repair of punctures and minor damage',
            price=59.90,
            duration=60,
            category='Repair'
        ),
        Service(
            name='Wheel Alignment',
            description='Complete wheel alignment service',
            price=129.90,
            duration=90,
            category='Maintenance'
        ),
        Service(
            name='Seasonal Tire Storage',
            description='Safe storage of your off-season tires',
            price=149.90,
            duration=30,
            category='Storage',
            is_active=True
        ),
    ]
    
    db.session.add_all(services)
    db.session.commit()

    # Create sample orders
    statuses = ['pending', 'completed', 'cancelled']
    customers = ['Hans Müller', 'Sarah Weber', 'Michael Schmidt', 'Anna Fischer']
    
    for i in range(20):
        days_ago = random.randint(0, 60)
        order = Order(
            customer_name=random.choice(customers),
            total_amount=random.uniform(200, 1200),
            status=random.choice(statuses),
            created_at=datetime.utcnow() - timedelta(days=days_ago)
        )
        db.session.add(order)
    
    db.session.commit() 