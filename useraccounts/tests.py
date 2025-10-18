from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core import mail
import tempfile
from PIL import Image
from .models import UserProfile, Wishlist, Address, NewsletterSubscription, UserActivity, UserPreferences
from .forms import UserRegistrationForm, UserProfileForm, ContactForm
from ecommerce.models import Category, Product, Order

class UserProfileModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
    
    def test_profile_creation(self):
        """Test that profile is created automatically when user is created"""
        self.assertTrue(UserProfile.objects.filter(user=self.user).exists())
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(str(profile), "testuser's Profile")
    
    def test_profile_fields(self):
        """Test profile field functionality"""
        profile = self.user.profile
        profile.phone = '+919876543210'
        profile.city = 'Mumbai'
        profile.state = 'Maharashtra'
        profile.pincode = '400001'
        profile.address_line1 = 'Test Address'
        profile.save()
        
        self.assertEqual(profile.phone, '+919876543210')
        self.assertEqual(profile.city, 'Mumbai')
        self.assertEqual(profile.pincode, '400001')
    
    def test_get_full_address(self):
        """Test the get_full_address property"""
        profile = self.user.profile
        profile.address_line1 = '123 Main St'
        profile.city = 'Mumbai'
        profile.state = 'Maharashtra'
        profile.pincode = '400001'
        profile.country = 'India'
        profile.save()
        
        expected_address = '123 Main St, Mumbai, Maharashtra, 400001, India'
        self.assertEqual(profile.get_full_address, expected_address)

class WishlistModelTest(TestCase):
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
            price=100.00,
            stock=10
        )
    
    def test_wishlist_creation(self):
        """Test that wishlist is created automatically"""
        self.assertTrue(Wishlist.objects.filter(user=self.user).exists())
        wishlist = Wishlist.objects.get(user=self.user)
        self.assertEqual(str(wishlist), "testuser's Wishlist")
    
    def test_wishlist_add_product(self):
        """Test adding product to wishlist"""
        wishlist = self.user.wishlist
        wishlist.products.add(self.product)
        
        self.assertEqual(wishlist.product_count, 1)
        self.assertTrue(wishlist.products.filter(id=self.product.id).exists())

class AddressModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_address_creation(self):
        """Test address creation"""
        address = Address.objects.create(
            user=self.user,
            name='Home',
            address_line1='123 Main St',
            city='Mumbai',
            state='Maharashtra',
            pincode='400001',
            is_default=True
        )
        
        self.assertEqual(str(address), 'Home - testuser')
        self.assertTrue(address.is_default)
    
    def test_default_address_logic(self):
        """Test that only one address can be default"""
        # Create first address as default
        address1 = Address.objects.create(
            user=self.user,
            name='Home',
            address_line1='123 Main St',
            city='Mumbai',
            state='Maharashtra',
            pincode='400001',
            is_default=True
        )
        
        # Create second address as default
        address2 = Address.objects.create(
            user=self.user,
            name='Work',
            address_line1='456 Work St',
            city='Delhi',
            state='Delhi',
            pincode='110001',
            is_default=True
        )
        
        # Refresh from database
        address1.refresh_from_db()
        
        # First address should no longer be default
        self.assertFalse(address1.is_default)
        self.assertTrue(address2.is_default)

class UserRegistrationFormTest(TestCase):
    def test_valid_registration_form(self):
        """Test valid registration form"""
        form_data = {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'newuser@example.com',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_duplicate_email_registration(self):
        """Test that duplicate email is rejected"""
        # Create existing user
        User.objects.create_user(
            username='existing',
            email='existing@example.com',
            password='testpass123'
        )
        
        form_data = {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'existing@example.com',  # Duplicate email
            'password1': 'complexpassword123',
            'password2': 'complexpassword123'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

class ViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_signup_view_get(self):
        """Test signup view GET request"""
        response = self.client.get(reverse('signup'))
        self.assertEqual(response.status_code, 200)
    
    def test_signup_view_post_valid(self):
        """Test signup view POST with valid data"""
        form_data = {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'newuser@example.com',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123'
        }
        response = self.client.post(reverse('signup'), data=form_data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful signup
        
        # Check that user was created
        self.assertTrue(User.objects.filter(username='newuser').exists())
    
    def test_profile_view_authenticated(self):
        """Test profile view for authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
    
    def test_profile_view_unauthenticated(self):
        """Test profile view for unauthenticated user"""
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

class IntegrationTest(TestCase):
    def test_complete_user_registration_flow(self):
        """Test complete user registration and profile setup flow"""
        # 1. User visits signup page
        response = self.client.get(reverse('signup'))
        self.assertEqual(response.status_code, 200)
        
        # 2. User submits registration form
        form_data = {
            'username': 'integrationuser',
            'first_name': 'Integration',
            'last_name': 'User',
            'email': 'integration@example.com',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123'
        }
        response = self.client.post(reverse('signup'), data=form_data)
        self.assertEqual(response.status_code, 302)
        
        # 3. Check user was created with profile
        user = User.objects.get(username='integrationuser')
        self.assertTrue(hasattr(user, 'profile'))
        self.assertTrue(hasattr(user, 'wishlist'))
        
        # 4. User logs in
        login_success = self.client.login(username='integrationuser', password='complexpassword123')
        self.assertTrue(login_success)
        
        # 5. User visits profile page
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
