"""
Unit tests for the e-commerce store API
Tests all endpoints and business logic functionality
"""

import unittest
import json
from datetime import datetime, timedelta

from app import app
from models import InMemoryStore, Item, Cart, Order, DiscountCode
from services import CartService, OrderService, DiscountService, AdminService


class EcommerceAPITestCase(unittest.TestCase):
    """Test case for e-commerce API endpoints"""
    
    def setUp(self):
        """Set up test fixtures before each test"""
        app.config['TESTING'] = True
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
        # Reset the store for each test
        from app import store
        store.reset()
    
    def tearDown(self):
        """Clean up after each test"""
        self.app_context.pop()
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('timestamp', data)
    
    def test_add_item_to_cart_success(self):
        """Test successfully adding item to cart"""
        item_data = {
            'item_id': 'item1',
            'name': 'Test Product',
            'price': 29.99,
            'quantity': 2
        }
        
        response = self.app.post('/cart/user1/items', 
                                json=item_data,
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Item added to cart successfully')
        self.assertIn('cart', data)
        self.assertEqual(data['cart']['user_id'], 'user1')
        self.assertEqual(len(data['cart']['items']), 1)
        self.assertEqual(data['cart']['total_amount'], 59.98)
    
    def test_add_item_to_cart_validation_error(self):
        """Test adding item with invalid data"""
        item_data = {
            'item_id': 'item1',
            'name': '',  # Empty name should fail
            'price': 29.99,
            'quantity': 2
        }
        
        response = self.app.post('/cart/user1/items',
                                json=item_data,
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_add_item_missing_fields(self):
        """Test adding item with missing required fields"""
        item_data = {
            'item_id': 'item1',
            'price': 29.99
            # Missing name and quantity
        }
        
        response = self.app.post('/cart/user1/items',
                                json=item_data,
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
    
    def test_get_empty_cart(self):
        """Test getting empty cart"""
        response = self.app.get('/cart/user1')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['user_id'], 'user1')
        self.assertEqual(len(data['items']), 0)
        self.assertEqual(data['total_amount'], 0)
    
    def test_checkout_empty_cart(self):
        """Test checkout with empty cart"""
        response = self.app.post('/cart/user1/checkout',
                                json={},
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Cart is empty')
    
    def test_checkout_success(self):
        """Test successful checkout"""
        # First add items to cart
        item_data = {
            'item_id': 'item1',
            'name': 'Test Product',
            'price': 29.99,
            'quantity': 2
        }
        
        self.app.post('/cart/user1/items',
                     json=item_data,
                     content_type='application/json')
        
        # Then checkout
        response = self.app.post('/cart/user1/checkout',
                                json={},
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Order placed successfully')
        self.assertIn('order', data)
        self.assertEqual(data['order']['user_id'], 'user1')
        self.assertEqual(data['order']['total_amount'], 59.98)
    
    def test_checkout_with_invalid_discount_code(self):
        """Test checkout with invalid discount code"""
        # Add items to cart
        item_data = {
            'item_id': 'item1',
            'name': 'Test Product',
            'price': 100.0,
            'quantity': 1
        }
        
        self.app.post('/cart/user1/items',
                     json=item_data,
                     content_type='application/json')
        
        # Checkout with invalid discount code
        response = self.app.post('/cart/user1/checkout',
                                json={'discount_code': 'INVALID'},
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Invalid or expired discount code')
    
    def test_discount_code_generation_after_nth_order(self):
        """Test discount code generation after every 3rd order"""
        from app import store, discount_service
        
        # Create 3 orders to trigger discount code generation
        for i in range(3):
            user_id = f'user{i+1}'
            
            # Add item to cart
            item_data = {
                'item_id': f'item{i+1}',
                'name': f'Product {i+1}',
                'price': 50.0,
                'quantity': 1
            }
            
            self.app.post(f'/cart/{user_id}/items',
                         json=item_data,
                         content_type='application/json')
            
            # Checkout
            self.app.post(f'/cart/{user_id}/checkout',
                         json={},
                         content_type='application/json')
        
        # After 3 orders, there should be a discount code
        discount_codes = store.get_unused_discount_codes()
        self.assertEqual(len(discount_codes), 1)
    
    def test_checkout_with_valid_discount_code(self):
        """Test checkout with valid discount code"""
        from app import store, discount_service
        
        # Generate a discount code
        discount_code = discount_service.generate_discount_code()
        
        # Add items to cart
        item_data = {
            'item_id': 'item1',
            'name': 'Test Product',
            'price': 100.0,
            'quantity': 1
        }
        
        self.app.post('/cart/user1/items',
                     json=item_data,
                     content_type='application/json')
        
        # Checkout with valid discount code
        response = self.app.post('/cart/user1/checkout',
                                json={'discount_code': discount_code.code},
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        
        data = json.loads(response.data)
        order = data['order']
        self.assertEqual(order['discount_code'], discount_code.code)
        self.assertEqual(order['discount_amount'], 10.0)  # 10% of 100
        self.assertEqual(order['total_amount'], 90.0)
        
        # Discount code should now be used
        updated_discount = store.get_discount_code(discount_code.code)
        self.assertTrue(updated_discount.is_used)
    
    def test_admin_generate_discount_code_success(self):
        """Test admin discount code generation"""
        from app import store
        
        # Create 3 orders first to meet the condition
        for i in range(3):
            user_id = f'user{i+1}'
            item_data = {
                'item_id': f'item{i+1}',
                'name': f'Product {i+1}',
                'price': 50.0,
                'quantity': 1
            }
            
            self.app.post(f'/cart/{user_id}/items', json=item_data)
            self.app.post(f'/cart/{user_id}/checkout', json={})
        
        # Clear existing discount codes generated automatically
        store.discount_codes.clear()
        
        # Now admin can generate a discount code
        response = self.app.post('/admin/discount-codes')
        
        self.assertEqual(response.status_code, 201)
        
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Discount code generated successfully')
        self.assertIn('discount_code', data)
    
    def test_admin_generate_discount_code_failure(self):
        """Test admin discount code generation when condition not met"""
        # Try to generate without meeting the nth order condition
        response = self.app.post('/admin/discount-codes')
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_admin_stats(self):
        """Test admin statistics endpoint"""
        from app import store, discount_service
        
        # Create some test data
        # Add item and checkout
        item_data = {
            'item_id': 'item1',
            'name': 'Test Product',
            'price': 100.0,
            'quantity': 2
        }
        
        self.app.post('/cart/user1/items', json=item_data)
        self.app.post('/cart/user1/checkout', json={})
        
        # Generate a discount code
        discount_service.generate_discount_code()
        
        response = self.app.get('/admin/stats')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('orders', data)
        self.assertIn('discounts', data)
        self.assertIn('revenue', data)
        
        self.assertEqual(data['orders']['total_orders'], 1)
        self.assertEqual(data['orders']['total_items_purchased'], 2)
        self.assertEqual(data['orders']['total_purchase_amount'], 200.0)
    
    def test_list_discount_codes(self):
        """Test listing discount codes"""
        from app import discount_service
        
        # Generate some discount codes
        discount_service.generate_discount_code()
        discount_service.generate_discount_code()
        
        response = self.app.get('/admin/discount-codes')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('discount_codes', data)
        self.assertIn('total_count', data)
        self.assertEqual(data['total_count'], 2)
    
    def test_404_error_handling(self):
        """Test 404 error handling"""
        response = self.app.get('/nonexistent-endpoint')
        
        self.assertEqual(response.status_code, 404)
        
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Endpoint not found')
    
    def test_method_not_allowed(self):
        """Test 405 error handling"""
        response = self.app.put('/cart/user1')
        
        self.assertEqual(response.status_code, 405)
        
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Method not allowed')


class ModelsTestCase(unittest.TestCase):
    """Test case for data models"""
    
    def test_item_creation(self):
        """Test item creation and validation"""
        item = Item(item_id='1', name='Test', price=10.0, quantity=2)
        self.assertEqual(item.item_id, '1')
        self.assertEqual(item.name, 'Test')
        self.assertEqual(item.price, 10.0)
        self.assertEqual(item.quantity, 2)
    
    def test_item_negative_price(self):
        """Test item with negative price raises error"""
        with self.assertRaises(ValueError):
            Item(item_id='1', name='Test', price=-10.0, quantity=2)
    
    def test_item_zero_quantity(self):
        """Test item with zero quantity raises error"""
        with self.assertRaises(ValueError):
            Item(item_id='1', name='Test', price=10.0, quantity=0)
    
    def test_cart_add_item(self):
        """Test adding item to cart"""
        cart = Cart(user_id='user1')
        item = Item(item_id='1', name='Test', price=10.0, quantity=2)
        
        cart.add_item(item)
        
        self.assertEqual(len(cart.items), 1)
        self.assertEqual(cart.get_total(), 20.0)
        self.assertEqual(cart.get_item_count(), 2)
    
    def test_cart_add_same_item_twice(self):
        """Test adding same item twice combines quantities"""
        cart = Cart(user_id='user1')
        item1 = Item(item_id='1', name='Test', price=10.0, quantity=2)
        item2 = Item(item_id='1', name='Test', price=10.0, quantity=3)
        
        cart.add_item(item1)
        cart.add_item(item2)
        
        self.assertEqual(len(cart.items), 1)
        self.assertEqual(cart.items[0].quantity, 5)
        self.assertEqual(cart.get_total(), 50.0)
    
    def test_discount_code_validation(self):
        """Test discount code validation"""
        discount_code = DiscountCode(code='TEST10', discount_percentage=10.0)
        
        self.assertTrue(discount_code.is_valid())
        self.assertFalse(discount_code.is_used)
        
        discount_code.use()
        
        self.assertFalse(discount_code.is_valid())
        self.assertTrue(discount_code.is_used)
    
    def test_discount_code_expiry(self):
        """Test discount code expiry"""
        past_date = datetime.utcnow() - timedelta(days=1)
        discount_code = DiscountCode(
            code='EXPIRED',
            discount_percentage=10.0,
            expires_at=past_date
        )
        
        self.assertFalse(discount_code.is_valid())
    
    def test_order_creation(self):
        """Test order creation"""
        items = [Item(item_id='1', name='Test', price=10.0, quantity=2)]
        order = Order(
            order_id='order1',
            user_id='user1',
            items=items,
            subtotal=20.0,
            discount_amount=2.0
        )
        
        self.assertEqual(order.total_amount, 18.0)


class ServicesTestCase(unittest.TestCase):
    """Test case for service layer"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.store = InMemoryStore()
        self.cart_service = CartService(self.store)
        self.order_service = OrderService(self.store)
        self.discount_service = DiscountService(self.store)
        self.admin_service = AdminService(self.store)
    
    def test_cart_service_add_item(self):
        """Test cart service add item functionality"""
        item = Item(item_id='1', name='Test', price=10.0, quantity=2)
        cart = self.cart_service.add_item_to_cart('user1', item)
        
        self.assertEqual(cart.user_id, 'user1')
        self.assertEqual(len(cart.items), 1)
        self.assertEqual(cart.get_total(), 20.0)
    
    def test_order_service_create_order(self):
        """Test order service create order functionality"""
        # Create cart with items
        cart = Cart(user_id='user1')
        item = Item(item_id='1', name='Test', price=100.0, quantity=1)
        cart.add_item(item)
        
        # Create order
        order = self.order_service.create_order(cart)
        
        self.assertEqual(order.user_id, 'user1')
        self.assertEqual(order.subtotal, 100.0)
        self.assertEqual(order.total_amount, 100.0)
        self.assertEqual(len(order.items), 1)
    
    def test_order_service_create_order_with_discount(self):
        """Test creating order with discount code"""
        # Generate discount code
        discount_code = self.discount_service.generate_discount_code()
        
        # Create cart with items
        cart = Cart(user_id='user1')
        item = Item(item_id='1', name='Test', price=100.0, quantity=1)
        cart.add_item(item)
        
        # Create order with discount
        order = self.order_service.create_order(cart, discount_code.code)
        
        self.assertEqual(order.discount_amount, 10.0)
        self.assertEqual(order.total_amount, 90.0)
        self.assertEqual(order.discount_code, discount_code.code)
    
    def test_discount_service_generate_code(self):
        """Test discount service generate code functionality"""
        discount_code = self.discount_service.generate_discount_code()
        
        self.assertIsNotNone(discount_code.code)
        self.assertEqual(discount_code.discount_percentage, 10.0)
        self.assertTrue(discount_code.is_valid())
    
    def test_discount_service_use_code(self):
        """Test using discount code"""
        discount_code = self.discount_service.generate_discount_code()
        
        self.assertTrue(self.discount_service.is_discount_code_valid(discount_code.code))
        
        self.discount_service.use_discount_code(discount_code.code)
        
        self.assertFalse(self.discount_service.is_discount_code_valid(discount_code.code))
    
    def test_admin_service_statistics(self):
        """Test admin service statistics"""
        # Create some test data
        cart = Cart(user_id='user1')
        item = Item(item_id='1', name='Test', price=100.0, quantity=2)
        cart.add_item(item)
        
        order = self.order_service.create_order(cart)
        discount_code = self.discount_service.generate_discount_code()
        
        stats = self.admin_service.get_store_statistics()
        
        self.assertEqual(stats['orders']['total_orders'], 1)
        self.assertEqual(stats['orders']['total_items_purchased'], 2)
        self.assertEqual(stats['orders']['total_purchase_amount'], 200.0)
        self.assertEqual(stats['discounts']['total_discount_codes'], 1)


if __name__ == '__main__':
    unittest.main()