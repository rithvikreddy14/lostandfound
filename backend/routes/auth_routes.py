from flask import Blueprint, request, jsonify

def create_auth_bp(db_service, auth_service):
    bp = Blueprint('auth_routes', __name__)

    @bp.route('/signup', methods=['POST'])
    def signup():
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')

        if not name or not email or not password:
            return jsonify({"message": "Name, email, and password are required"}), 400

        if db_service.users.find_user_by_email(email):
            return jsonify({"message": "User with this email already exists"}), 409

        hashed_password = auth_service.hash_password(password)
        user_data = {
            "name": name,
            "email": email,
            "password_hash": hashed_password
        }
        user_id = db_service.users.create_user(user_data)
        
        token = auth_service.generate_jwt(user_id)
        return jsonify({"access_token": token}), 201

    @bp.route('/login', methods=['POST'])
    def login():
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        user = db_service.users.find_user_by_email(email)
        if user and auth_service.check_password(user['password_hash'], password):
            token = auth_service.generate_jwt(user['_id'])
            return jsonify({"access_token": token}), 200
        else:
            return jsonify({"message": "Invalid email or password"}), 401
    
    return bp