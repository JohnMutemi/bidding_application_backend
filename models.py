from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from sqlalchemy.orm import validates
from sqlalchemy_serializer import SerializerMixin
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

metadata = MetaData(naming_convention={
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"
})

db = SQLAlchemy(metadata=metadata)



class User(db.Model, SerializerMixin):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    _password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='customer') 
    products = db.relationship('Product', backref='user', lazy=True)

    serialize_rules = ('-password_hash', '-products')

    def __repr__(self):
        return f'<User {self.username}>'

    @property
    def password_hash(self):
        return self._password_hash

    @password_hash.setter
    def password_hash(self, password):
        self._password_hash = generate_password_hash(password)

    def set_password(self, password):
        self.password_hash = password

    def check_password(self, password):
        return check_password_hash(self._password_hash, password)

    @validates('username')
    def validate_username(self, key, username):
        if not username:
            raise ValueError("Username cannot be empty")
        if len(username) > 50:
            raise ValueError("Username must be 50 characters or less")
        return username

    @validates('email')
    def validate_email(self, key, email):
        if not email:
            raise ValueError("Email cannot be empty")
        if len(email) > 120:
            raise ValueError("Email must be 120 characters or less")
        
        return email

    @validates('role')
    def validate_role(self, key, role):
        valid_roles = ['admin', 'customer']
        if role not in valid_roles:
            raise ValueError(f"Invalid role. Must be one of {valid_roles}")
        return role

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role, 
        }


class Product(db.Model, SerializerMixin):
    __tablename__ = 'product'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price_tag = db.Column(db.Float, nullable=False)  
    quantity=db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='available')  
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    bidding_end_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Exclude the 'user' field from serialization to avoid recursion
    serialize_rules = ('-user',)

    STATUS_OPTIONS = ['available', 'sold']

    def __repr__(self):
        return f'<Product {self.name}>'

    @validates('name')
    def validate_title(self, key, name):
        if not name:
            raise ValueError("Name cannot be empty.")
        if len(name) > 30:
            raise ValueError("Name must be 30 characters or less.")
        return name

    @validates('price_tag')
    def validate_price(self, key, price_tag):
        if price_tag <= 0:
            raise ValueError("Price tag must be positive.")
        return price_tag


    @validates('status')
    def validate_status(self, key, status):
        if status not in self.STATUS_OPTIONS:
            raise ValueError(f"Invalid status. Must be one of {self.STATUS_OPTIONS}.")
        return status


    def to_dict(self):
        """Convert the product to a dictionary for JSON serialization."""
        return {
            'id': self.id,
            'name': self.title,
            'description': self.description,
            'price_tag': self.price_tag,
            'quantity':self.quantity,
            'status': self.status,
            'user_id': self.user_id,
            'bidding_end_time':self.bidding_end_time.isoformat()
        }


class Bid(db.Model):
    __tablename__ = 'bids'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending') 
    bidding_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    highest_bid=db.Column(db.Float, nullable=False)

    # Define relationships
    user = db.relationship('User', backref='bids', lazy=True)  
    product = db.relationship('Product', backref='bids', lazy=True)

    STATUS_OPTIONS = ['pending', 'accepted', 'rejected']

    def __repr__(self):
        return f'<Bid {self.id} by User {self.user_id} for Product {self.product_id}>'
    
    @validates('amount')
    def validate_amount(self, key, amount):
        try:
            amount = float(amount)  
        except ValueError:
            raise ValueError("Bid amount must be a valid number.")
        
        if amount <= 0:
            raise ValueError("Bid amount must be positive.")
        return amount



    @validates('status')
    def validate_status(self, key, status):
        if status not in self.STATUS_OPTIONS:
            raise ValueError(f"Invalid status. Must be one of {self.STATUS_OPTIONS}.")
        return status

    def to_dict(self):
        # Convert the bid to a dictionary for JSON serialization.
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user': self.user.username if self.user else 'Unknown',  
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else 'Unknown',  
            'amount': self.amount,
            'status': self.status,
            'bidding_time': self.bidding_time.isoformat(),
            'highest_bid':self.highest_bid
        }