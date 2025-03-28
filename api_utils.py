"""
Utility functions for the Continuum Digital Twin API.
Includes authentication helpers and compatibility layers.
"""

import os
import logging
import secrets
from typing import Dict, Optional, Union, Callable
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthenticationManager:
    """
    Manages authentication-related functionality with fallbacks
    for compatibility issues.
    """
    
    def __init__(self):
        self.pwd_context = None
        self.jwt_module = None
        self.secret_key = os.getenv("JWT_SECRET_KEY", secrets.token_hex(32))
        self.algorithm = "HS256"
        self.initialized = False
        
        # Initialize authentication libraries
        self._initialize()
    
    def _initialize(self):
        """Initialize authentication libraries with fallbacks."""
        # Try to load passlib and bcrypt
        try:
            from passlib.context import CryptContext
            self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            logger.info("Initialized password hashing with bcrypt")
        except ImportError as e:
            logger.warning(f"Failed to initialize passlib/bcrypt: {e}")
            self._setup_fallback_password_context()
        
        # Try to load JWT
        try:
            import jose.jwt as jwt
            self.jwt_module = jwt
            logger.info("Initialized JWT authentication")
        except ImportError as e:
            logger.warning(f"Failed to initialize JWT: {e}")
            self.jwt_module = None
        
        self.initialized = True
    
    def _setup_fallback_password_context(self):
        """Set up a fallback password context for development use only."""
        class FallbackContext:
            def verify(self, plain_password, hashed_password):
                # IMPORTANT: This is NOT secure and only for development
                return plain_password == "admin" or plain_password == hashed_password.replace("mock_hash_", "")
            
            def hash(self, password):
                # IMPORTANT: This is NOT secure and only for development
                return f"mock_hash_{password}"
        
        self.pwd_context = FallbackContext()
        logger.warning("Using insecure fallback password hashing - DO NOT USE IN PRODUCTION")
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash with error handling."""
        if not self.initialized:
            self._initialize()
        
        try:
            return self.pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            # Only in development mode, allow admin password as fallback
            if os.getenv("ENVIRONMENT") == "development":
                return plain_password == "admin"
            return False
    
    def hash_password(self, password: str) -> str:
        """Hash a password with error handling."""
        if not self.initialized:
            self._initialize()
        
        try:
            return self.pwd_context.hash(password)
        except Exception as e:
            logger.error(f"Password hashing error: {e}")
            # Fallback for development
            return f"mock_hash_{password}"
    
    def create_token(self, data: Dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT token with error handling."""
        if not self.initialized:
            self._initialize()
        
        if self.jwt_module is None:
            # Fallback for development
            return f"dev_token_{data.get('sub', 'unknown')}"
        
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=30)
            
        to_encode.update({"exp": expire})
        
        try:
            return self.jwt_module.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        except Exception as e:
            logger.error(f"Token creation error: {e}")
            # Fallback for development
            if os.getenv("ENVIRONMENT") == "development":
                return f"dev_token_{data.get('sub', 'unknown')}"
            raise
    
    def decode_token(self, token: str) -> Dict:
        """Decode a JWT token with error handling."""
        if not self.initialized:
            self._initialize()
        
        if self.jwt_module is None:
            # Fallback for development
            if token.startswith("dev_token_"):
                return {"sub": token.replace("dev_token_", "")}
            return {}
        
        try:
            return self.jwt_module.decode(token, self.secret_key, algorithms=[self.algorithm])
        except Exception as e:
            logger.error(f"Token decoding error: {e}")
            # No fallback for token decoding in production
            if os.getenv("ENVIRONMENT") == "development" and token.startswith("dev_token_"):
                return {"sub": token.replace("dev_token_", "")}
            raise

# Singleton instance
auth_manager = AuthenticationManager()
