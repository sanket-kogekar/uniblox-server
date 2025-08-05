"""
Data models for the e-commerce store
Contains all data structures and in-memory storage implementation
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid


@dataclass
class Item:
    """Represents an item in the store"""
    item_id: str
    name: str
    price: float
    quantity: int
    
    def __post_init__(self):
        """Validate item data after initialization"""
        if self.price < 0:
            raise ValueError("Price cannot be negative")
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")
    
    def to_dict(self) -> dict:
        """Convert item to dictionary"""
        return {
            "item_id": self.item_id,
            "name": self.name,
            "price": self.price,
            "quantity": self.quantity,
            "subtotal": self.price * self.quantity
        }


@dataclass
class Cart:
    """Represents a user's shopping cart"""
    user_id: str
    items: List[Item] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def add_item(self, item: Item):
        """Add item to cart or update quantity if item already exists"""
        existing_item = self.find_item(item.item_id)
        if existing_item:
            existing_item.quantity += item.quantity
        else:
            self.items.append(item)
        self.updated_at = datetime.utcnow()
    
    def find_item(self, item_id: str) -> Optional[Item]:
        """Find item in cart by item_id"""
        return next((item for item in self.items if item.item_id == item_id), None)
    
    def get_total(self) -> float:
        """Calculate total cart value"""
        return sum(item.price * item.quantity for item in self.items)
    
    def get_item_count(self) -> int:
        """Get total number of items in cart"""
        return sum(item.quantity for item in self.items)
    
    def clear(self):
        """Clear all items from cart"""
        self.items.clear()
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert cart to dictionary"""
        return {
            "user_id": self.user_id,
            "items": [item.to_dict() for item in self.items],
            "total_items": self.get_item_count(),
            "total_amount": self.get_total(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


@dataclass
class DiscountCode:
    """Represents a discount code"""
    code: str
    discount_percentage: float
    is_used: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Set default expiration if not provided"""
        if self.expires_at is None:
            # Discount codes expire after 30 days by default
            self.expires_at = self.created_at + timedelta(days=30)
    
    def is_valid(self) -> bool:
        """Check if discount code is valid and not expired"""
        if self.is_used:
            return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        return True
    
    def use(self):
        """Mark discount code as used"""
        self.is_used = True
        self.used_at = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert discount code to dictionary"""
        return {
            "code": self.code,
            "discount_percentage": self.discount_percentage,
            "is_used": self.is_used,
            "created_at": self.created_at.isoformat(),
            "used_at": self.used_at.isoformat() if self.used_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_valid": self.is_valid()
        }


@dataclass
class Order:
    """Represents a completed order"""
    order_id: str
    user_id: str
    items: List[Item]
    subtotal: float
    discount_code: Optional[str] = None
    discount_amount: float = 0.0
    total_amount: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Calculate total amount after initialization"""
        if self.total_amount == 0.0:
            self.total_amount = self.subtotal - self.discount_amount
    
    def to_dict(self) -> dict:
        """Convert order to dictionary"""
        return {
            "order_id": self.order_id,
            "user_id": self.user_id,
            "items": [item.to_dict() for item in self.items],
            "subtotal": self.subtotal,
            "discount_code": self.discount_code,
            "discount_amount": self.discount_amount,
            "total_amount": self.total_amount,
            "created_at": self.created_at.isoformat()
        }


class InMemoryStore:
    """
    In-memory data store for the e-commerce application
    
    This class manages all data persistence using Python dictionaries.
    In a production environment, this would be replaced with a proper database.
    """
    
    def __init__(self):
        """Initialize empty data stores"""
        # Store user carts - key: user_id, value: Cart
        self.carts: Dict[str, Cart] = {}
        
        # Store completed orders - key: order_id, value: Order
        self.orders: Dict[str, Order] = {}
        
        # Store discount codes - key: code, value: DiscountCode
        self.discount_codes: Dict[str, DiscountCode] = {}
        
        # Track order count for discount code generation
        self.order_counter = 0
    
    def get_cart(self, user_id: str) -> Cart:
        """Get or create cart for user"""
        if user_id not in self.carts:
            self.carts[user_id] = Cart(user_id=user_id)
        return self.carts[user_id]
    
    def save_cart(self, cart: Cart):
        """Save cart to store"""
        self.carts[cart.user_id] = cart
    
    def delete_cart(self, user_id: str):
        """Delete cart from store"""
        if user_id in self.carts:
            del self.carts[user_id]
    
    def save_order(self, order: Order):
        """Save order to store"""
        self.orders[order.order_id] = order
        self.order_counter += 1
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID"""
        return self.orders.get(order_id)
    
    def save_discount_code(self, discount_code: DiscountCode):
        """Save discount code to store"""
        self.discount_codes[discount_code.code] = discount_code
    
    def get_discount_code(self, code: str) -> Optional[DiscountCode]:
        """Get discount code by code"""
        return self.discount_codes.get(code)
    
    def get_all_orders(self) -> List[Order]:
        """Get all orders"""
        return list(self.orders.values())
    
    def get_all_discount_codes(self) -> List[DiscountCode]:
        """Get all discount codes"""
        return list(self.discount_codes.values())
    
    def get_unused_discount_codes(self) -> List[DiscountCode]:
        """Get all unused and valid discount codes"""
        return [dc for dc in self.discount_codes.values() if dc.is_valid()]
    
    def get_total_items_purchased(self) -> int:
        """Calculate total number of items purchased across all orders"""
        return sum(
            sum(item.quantity for item in order.items)
            for order in self.orders.values()
        )
    
    def get_total_purchase_amount(self) -> float:
        """Calculate total purchase amount across all orders"""
        return sum(order.total_amount for order in self.orders.values())
    
    def get_total_discount_amount(self) -> float:
        """Calculate total discount amount given across all orders"""
        return sum(order.discount_amount for order in self.orders.values())
    
    def reset(self):
        """Reset all data (useful for testing)"""
        self.carts.clear()
        self.orders.clear()
        self.discount_codes.clear()
        self.order_counter = 0