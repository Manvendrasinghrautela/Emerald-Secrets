from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in, user_logged_out
from .models import UserProfile, Wishlist, UserActivity, UserPreferences
from ecommerce.models import Cart

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a user profile when a new user is created"""
    if created:
        UserProfile.objects.create(user=instance)
        print(f"Created profile for user: {instance.username}")

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save the user profile when the user is updated"""
    try:
        instance.profile.save()
    except UserProfile.DoesNotExist:
        # Create profile if it doesn't exist
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def create_user_wishlist(sender, instance, created, **kwargs):
    """Create a wishlist for new users"""
    if created:
        Wishlist.objects.create(user=instance)
        print(f"Created wishlist for user: {instance.username}")

@receiver(post_save, sender=User)
def create_user_preferences(sender, instance, created, **kwargs):
    """Create user preferences for new users"""
    if created:
        UserPreferences.objects.create(user=instance)
        print(f"Created preferences for user: {instance.username}")

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log user login activity"""
    try:
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        UserActivity.objects.create(
            user=user,
            activity_type='login',
            description=f'User logged in from {ip_address}',
            ip_address=ip_address,
            user_agent=user_agent
        )
    except Exception as e:
        print(f"Error logging user login: {e}")

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Log user logout activity"""
    if user:
        try:
            ip_address = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            UserActivity.objects.create(
                user=user,
                activity_type='logout',
                description=f'User logged out from {ip_address}',
                ip_address=ip_address,
                user_agent=user_agent
            )
        except Exception as e:
            print(f"Error logging user logout: {e}")

@receiver(post_delete, sender=User)
def cleanup_user_data(sender, instance, **kwargs):
    """Clean up user-related data when user is deleted"""
    try:
        # Delete profile image if it's not the default
        if hasattr(instance, 'profile') and instance.profile.profile_image:
            if instance.profile.profile_image.name != 'profiles/default.jpg':
                instance.profile.profile_image.delete(save=False)
        print(f"Cleaned up data for deleted user: {instance.username}")
    except Exception as e:
        print(f"Error cleaning up user data: {e}")

def get_client_ip(request):
    """Get the client's IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

# Signal for tracking specific user activities
def log_user_activity(user, activity_type, description="", request=None):
    """Helper function to log user activities"""
    try:
        ip_address = None
        user_agent = ""
        
        if request:
            ip_address = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        UserActivity.objects.create(
            user=user,
            activity_type=activity_type,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent
        )
    except Exception as e:
        print(f"Error logging user activity: {e}")

# You can call this function from views like:
# from useraccounts.signals import log_user_activity
# log_user_activity(request.user, 'product_view', f'Viewed product: {product.name}', request)
