"""
Request validation utilities for the e-commerce API
Contains functions to validate incoming request data
"""

from typing import Optional, Dict, Any


def validate_add_item_request(data: Optional[Dict[str, Any]]) -> Optional[str]:
    """
    Validate add item to cart request data
    
    Args:
        data: Request JSON data
        
    Returns:
        Error message if validation fails, None if valid
    """
    if not data:
        return "Request body is required"
    
    # Required fields
    required_fields = ['item_id', 'name', 'price', 'quantity']
    for field in required_fields:
        if field not in data:
            return f"Missing required field: {field}"
    
    # Validate field types and values
    if not isinstance(data['item_id'], str) or not data['item_id'].strip():
        return "item_id must be a non-empty string"
    
    if not isinstance(data['name'], str) or not data['name'].strip():
        return "name must be a non-empty string"
    
    if not isinstance(data['price'], (int, float)) or data['price'] < 0:
        return "price must be a non-negative number"
    
    if not isinstance(data['quantity'], int) or data['quantity'] <= 0:
        return "quantity must be a positive integer"
    
    return None


def validate_checkout_request(data: Optional[Dict[str, Any]]) -> Optional[str]:
    """
    Validate checkout request data
    
    Args:
        data: Request JSON data
        
    Returns:
        Error message if validation fails, None if valid
    """
    # Checkout request body is optional (for discount code)
    if data is None:
        return None
    
    # If data is provided, validate discount_code if present
    if 'discount_code' in data:
        if not isinstance(data['discount_code'], str) or not data['discount_code'].strip():
            return "discount_code must be a non-empty string"
    
    # Check for unexpected fields
    allowed_fields = ['discount_code']
    for field in data:
        if field not in allowed_fields:
            return f"Unexpected field: {field}"
    
    return None


def validate_user_id(user_id: str) -> Optional[str]:
    """
    Validate user ID parameter
    
    Args:
        user_id: User identifier from URL parameter
        
    Returns:
        Error message if validation fails, None if valid
    """
    if not user_id or not user_id.strip():
        return "user_id cannot be empty"
    
    # Basic validation - can be extended for specific format requirements
    if len(user_id.strip()) < 1:
        return "user_id must be at least 1 character long"
    
    return None


def validate_pagination_params(page: Optional[str], per_page: Optional[str]) -> tuple[Optional[str], int, int]:
    """
    Validate pagination parameters
    
    Args:
        page: Page number as string
        per_page: Items per page as string
        
    Returns:
        Tuple of (error_message, page_int, per_page_int)
    """
    try:
        page_int = int(page) if page else 1
        per_page_int = int(per_page) if per_page else 10
        
        if page_int < 1:
            return "page must be a positive integer", 1, 10
        
        if per_page_int < 1 or per_page_int > 100:
            return "per_page must be between 1 and 100", 1, 10
        
        return None, page_int, per_page_int
        
    except ValueError:
        return "page and per_page must be valid integers", 1, 10