from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from .models import Category, Product, Cart, CartItem, Order, OrderItem, Review
from useraccounts.models import UserProfile

class CategoryModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category',
            description='A test category'
        )
    
    def test_category_creation(self):
        self.assertEqual(self.category.name, 'Test Category')
        self.assertEqual(self.category.slug, 'test-category')
        self.assertEqual(str(self.category), 'Test Category')
    
    def test_category_absolute_url(self):
        url = self.category.get_absolute_url()
        self.assertEqual(url, reverse('category_products', kwargs={'slug': 'test-category'}))

class ProductModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='A test product',
            category=self.category,
            price=Decimal('100.00'),
            compare_price=Decimal('120.00'),
            stock=10
        )
    
    def test_product_creation(self):
        self.assertEqual(self.product.name, 'Test Product')
        self.assertEqual(self.product.price, Decimal('100.00'))
        self.assertEqual(str(self.product), 'Test Product')
    
    def test_discount_percentage(self):
        discount = self.product.discount_percentage
        self.assertEqual(discount, 17)  # (120-100)/120 * 100 = 16.67 rounded to 17
    
    def test_product_absolute_url(self):
        url = self.product.get_absolute_url()
        self.assertEqual(url, reverse('product_detail', kwargs={'slug': 'test-product'}))

class CartModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='A test product',
            category=self.category,
            price=Decimal('100.00'),
            stock=10
        )
        self.cart = Cart.objects.create(user=self.user)
        self.cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2
        )
    
    def test_cart_creation(self):
        self.assertEqual(str(self.cart), f"Cart for {self.user.username}")
    
    def test_cart_total_price(self):
        self.assertEqual(self.cart.total_price, Decimal('200.00'))
    
    def test_cart_total_items(self):
        self.assertEqual(self.cart.total_items, 2)
    
    def test_cart_item_total_price(self):
        self.assertEqual(self.cart_item.total_price, Decimal('200.00'))

class OrderModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.order = Order.objects.create(
            user=self.user,
            total_amount=Decimal('100.00'),
            shipping_name='Test User',
            shipping_email='test@example.com',
            shipping_phone='1234567890',
            shipping_address='Test Address',
            shipping_city='Test City',
            shipping_state='Test State',
            shipping_pincode='123456'
        )
    
    def test_order_creation(self):
        self.assertEqual(self.order.user, self.user)
        self.assertEqual(self.order.total_amount, Decimal('100.00'))
        self.assertTrue(self.order.order_number.startswith('ES'))
    
    def test_order_string_representation(self):
        expected = f"Order {self.order.order_number}"
        self.assertEqual(str(self.order), expected)

class ReviewModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='A test product',
            category=self.category,
            price=Decimal('100.00'),
            stock=10
        )
        self.review = Review.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            comment='Great product!'
        )
    
    def test_review_creation(self):
        self.assertEqual(self.review.rating, 5)
        self.assertEqual(self.review.comment, 'Great product!')
        expected = f"{self.user.username} - {self.product.name} (5 stars)"
        self.assertEqual(str(self.review), expected)

class ViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='A test product',
            category=self.category,
            price=Decimal('100.00'),
            stock=10,
            is_active=True,
            is_featured=True
        )
    
    def test_home_view(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Emerald Secrets')
        self.assertIn('featured_products', response.context)
    
    def test_shop_view(self):
        response = self.client.get(reverse('shop'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Product')
    
    def test_product_detail_view(self):
        response = self.client.get(
            reverse('product_detail', kwargs={'slug': 'test-product'})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Product')
        self.assertEqual(response.context['product'], self.product)
    
    def test_cart_view_authenticated(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('cart'))
        self.assertEqual(response.status_code, 200)
    
    def test_cart_view_unauthenticated(self):
        response = self.client.get(reverse('cart'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_add_to_cart_authenticated(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('add_to_cart', kwargs={'product_id': self.product.id})
        )
        self.assertEqual(response.status_code, 302)  # Redirect to cart
        
        # Check if cart item was created
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.items.count(), 1)
    
    def test_search_functionality(self):
        response = self.client.get(reverse('shop'), {'search': 'Test'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Product')
    
    def test_category_filter(self):
        response = self.client.get(
            reverse('shop'), 
            {'category': 'test-category'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Product')

class SignalTest(TestCase):
    def test_cart_creation_on_user_signup(self):
        # Create user
        user = User.objects.create_user(
            username='newuser',
            email='newuser@example.com',
            password='testpass123'
        )
        
        # Check if cart was created automatically
        self.assertTrue(Cart.objects.filter(user=user).exists())
    
    def test_product_slug_generation(self):
        category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        # Create product without slug
        product = Product.objects.create(
            name='Test Product Name',
            description='A test product',
            category=category,
            price=Decimal('100.00'),
            stock=10
        )
        
        self.assertEqual(product.slug, 'test-product-name')

class IntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Skincare',
            slug='skincare'
        )
        self.product = Product.objects.create(
            name='Rose Water',
            slug='rose-water',
            description='Pure rose water',
            category=self.category,
            price=Decimal('299.00'),
            stock=50,
            is_active=True
        )
    
    def test_complete_shopping_flow(self):
        # 1. User visits homepage
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        
        # 2. User browses shop
        response = self.client.get(reverse('shop'))
        self.assertEqual(response.status_code, 200)
        
        # 3. User views product detail
        response = self.client.get(
            reverse('product_detail', kwargs={'slug': 'rose-water'})
        )
        self.assertEqual(response.status_code, 200)
        
        # 4. User logs in
        self.client.login(username='testuser', password='testpass123')
        
        # 5. User adds product to cart
        response = self.client.get(
            reverse('add_to_cart', kwargs={'product_id': self.product.id})
        )
        self.assertEqual(response.status_code, 302)
        
        # 6. User views cart
        response = self.client.get(reverse('cart'))
        self.assertEqual(response.status_code, 200)
        
        # Verify cart has product
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.items.count(), 1)
        self.assertEqual(cart.total_price, Decimal('299.00'))
