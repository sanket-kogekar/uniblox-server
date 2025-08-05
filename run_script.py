#!/usr/bin/env python3
"""
Development server runner for the e-commerce store API
Provides a convenient way to run the application with different configurations
"""

import os
import sys
import argparse
from app import app
from config import get_config


def run_server(host='0.0.0.0', port=5000, debug=True, env='development'):
    """
    Run the Flask development server
    
    Args:
        host: Host to bind to
        port: Port to bind to  
        debug: Enable debug mode
        env: Environment (development, production, testing)
    """
    # Set environment
    os.environ['FLASK_ENV'] = env
    
    # Configure app
    config_class = get_config()
    app.config.from_object(config_class)
    
    print(f"Starting e-commerce API server...")
    print(f"Environment: {env}")
    print(f"Debug mode: {debug}")
    print(f"Server: http://{host}:{port}")
    print(f"Health check: http://{host}:{port}/health")
    print(f"API Documentation: See README.md")
    print("-" * 50)
    
    # Run the server
    app.run(host=host, port=port, debug=debug)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Run the e-commerce store API server')
    
    parser.add_argument('--host', 
                       default='0.0.0.0',
                       help='Host to bind to (default: 0.0.0.0)')
    
    parser.add_argument('--port', 
                       type=int, 
                       default=5000,
                       help='Port to bind to (default: 5000)')
    
    parser.add_argument('--env',
                       choices=['development', 'production', 'testing'],
                       default='development',
                       help='Environment to run in (default: development)')
    
    parser.add_argument('--no-debug',
                       action='store_true',
                       help='Disable debug mode')
    
    parser.add_argument('--test',
                       action='store_true',
                       help='Run in testing mode with test data')
    
    args = parser.parse_args()
    
    # Determine debug mode
    debug = not args.no_debug and args.env == 'development'
    
    # Set testing environment if requested
    if args.test:
        args.env = 'testing'
        print("Running in testing mode...")
        
        # Load some test data
        from models import Item
        from services import CartService, OrderService, DiscountService
        from app import store
        
        cart_service = CartService(store)
        order_service = OrderService(store)
        discount_service = DiscountService(store)
        
        # Add some sample data
        print("Loading test data...")
        
        # Sample items for different users
        test_items = [
            ("testuser1", Item("laptop001", "Gaming Laptop", 999.99, 1)),
            ("testuser1", Item("mouse001", "Gaming Mouse", 79.99, 1)),
            ("testuser2", Item("phone001", "Smartphone", 699.99, 1)),
            ("testuser2", Item("case001", "Phone Case", 29.99, 2)),
        ]
        
        for user_id, item in test_items:
            cart_service.add_item_to_cart(user_id, item)
        
        # Create some orders to demonstrate discount code generation
        for i in range(2):
            user_id = f"testuser{i+1}"
            cart = cart_service.get_cart(user_id)
            if cart.items:
                order_service.create_order(cart)
                cart_service.clear_cart(user_id)
        
        print("Test data loaded successfully!")
        print("Try these test users: testuser1, testuser2")
    
    try:
        run_server(
            host=args.host,
            port=args.port,
            debug=debug,
            env=args.env
        )
    except KeyboardInterrupt:
        print("\nShutting down server...")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()