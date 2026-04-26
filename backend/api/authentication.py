from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from .models import User
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class CustomJWTAuthentication(JWTAuthentication):   # Extend JWT authentication class


    def authenticate(self, request):    # Override authenticate method

        header_auth = self.get_header(request)   # Get Authorization header
        logger.debug(f"Header Authorization: {header_auth}")

        if header_auth is not None: # Check if header exists
            raw_token = self.get_raw_token(header_auth) # Extract raw token from header
            if raw_token is not None:    # Check if token exists
                try:     # Try to validate token
                    validated_token = self.get_validated_token(raw_token)        # Validate JWT token
                    user = self.get_user(validated_token)   # Get user from token
                    logger.debug(
                        f"Authenticated user from header: {user.username}")
                    return (user, validated_token)
                except Exception as e:
                    logger.debug(f"Header token invalid: {e}")
             


        cookie_token = request.COOKIES.get("access_token")  # Get token from cookies
        logger.debug(f"Cookie access_token: {cookie_token}")

        if cookie_token is not None:    # Check if cookie token exists
            try:
                validated_token = self.get_validated_token(cookie_token)    # Validate JWT token
                user = self.get_user(validated_token)   # Get user from token
                logger.debug(
                    f"Authenticated user from cookie: {user.username}")
                return (user, validated_token)
            except Exception as e:   # Catch validation errors
                logger.debug(f"Cookie token invalid: {e}")
                return None

  
        logger.debug("No JWT token found in header or cookie")
        return None

    def get_user(self, validated_token):     # Extract user from validated token

        user_id = validated_token.get("user_id")    # Get user_id from token
        if not user_id: # Try converting to ObjectId
            logger.debug("Token don't have user_id")
            raise AuthenticationFailed(
                "Token contained no user_id", code="no_user_id")

        logger.debug(f"Token user_id: {user_id}")

   
        try:    # Try converting to ObjectId
            oid = ObjectId(user_id)     # Convert string to ObjectId
        except Exception as e:   # Catch conversion error
            logger.debug(f"user_id invaild : {user_id}, error: {e}")
            raise AuthenticationFailed(
                "Invalid user_id format", code="invalid_user_id")

        # Lấy user từ DB
        try:
            user = User.objects.get(_id=oid)    # Query user by ObjectId
        except User.DoesNotExist:   # If user not found
            logger.debug(f"Not found user with _id={oid}")
            raise AuthenticationFailed("User not found", code="user_not_found")
        
        logger.debug(f"Found user : {user.username}")    # Raise error
        return user
    
    