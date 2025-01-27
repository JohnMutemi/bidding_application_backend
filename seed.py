from app import app
from models import db, User, Product, Bid
from datetime import datetime

def seed_data():
    with app.app_context():
        # Drop existing tables and create new ones
        db.drop_all()
        db.create_all()

        # Clear session
        db.session.remove()

        # Sample users with passwords and roles (writer, admin, client)
        users = [
            {'username': 'johndoe', 'email': 'johndoe@example.com', 'password': 'password123', 'role': 'customer'},
            {'username': 'scholar', 'email': 'scholar@example.com', 'password': 'scholarpass', 'role': 'admin'}
        ]

        # Add users to the session
        for user_data in users:
            user = User(username=user_data['username'], email=user_data['email'], role=user_data['role'])
            user.set_password(user_data['password'])  
            db.session.add(user)

        db.session.commit()

        # Sample products
        products = [
            Product(
                name='Gear Box', description=' Sparkling new', price_tag=2000.00, 
                quantity=12, bidding_end_time=datetime(2024, 8, 1), user_id=1, 
                status='available'
            ),
            Product(
                name='Steering Wheel', description='Achieve comfy with the imported steering wheels', price_tag=3500.00, 
                quantity=100, bidding_end_time=datetime(2024, 8, 10), user_id=1, 
                status='available'
            ),
            Product(
                name='Tyres', description='Lets go spanning with the new japan tyres', price_tag=4500.00,
                quantity=70, bidding_end_time=datetime(2024, 8, 5), user_id=1, 
                status='available'
            ),
        ]

  
        # Add products to the session
        db.session.bulk_save_objects(products)
        db.session.commit()

        # Sample bids 
        bids = [
            Bid(user_id=2, product_id=1, amount=2300.00, status='accepted', bidding_time=datetime(2025, 8,5), highest_bid=3000), 
            Bid(user_id=2, product_id=2, amount=3700.00, status='pending', bidding_time=datetime(2025, 9,5), highest_bid=4500),   
            Bid(user_id=2, product_id=3, amount=4900.00, status='rejected', bidding_time=datetime(2025, 8,5), highest_bid=5000),  
        ]

        

        # Add bids to the session
        db.session.bulk_save_objects(bids)
        db.session.commit()

if __name__ == '__main__':
    seed_data()
    print("Database seeded!")