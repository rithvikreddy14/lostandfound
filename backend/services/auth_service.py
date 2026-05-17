from datetime import datetime, timedelta
import jwt
from flask_bcrypt import Bcrypt

class AuthService:
    def __init__(self, db_service, secret_key):
        self.db = db_service
        self.secret_key = secret_key
        self.bcrypt = Bcrypt()

    def hash_password(self, password):
        """Hashes a password using bcrypt."""
        return self.bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, hashed_password, password):
        """Checks if a password matches a hash."""
        return self.bcrypt.check_password_hash(hashed_password, password)

    def generate_jwt(self, user_id):
        """Generates a JWT access token."""
        payload = {
            'exp': datetime.utcnow() + timedelta(hours=24),
            'iat': datetime.utcnow(),
            'sub': user_id
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')

    def decode_jwt(self, token):
        """Decodes a JWT access token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload['sub']
        except jwt.ExpiredSignatureError:
            return None # Signature has expired
        except jwt.InvalidTokenError:
            return None # Invalid token