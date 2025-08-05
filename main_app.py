"""
E-commerce Store API
Main Flask application with cart and checkout functionality
"""

from flask import Flask, request, jsonify
from datetime import datetime
import uuid
from typing import Dict, List, Optional
import logging
from flask_cors import CORS

from models import InMemoryStore, Cart, Order, Item, DiscountCode
from services import CartService, OrderService, DiscountService, AdminService
from validators import validate_add_item_request, validate_checkout_request

app = Flask(__name__)
CORS(app, origins=["https://uniblox-ten.vercel.app"])

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
store = InMemoryStore()
cart_service = CartService(store)
order_service = OrderService(store)
discount_service = DiscountService(store)
admin_service = AdminService(store)

# Configuration
DISCOUNT_ORDER_FREQUENCY = 3  # Every 3rd order gets a discount code


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})


@app.route('/cart/<user_id>/items', methods=['POST'])
def add_item_to_cart(user_id: str):
    """
    Add item to user's cart
    
    Expected payload:
    {
        "item_id": "string",
        "name": "string",
        "price": float,
        "quantity": int
    }
    """
    try:
        # Validate request data
        validation_error = validate_add_item_request(request.json)
        if validation_error:
            return jsonify({"error": validation_error}), 400
        
        data = request.json
        item = Item(
            item_id=data['item_id'],
            name=data['name'],
            price=data['price'],
            quantity=data['quantity']
        )
        
        cart = cart_service.add_item_to_cart(user_id, item)
        
        logger.info(f"Item {item.item_id} added to cart for user {user_id}")
        
        return jsonify({
            "message": "Item added to cart successfully",
            "cart": cart.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error adding item to cart: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/cart/<user_id>', methods=['GET'])
def get_cart(user_id: str):
    """Get user's current cart"""
    try:
        cart = cart_service.get_cart(user_id)
        return jsonify(cart.to_dict()), 200
    except Exception as e:
        logger.error(f"Error retrieving cart: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/cart/<user_id>/checkout', methods=['POST'])
def checkout(user_id: str):
    """
    Checkout user's cart and place order
    
    Expected payload:
    {
        "discount_code": "string" (optional)
    }
    """
    try:
        # Validate request data
        validation_error = validate_checkout_request(request.json)
        if validation_error:
            return jsonify({"error": validation_error}), 400
        
        data = request.json or {}
        discount_code = data.get('discount_code')
        
        # Get user's cart
        cart = cart_service.get_cart(user_id)
        
        if not cart.items:
            return jsonify({"error": "Cart is empty"}), 400
        
        # Validate discount code if provided
        if discount_code:
            if not discount_service.is_discount_code_valid(discount_code):
                return jsonify({"error": "Invalid or expired discount code"}), 400
        
        # Process checkout
        order = order_service.create_order(cart, discount_code)
        
        # Mark discount code as used if it was applied
        if discount_code:
            discount_service.use_discount_code(discount_code)
        
        # Clear the cart
        cart_service.clear_cart(user_id)
        
        # Check if this order qualifies for a discount code
        total_orders = len(store.orders)
        if total_orders % DISCOUNT_ORDER_FREQUENCY == 0:
            new_discount_code = discount_service.generate_discount_code()
            logger.info(f"New discount code generated: {new_discount_code.code}")
        
        logger.info(f"Order {order.order_id} created for user {user_id}")
        
        return jsonify({
            "message": "Order placed successfully",
            "order": order.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error during checkout: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/admin/discount-codes', methods=['POST'])
def generate_discount_code():
    """
    Admin endpoint to manually generate a discount code
    """
    try:
        # Check if we should generate a discount code
        total_orders = len(store.orders)
        if total_orders % DISCOUNT_ORDER_FREQUENCY != 0:
            return jsonify({
                "error": f"Discount code can only be generated every {DISCOUNT_ORDER_FREQUENCY} orders. Current orders: {total_orders}"
            }), 400
        
        # Check if there's already an unused discount code
        if discount_service.has_unused_discount_code():
            return jsonify({
                "error": "There is already an unused discount code available"
            }), 400
        
        discount_code = discount_service.generate_discount_code()
        
        logger.info(f"Admin generated discount code: {discount_code.code}")
        
        return jsonify({
            "message": "Discount code generated successfully",
            "discount_code": discount_code.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Error generating discount code: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/admin/stats', methods=['GET'])
def get_admin_stats():
    """
    Admin endpoint to get store statistics
    """
    try:
        stats = admin_service.get_store_statistics()
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Error retrieving admin stats: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/admin/discount-codes', methods=['GET'])
def list_discount_codes():
    """
    Admin endpoint to list all discount codes
    """
    try:
        discount_codes = [dc.to_dict() for dc in store.discount_codes.values()]
        return jsonify({
            "discount_codes": discount_codes,
            "total_count": len(discount_codes)
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing discount codes: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors"""
    return jsonify({"error": "Method not allowed"}), 405


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    # Development server configuration
    app.run(debug=True, host='0.0.0.0', port=5000)