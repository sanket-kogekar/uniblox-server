"""
Service layer containing business logic for the e-commerce store
Handles cart operations, order processing, discount management, and admin functions
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, List
import logging

from models import InMemoryStore, Cart, Order, Item, DiscountCode

logger = logging.getLogger(__name__)


class CartService:
    """Service for managing shopping cart operations"""
    
    def __init__(self, store: InMemoryStore):
        self.store = store
    
    def add_item_to_cart(self, user_id: str, item: Item) -> Cart:
        """
        Add an item to user's cart
        
        Args:
            user_id: User identifier
            item: Item to add to cart
            
        Returns:
            Updated cart object
            
        Raises:
            ValueError: If item data is invalid
        """
        if not user_id.strip():
            raise ValueError("User ID cannot be empty")
        
        cart = self.store.get_cart(user_id)
        cart.add_item(item)
        self.store.save_cart(cart)
        
        logger.info(f"Added item {item.item_id} (qty: {item.quantity}) to cart for user {user_id}")
        return cart
    
    def get_cart(self, user_id: str) -> Cart:
        """
        Get user's current cart
        
        Args:
            user_id: User identifier
            
        Returns:
            User's cart object
        """
        return self.store.get_cart(user_id)
    
    def clear_cart(self, user_id: str):
        """
        Clear all items from user's cart
        
        Args:
            user_id: User identifier
        """
        cart = self.store.get_cart(user_id)
        cart.clear()
        self.store.save_cart(cart)
        logger.info(f"Cleared cart for user {user_id}")
    
    def remove_item_from_cart(self, user_id: str, item_id: str) -> Cart:
        """
        Remove an item from user's cart
        
        Args:
            user_id: User identifier
            item_id: Item to remove
            
        Returns:
            Updated cart object
            
        Raises:
            ValueError: If item is not found in cart
        """
        cart = self.store.get_cart(user_id)
        item = cart.find_item(item_id)
        
        if not item:
            raise ValueError(f"Item {item_id} not found in cart")
        
        cart.items.remove(item)
        cart.updated_at = datetime.utcnow()
        self.store.save_cart(cart)
        
        logger.info(f"Removed item {item_id} from cart for user {user_id}")
        return cart


class OrderService:
    """Service for managing order operations"""
    
    def __init__(self, store: InMemoryStore):
        self.store = store
    
    def create_order(self, cart: Cart, discount_code: Optional[str] = None) -> Order:
        """
        Create an order from a cart
        
        Args:
            cart: Cart to convert to order
            discount_code: Optional discount code to apply
            
        Returns:
            Created order object
            
        Raises:
            ValueError: If cart is empty or discount code is invalid
        """
        if not cart.items:
            raise ValueError("Cannot create order from empty cart")
        
        # Calculate subtotal
        subtotal = cart.get_total()
        discount_amount = 0.0
        
        # Apply discount if code is provided
        if discount_code:
            discount = self.store.get_discount_code(discount_code)
            if not discount or not discount.is_valid():
                raise ValueError("Invalid or expired discount code")
            
            discount_amount = subtotal * (discount.discount_percentage / 100)
        
        # Create order
        order = Order(
            order_id=str(uuid.uuid4()),
            user_id=cart.user_id,
            items=cart.items.copy(),  # Copy items to preserve order data
            subtotal=subtotal,
            discount_code=discount_code,
            discount_amount=discount_amount,
            total_amount=subtotal - discount_amount
        )
        
        self.store.save_order(order)
        logger.info(f"Created order {order.order_id} for user {cart.user_id} with total {order.total_amount}")
        
        return order
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """
        Get order by ID
        
        Args:
            order_id: Order identifier
            
        Returns:
            Order object if found, None otherwise
        """
        return self.store.get_order(order_id)
    
    def get_user_orders(self, user_id: str) -> List[Order]:
        """
        Get all orders for a specific user
        
        Args:
            user_id: User identifier
            
        Returns:
            List of user's orders
        """
        return [order for order in self.store.get_all_orders() if order.user_id == user_id]


class DiscountService:
    """Service for managing discount codes"""
    
    def __init__(self, store: InMemoryStore):
        self.store = store
        self.discount_percentage = 10.0  # 10% discount
    
    def generate_discount_code(self) -> DiscountCode:
        """
        Generate a new discount code
        
        Returns:
            Generated discount code object
        """
        code = f"DISCOUNT{uuid.uuid4().hex[:8].upper()}"
        
        discount_code = DiscountCode(
            code=code,
            discount_percentage=self.discount_percentage
        )
        
        self.store.save_discount_code(discount_code)
        logger.info(f"Generated new discount code: {code}")
        
        return discount_code
    
    def is_discount_code_valid(self, code: str) -> bool:
        """
        Check if a discount code is valid
        
        Args:
            code: Discount code to validate
            
        Returns:
            True if code is valid and unused, False otherwise
        """
        discount = self.store.get_discount_code(code)
        return discount is not None and discount.is_valid()
    
    def use_discount_code(self, code: str):
        """
        Mark a discount code as used
        
        Args:
            code: Discount code to mark as used
            
        Raises:
            ValueError: If code is not found or already used
        """
        discount = self.store.get_discount_code(code)
        
        if not discount:
            raise ValueError("Discount code not found")
        
        if not discount.is_valid():
            raise ValueError("Discount code is expired or already used")
        
        discount.use()
        self.store.save_discount_code(discount)
        logger.info(f"Marked discount code {code} as used")
    
    def has_unused_discount_code(self) -> bool:
        """
        Check if there are any unused discount codes available
        
        Returns:
            True if there's at least one unused discount code, False otherwise
        """
        return len(self.store.get_unused_discount_codes()) > 0
    
    def get_available_discount_codes(self) -> List[DiscountCode]:
        """
        Get all available (unused and not expired) discount codes
        
        Returns:
            List of available discount codes
        """
        return self.store.get_unused_discount_codes()


class AdminService:
    """Service for admin operations and statistics"""
    
    def __init__(self, store: InMemoryStore):
        self.store = store
    
    def get_store_statistics(self) -> Dict:
        """
        Get comprehensive store statistics
        
        Returns:
            Dictionary containing store statistics
        """
        orders = self.store.get_all_orders()
        discount_codes = self.store.get_all_discount_codes()
        
        # Calculate statistics
        total_orders = len(orders)
        total_items_purchased = self.store.get_total_items_purchased()
        total_purchase_amount = self.store.get_total_purchase_amount()
        total_discount_amount = self.store.get_total_discount_amount()
        
        # Discount code statistics
        total_discount_codes = len(discount_codes)
        used_discount_codes = len([dc for dc in discount_codes if dc.is_used])
        available_discount_codes = len(self.store.get_unused_discount_codes())
        
        # Revenue statistics
        average_order_value = total_purchase_amount / total_orders if total_orders > 0 else 0
        
        stats = {
            "orders": {
                "total_orders": total_orders,
                "total_items_purchased": total_items_purchased,
                "total_purchase_amount": round(total_purchase_amount, 2),
                "average_order_value": round(average_order_value, 2)
            },
            "discounts": {
                "total_discount_codes": total_discount_codes,
                "used_discount_codes": used_discount_codes,
                "available_discount_codes": available_discount_codes,
                "total_discount_amount": round(total_discount_amount, 2),
                "discount_codes": [dc.to_dict() for dc in discount_codes]
            },
            "revenue": {
                "gross_revenue": round(total_purchase_amount + total_discount_amount, 2),
                "net_revenue": round(total_purchase_amount, 2),
                "total_savings_given": round(total_discount_amount, 2)
            }
        }
        
        logger.info("Generated store statistics")
        return stats
    
    def get_order_summary(self) -> List[Dict]:
        """
        Get summary of all orders
        
        Returns:
            List of order summaries
        """
        orders = self.store.get_all_orders()
        return [
            {
                "order_id": order.order_id,
                "user_id": order.user_id,
                "total_amount": order.total_amount,
                "discount_applied": order.discount_code is not None,
                "discount_amount": order.discount_amount,
                "created_at": order.created_at.isoformat()
            }
            for order in orders
        ]
    
    def get_discount_code_summary(self) -> Dict:
        """
        Get summary of discount codes
        
        Returns:
            Dictionary containing discount code statistics
        """
        discount_codes = self.store.get_all_discount_codes()
        
        return {
            "total_codes": len(discount_codes),
            "used_codes": len([dc for dc in discount_codes if dc.is_used]),
            "available_codes": len(self.store.get_unused_discount_codes()),
            "codes": [dc.to_dict() for dc in discount_codes]
        }