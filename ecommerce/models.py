from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from PIL import Image
from django.utils import timezone
import uuid


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category_products', kwargs={'slug': self.slug})


class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    image = models.ImageField(upload_to='products/')
    image2 = models.ImageField(upload_to='products/', blank=True, null=True)
    image3 = models.ImageField(upload_to='products/', blank=True, null=True)
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    weight = models.CharField(max_length=50, blank=True)
    ingredients = models.TextField(blank=True)
    how_to_use = models.TextField(blank=True)
    benefits = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('product_detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.image:
            img = Image.open(self.image.path)
            if img.height > 800 or img.width > 800:
                output_size = (800, 800)
                img.thumbnail(output_size)
                img.save(self.image.path)

    @property
    def discount_percentage(self):
        if self.compare_price and self.compare_price > self.price:
            return round(((self.compare_price - self.price) / self.compare_price) * 100)
        return 0


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlists')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.user.username}'s wishlist: {self.product.name}"


class Newsletter(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    unsubscribe_token = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.email


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user.username}"

    @property
    def total_price(self):
        total = 0
        for item in self.items.all():
            total += item.product.price * item.quantity
        return total

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'product')

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    @property
    def total_price(self):
        return self.quantity * self.product.price


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=20, unique=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    affiliate_code = models.CharField(max_length=20, blank=True, null=True)
    shipping_name = models.CharField(max_length=100)
    shipping_email = models.EmailField()
    shipping_phone = models.CharField(max_length=20)
    shipping_address = models.TextField()
    shipping_city = models.CharField(max_length=100)
    shipping_state = models.CharField(max_length=100)
    shipping_pincode = models.CharField(max_length=10)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.order_number}"

    def calculate_total(self):
        """Calculate total order amount from order items"""
        if self.pk:  # Only calculate if order exists in database
            return sum(item.total_price for item in self.items.all())
        return 0

    def save(self, *args, **kwargs):
        """Override save to auto-calculate total_amount"""
        # Save first to ensure order has a primary key
        super().save(*args, **kwargs)
        # Then calculate and update total_amount
        calculated_total = self.calculate_total()
        if self.total_amount != calculated_total:
            self.total_amount = calculated_total
            # Use update to avoid recursion
            Order.objects.filter(pk=self.pk).update(total_amount=calculated_total)

    

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    @property
    def total_price(self):
        """Calculate total price for this order item"""
        if self.price is not None and self.quantity is not None:
            return self.price * self.quantity
        elif self.product and self.product.price and self.quantity is not None:
            # Fallback to product price if item price is not set
            return self.product.price * self.quantity
        return 0

    def save(self, *args, **kwargs):
        """Auto-set price from product if not provided"""
        if not self.price and self.product:
            self.price = self.product.price
        super().save(*args, **kwargs)
        # Update order total after saving order item
        if self.order:
            self.order.save()


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating} stars)"


class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=20, choices=[('percentage', 'Percentage'), ('fixed', 'Fixed Amount')])
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    min_purchase = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    usage_limit = models.IntegerField(null=True, blank=True)
    used_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.code


class AffiliateProfile(models.Model):
    """Affiliate user profile"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='affiliate_profile')
    affiliate_code = models.CharField(max_length=20, unique=True, editable=False)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)  # 5%
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pending_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    withdrawn_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Bank details for payouts
    bank_account_name = models.CharField(max_length=100, blank=True)
    bank_account_number = models.CharField(max_length=50, blank=True)
    bank_ifsc_code = models.CharField(max_length=20, blank=True)
    upi_id = models.CharField(max_length=100, blank=True)

    is_approved = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Affiliate Profile'
        verbose_name_plural = 'Affiliate Profiles'

    def __str__(self):
        return f"{self.user.username} - {self.affiliate_code}"

    def save(self, *args, **kwargs):
        if not self.affiliate_code:
            self.affiliate_code = self.generate_affiliate_code()
        super().save(*args, **kwargs)

    def generate_affiliate_code(self):
        """Generate unique affiliate code"""
        return f"AFF{uuid.uuid4().hex[:8].upper()}"

    def get_affiliate_link(self, product_id=None):
        """Generate affiliate link"""
        from django.conf import settings
        base_url = settings.SITE_URL
        if product_id:
            return f"{base_url}/shop/product/{product_id}/?ref={self.affiliate_code}"
        return f"{base_url}/shop/?ref={self.affiliate_code}"


class AffiliateClick(models.Model):
    """Track clicks on affiliate links"""
    affiliate = models.ForeignKey(AffiliateProfile, on_delete=models.CASCADE, related_name='clicks')
    product = models.ForeignKey('Product', on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    referrer = models.URLField(blank=True)
    clicked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Affiliate Click'
        verbose_name_plural = 'Affiliate Clicks'

    def __str__(self):
        return f"{self.affiliate.affiliate_code} - {self.clicked_at}"


class AffiliateReferral(models.Model):
    """Track successful referrals and commissions"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('rejected', 'Rejected'),
    ]

    affiliate = models.ForeignKey(AffiliateProfile, on_delete=models.CASCADE, related_name='referrals')
    order = models.OneToOneField('Order', on_delete=models.CASCADE, related_name='affiliate_referral')
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Affiliate Referral'
        verbose_name_plural = 'Affiliate Referrals'

    def __str__(self):
        return f"{self.affiliate.affiliate_code} - Order #{self.order.order_number}"

    def approve(self):
        """Approve referral and update affiliate earnings"""
        if self.status == 'pending':
            self.status = 'approved'
            self.approved_at = timezone.now()
            self.affiliate.pending_earnings += self.commission_amount
            self.affiliate.total_earnings += self.commission_amount
            self.affiliate.save()
            self.save()

    def mark_as_paid(self):
        """Mark commission as paid"""
        if self.status == 'approved':
            self.status = 'paid'
            self.paid_at = timezone.now()
            self.affiliate.pending_earnings -= self.commission_amount
            self.affiliate.withdrawn_earnings += self.commission_amount
            self.affiliate.save()
            self.save()


class AffiliateWithdrawal(models.Model):
    """Track withdrawal requests"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]

    affiliate = models.ForeignKey(AffiliateProfile, on_delete=models.CASCADE, related_name='withdrawals')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=[('bank', 'Bank Transfer'), ('upi', 'UPI')])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Affiliate Withdrawal'
        verbose_name_plural = 'Affiliate Withdrawals'

    def __str__(self):
        return f"{self.affiliate.affiliate_code} - ₹{self.amount}"
