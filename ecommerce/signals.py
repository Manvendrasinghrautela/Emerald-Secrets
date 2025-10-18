from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Cart, Order, OrderItem, Product
from useraccounts.models import UserProfile

@receiver(post_save, sender=User)
def create_user_cart(sender, instance, created, **kwargs):
    """Create a cart for new users"""
    if created:
        Cart.objects.get_or_create(user=instance)

@receiver(post_save, sender=Order)
def update_product_stock(sender, instance, created, **kwargs):
    """Update product stock when order is created"""
    if created:
        for item in instance.items.all():
            product = item.product
            if product.stock >= item.quantity:
                product.stock -= item.quantity
                product.save()

@receiver(pre_save, sender=Product)
def generate_product_slug(sender, instance, **kwargs):
    """Generate slug from name if not provided"""
    if not instance.slug and instance.name:
        from django.utils.text import slugify
        base_slug = slugify(instance.name)
        slug = base_slug
        counter = 1
        
        while Product.objects.filter(slug=slug).exclude(pk=instance.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        instance.slug = slug

@receiver(post_save, sender=OrderItem)
def send_order_confirmation_email(sender, instance, created, **kwargs):
    """Send order confirmation email when order item is created"""
    if created:
        from django.core.mail import send_mail
        from django.conf import settings
        
        order = instance.order
        
        # Send email to customer
        subject = f'Order Confirmation - {order.order_number}'
        message = f'''
        Dear {order.shipping_name},
        
        Thank you for your order from Emerald Secrets!
        
        Order Number: {order.order_number}
        Total Amount: ₹{order.total_amount}
        
        We will process your order and send you tracking information soon.
        
        Best regards,
        Emerald Secrets Team
        '''
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [order.shipping_email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Failed to send email: {e}")
