import random
from flask import Flask, request, jsonify, make_response, session, redirect, url_for, render_template
from flask_migrate import Migrate
from flask_cors import CORS
from flask_restful import Api, Resource
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.exceptions import NotFound
from datetime import timedelta, datetime

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config["JWT_SECRET_KEY"] = "fsbdgfnhgvjnvhmvh" + str(random.randint(1, 1000000000000))
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=1)
app.config["SECRET_KEY"] = "JKSRVHJVFBSRDFV" + str(random.randint(1, 1000000000000))
app.json.compact = False
api = Api(app)

from models import db, User, Product, Bid

db.init_app(app)
jwt = JWTManager(app)
migrate = Migrate(app, db)

# Role-based decorator
def role_required(roles):
    def wrapper(fn):
        @jwt_required()
        def decorated_function(*args, **kwargs):
            user_id = get_jwt_identity()['user_id']
            user = User.query.get(user_id)
            if user and user.role not in roles:
                return {"message": f"{roles} role required"}, 403
            return fn(*args, **kwargs)
        return decorated_function
    return wrapper

# Error handler
@app.errorhandler(NotFound)
def handle_not_found(e):
    response = make_response(
        jsonify({'error': 'NotFound', 'message': 'The requested resource does not exist'}),
        404
    )
    response.headers['Content-Type'] = 'application/json'
    return response

app.register_error_handler(404, handle_not_found)



class UserResource(Resource):
    @role_required(['admin'])  # Only admin can view all users
    def get(self, user_id=None):
        if user_id:
            user = User.query.get(user_id)
            if user:
                return user.to_dict(), 200
            return {'error': 'User not found'}, 404
        users = User.query.all()
        return [user.to_dict() for user in users], 200

    @jwt_required()  # Only logged-in users can update their own profile
    def patch(self, user_id):
        user = User.query.get(user_id)
        if not user:
            return {'error': 'User not found'}, 404
        data = request.get_json()
        for key, value in data.items():
            setattr(user, key, value)
        db.session.commit()
        return user.to_dict(), 200

    @role_required(['admin'])  # Only admin can delete users
    def delete(self, user_id):
        user = User.query.get(user_id)
        if not user:
            return {'error': 'User not found'}, 404
        db.session.delete(user)
        db.session.commit()
        return {'message': 'User deleted successfully'}, 200

class BiddingResource(Resource):
    @role_required(['customer'])  # Only customer can bid on products
    def get(self):
        bids = Bid.query.all()
        return [bid.to_dict() for bid in bids], 200

    @role_required(['customer'])  # Only customers can post bids
    def post(self):
        user_id = get_jwt_identity()['user_id']
        data = request.get_json()
        product_id = data.get('product_id')
        amount = data.get('amount')
        bidding_time=data.get('bidding_time')
        highest_bid=data.get('highest_bid')

        # Validate if the product exists and is available
        product = Product.query.get(product_id)
        if not product or product.status != 'available':
            return {"message": "Product not available for bidding."}, 400

        bid = Bid(user_id=user_id, product_id=product_id, amount=amount, bidding_time=bidding_time, highest_bid=highest_bid)
        db.session.add(bid)
        db.session.commit()

        return bid.to_dict(), 201
    
class ProductResource(Resource):
    @jwt_required()
    @role_required(['admin'])  # Only addmins can add new products
    def post(self):
        user_identity = get_jwt_identity()
        user_id = user_identity.get('user_id')

        name = request.form.get('name')
        description = request.form.get('description')
        price_tag = request.form.get('price_tag')
        quantity=request.form.get('quantity')
        bidding_end_time=request.form.get('bidding_end_time')
       
        if not all([name, description, price_tag]):
            return {"message": "All fields are required"}, 400

        try:
            price_tag = float(price_tag)
        except ValueError:
            return {"message": "Invalid value for price tag"}, 400

        new_product = Product(
            name=name,
            description=description,
            price_tag=price_tag,
            user_id=user_id,
            quantity=quantity,
            bidding_end_time=bidding_end_time
        )

        db.session.add(new_product)
        db.session.commit()

        return new_product.to_dict(), 201
    
    @jwt_required()
    # a logged in user can view all products
    def get(self, product_id=None):
        if product_id:
            product = Product.query.get(product_id)
            if not product:
                return {"message": "Product not found"}, 404
            return product.to_dict(), 200

        status = request.args.get('status')
        query = Product.query
        if status:
            query = query.filter_by(status=status)
            products = query.all()
        return jsonify([product.to_dict() for product in products])

    @jwt_required()
    @role_required(['admin'])  # Only admins can update products
    def put(self, product_id):
        user_identity = get_jwt_identity()
        user_id = user_identity.get('user_id')

        product = Product.query.get(product_id)
        if not product:
            return {"message": "Product not found"}, 404

        if product.user_id != user_id:
            return {"message": "You are not authorized to update this product"}, 403

        name = request.form.get('title', product.name)
        description = request.form.get('description', product.description)
        price_tag = request.form.get('price_tag', product.price_tag)
        quantity=request.form.get('quantity', product.quantity)
        bidding_end_time=request.form.get('bidding_end_time', product.bidding_end_time)
        

        try:
            if price_tag:
                price_tag = float(price_tag)
        except ValueError:
            return {"message": "Invalid value for price tag, pages, or due date"}, 400

        product.name = name
        product.description = description
        product.price_tag = price_tag
        product.quantity=quantity
        product.bidding_end_time=bidding_end_time

        db.session.commit()
        return product.to_dict(), 200

    @jwt_required()
    @role_required(['admin'])  # Only admins can delete products
    def delete(self, product_id):
        user_identity = get_jwt_identity()
        user_id = user_identity.get('user_id')

        product = Product.query.get(product_id)
        if not product:
            return {"message": "Product not found"}, 404

        if product.user_id != user_id:
            return {"message": "You are not authorized to delete this product"}, 403

        db.session.delete(product)
        db.session.commit()
        return {"message": "Product deleted successfully"}, 200

#    login resource
class Login(Resource):
    def post(self):
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            access_token = create_access_token(identity={'user_id': user.id, 'role': user.role})
            return {
                'message': f"Welcome {user.username}",
                'access_token': access_token,
                'username': user.username,
                'email': user.email,
                'user_id': user.id,
                'role': user.role  
            }, 200
        return {"error": "Invalid username or password"}, 401
# register resource
class Register(Resource):
    def post(self):
        data = request.form
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        role = data.get('role', 'customer')  # Default to customer  role if not provided

        if not username or not password or not email:
            return {'message': 'username, password, and email are required'}, 400

        # Check if the user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return {'message': 'User already exists'}, 400

        new_user = User(username=username, email=email, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        return {'message': 'User registered successfully'}, 201

class CheckSession(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()['user_id']
        user = User.query.get(user_id)

        if user:
            return jsonify(user.to_dict()), 200
        return jsonify({"error": "User not found"}), 404

# logout resource
class Logout(Resource):
    @jwt_required()
    def post(self):
        session.pop('user_id', None)
        return jsonify({"message": "Logout successful"})

# Register API endpoints
api.add_resource(UserResource, '/users', '/users/<int:user_id>')
api.add_resource(ProductResource, '/products', '/products/<int:product_id>')
api.add_resource(BiddingResource, '/bids')
api.add_resource(Login, '/login')
api.add_resource(Register, '/register')
api.add_resource(CheckSession, '/session')
api.add_resource(Logout, '/logout')

if __name__ == '__main__':
    app.run(port=5555, debug=True)