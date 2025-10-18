from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
import json
import csv

from .forms import (
    UserRegistrationForm, UserProfileForm, ContactForm, 
    PasswordChangeForm, NewsletterSubscriptionForm
)
from .models import (
    UserProfile, Address, Wishlist, NewsletterSubscription, 
    UserActivity, UserPreferences
)
from ecommerce.models import Product, Order

def signup(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Log user activity
            log_user_activity(user, 'signup', 'User registered successfully', request)
            
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            
            # Send welcome email
            send_welcome_email(user)
            
            return redirect('login')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'useraccounts/signup.html', {'form': form})

@login_required
def profile_view(request):
    """User profile dashboard"""
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    # Get user's orders
    orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    # Get user statistics
    total_orders = Order.objects.filter(user=request.user).count()
    total_spent = sum(order.total_amount for order in Order.objects.filter(user=request.user))
    wishlist_count = 0
    if hasattr(request.user, 'wishlist'):
        wishlist_count = request.user.wishlist.products.count()
    
    context = {
        'profile': profile,
        'orders': orders,
        'total_orders': total_orders,
        'total_spent': total_spent,
        'wishlist_count': wishlist_count,
    }
    return render(request, 'useraccounts/profile.html', context)

@login_required
def edit_profile(request):
    """Edit user profile"""
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            # Update user's basic info
            user = request.user
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.save()
            
            # Update profile
            profile = form.save()
            
            # Log activity
            log_user_activity(request.user, 'profile_update', 'Profile updated', request)
            
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile')
    else:
        initial_data = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
        }
        form = UserProfileForm(instance=profile, initial=initial_data)
    
    return render(request, 'useraccounts/edit_profile.html', {'form': form})

@login_required
def change_password(request):
    """Change user password"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Keep user logged in
            
            # Log activity
            log_user_activity(request.user, 'password_change', 'Password changed', request)
            
            messages.success(request, 'Your password has been changed successfully!')
            return redirect('profile')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'useraccounts/change_password.html', {'form': form})

@login_required
def order_list(request):
    """List user's orders"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'useraccounts/order_list.html', {'page_obj': page_obj})

@login_required
def order_detail(request, order_number):
    """Order detail view"""
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, 'useraccounts/order_detail.html', {'order': order})

@login_required
def address_list(request):
    """List user addresses"""
    addresses = Address.objects.filter(user=request.user).order_by('-is_default', '-updated_at')
    return render(request, 'useraccounts/address_list.html', {'addresses': addresses})

@login_required
def add_address(request):
    """Add new address"""
    if request.method == 'POST':
        # Handle form data manually or use a form class
        name = request.POST.get('name')
        address_line1 = request.POST.get('address_line1')
        address_line2 = request.POST.get('address_line2', '')
        city = request.POST.get('city')
        state = request.POST.get('state')
        pincode = request.POST.get('pincode')
        address_type = request.POST.get('type', 'home')
        is_default = request.POST.get('is_default') == 'on'
        
        Address.objects.create(
            user=request.user,
            name=name,
            address_line1=address_line1,
            address_line2=address_line2,
            city=city,
            state=state,
            pincode=pincode,
            type=address_type,
            is_default=is_default
        )
        
        messages.success(request, 'Address added successfully!')
        return redirect('address_list')
    
    return render(request, 'useraccounts/add_address.html')

@login_required
def edit_address(request, address_id):
    """Edit address"""
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    if request.method == 'POST':
        address.name = request.POST.get('name')
        address.address_line1 = request.POST.get('address_line1')
        address.address_line2 = request.POST.get('address_line2', '')
        address.city = request.POST.get('city')
        address.state = request.POST.get('state')
        address.pincode = request.POST.get('pincode')
        address.type = request.POST.get('type', 'home')
        address.is_default = request.POST.get('is_default') == 'on'
        address.save()
        
        messages.success(request, 'Address updated successfully!')
        return redirect('address_list')
    
    return render(request, 'useraccounts/edit_address.html', {'address': address})

@login_required
def delete_address(request, address_id):
    """Delete address"""
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    if request.method == 'POST':
        address.delete()
        messages.success(request, 'Address deleted successfully!')
        return redirect('address_list')
    
    return render(request, 'useraccounts/delete_address.html', {'address': address})

@login_required
def set_default_address(request, address_id):
    """Set default address"""
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    # Remove default from all other addresses
    Address.objects.filter(user=request.user).update(is_default=False)
    
    # Set this address as default
    address.is_default = True
    address.save()
    
    messages.success(request, 'Default address updated!')
    return redirect('address_list')

@login_required
def wishlist_view(request):
    """View user's wishlist"""
    try:
        wishlist = request.user.wishlist
        products = wishlist.products.filter(is_active=True)
    except Wishlist.DoesNotExist:
        wishlist = Wishlist.objects.create(user=request.user)
        products = []
    
    return render(request, 'useraccounts/wishlist.html', {
        'wishlist': wishlist,
        'products': products
    })

@login_required
def add_to_wishlist(request, product_id):
    """Add product to wishlist"""
    product = get_object_or_404(Product, id=product_id)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    
    if product in wishlist.products.all():
        messages.info(request, f'{product.name} is already in your wishlist!')
    else:
        wishlist.products.add(product)
        log_user_activity(request.user, 'wishlist_add', f'Added {product.name} to wishlist', request)
        messages.success(request, f'{product.name} added to wishlist!')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': 'Added to wishlist'})
    
    return redirect('wishlist')

@login_required
def remove_from_wishlist(request, product_id):
    """Remove product from wishlist"""
    product = get_object_or_404(Product, id=product_id)
    try:
        wishlist = request.user.wishlist
        wishlist.products.remove(product)
        log_user_activity(request.user, 'wishlist_remove', f'Removed {product.name} from wishlist', request)
        messages.success(request, f'{product.name} removed from wishlist!')
    except Wishlist.DoesNotExist:
        messages.error(request, 'Wishlist not found!')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': 'Removed from wishlist'})
    
    return redirect('wishlist')

def newsletter_subscribe(request):
    """Subscribe to newsletter"""
    if request.method == 'POST':
        form = NewsletterSubscriptionForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            
            # Check if already subscribed
            subscription, created = NewsletterSubscription.objects.get_or_create(
                email=email,
                defaults={'user': request.user if request.user.is_authenticated else None}
            )
            
            if created:
                messages.success(request, 'Successfully subscribed to newsletter!')
            else:
                if subscription.is_active:
                    messages.info(request, 'You are already subscribed to our newsletter.')
                else:
                    subscription.is_active = True
                    subscription.unsubscribed_at = None
                    subscription.save()
                    messages.success(request, 'Welcome back! You are now subscribed to our newsletter.')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Subscribed successfully'})
    
    return redirect('home')

def newsletter_unsubscribe(request, token):
    """Unsubscribe from newsletter"""
    # This would need proper token implementation
    try:
        # Decode token and get email
        # For now, just show unsubscribe page
        return render(request, 'useraccounts/newsletter_unsubscribe.html')
    except:
        messages.error(request, 'Invalid unsubscribe link.')
        return redirect('home')

def contact_view(request):
    """Contact form"""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Send email
            subject = f"Contact Form: {form.cleaned_data['subject']}"
            message = f"""
            From: {form.cleaned_data['name']} ({form.cleaned_data['email']})
            Phone: {form.cleaned_data.get('phone', 'Not provided')}
            
            Message:
            {form.cleaned_data['message']}
            """
            
            try:
                send_mail(
                    subject,
                    message,
                    form.cleaned_data['email'],
                    [settings.DEFAULT_FROM_EMAIL],
                    fail_silently=False,
                )
                messages.success(request, 'Your message has been sent! We will get back to you soon.')
            except Exception as e:
                messages.error(request, 'There was an error sending your message. Please try again.')
            
            return redirect('contact')
    else:
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                'name': request.user.get_full_name(),
                'email': request.user.email,
            }
        form = ContactForm(initial=initial_data)
    
    return render(request, 'useraccounts/contact.html', {'form': form})

@login_required
def delete_account(request):
    """Delete user account"""
    if request.method == 'POST':
        password = request.POST.get('password')
        if request.user.check_password(password):
            # Log activity before deletion
            log_user_activity(request.user, 'account_delete', 'Account deleted', request)
            
            # Delete user
            request.user.delete()
            messages.success(request, 'Your account has been deleted successfully.')
            return redirect('home')
        else:
            messages.error(request, 'Incorrect password. Account not deleted.')
    
    return render(request, 'useraccounts/delete_account.html')

@login_required
def download_user_data(request):
    """Download user data (GDPR compliance)"""
    response = HttpResponse(content_type='application/json')
    response['Content-Disposition'] = f'attachment; filename="user_data_{request.user.username}.json"'
    
    # Collect user data
    user_data = {
        'user_info': {
            'username': request.user.username,
            'email': request.user.email,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'date_joined': request.user.date_joined.isoformat(),
        },
        'profile': {},
        'orders': [],
        'addresses': [],
        'activities': [],
    }
    
    # Profile data
    if hasattr(request.user, 'profile'):
        profile = request.user.profile
        user_data['profile'] = {
            'phone': profile.phone,
            'date_of_birth': profile.date_of_birth.isoformat() if profile.date_of_birth else None,
            'city': profile.city,
            'state': profile.state,
            'country': profile.country,
        }
    
    # Orders data
    for order in Order.objects.filter(user=request.user):
        user_data['orders'].append({
            'order_number': order.order_number,
            'total_amount': str(order.total_amount),
            'status': order.status,
            'created_at': order.created_at.isoformat(),
        })
    
    # Addresses data
    for address in Address.objects.filter(user=request.user):
        user_data['addresses'].append({
            'name': address.name,
            'address_line1': address.address_line1,
            'city': address.city,
            'state': address.state,
            'pincode': address.pincode,
        })
    
    # Activities data (last 100)
    for activity in UserActivity.objects.filter(user=request.user)[:100]:
        user_data['activities'].append({
            'activity_type': activity.activity_type,
            'description': activity.description,
            'created_at': activity.created_at.isoformat(),
        })
    
    json.dump(user_data, response, indent=2)
    return response

def verify_email(request, token):
    """Email verification"""
    # Implement email verification logic
    messages.success(request, 'Email verified successfully!')
    return redirect('login')

def resend_verification(request):
    """Resend email verification"""
    if request.user.is_authenticated:
        # Send verification email
        messages.success(request, 'Verification email sent!')
    else:
        messages.error(request, 'Please log in to resend verification email.')
    
    return redirect('profile')

@login_required
def user_activity(request):
    """View user activities"""
    activities = UserActivity.objects.filter(user=request.user).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(activities, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'useraccounts/user_activity.html', {'page_obj': page_obj})

@login_required
def user_preferences(request):
    """User preferences"""
    try:
        preferences = request.user.preferences
    except UserPreferences.DoesNotExist:
        preferences = UserPreferences.objects.create(user=request.user)
    
    if request.method == 'POST':
        preferences.email_marketing = request.POST.get('email_marketing') == 'on'
        preferences.email_order_updates = request.POST.get('email_order_updates') == 'on'
        preferences.sms_notifications = request.POST.get('sms_notifications') == 'on'
        preferences.profile_visibility = request.POST.get('profile_visibility', 'public')
        preferences.show_activity = request.POST.get('show_activity') == 'on'
        preferences.save()
        
        messages.success(request, 'Preferences updated successfully!')
        return redirect('user_preferences')
    
    return render(request, 'useraccounts/user_preferences.html', {'preferences': preferences})

# Helper functions
def send_welcome_email(user):
    """Send welcome email to new user"""
    subject = 'Welcome to Emerald Secrets!'
    message = f"""
    Dear {user.first_name or user.username},
    
    Welcome to Emerald Secrets! We're excited to have you join our community.
    
    Discover our premium natural beauty products and enjoy:
    - 100% Natural Ingredients
    - Free Shipping on all orders
    - Exclusive member offers
    - Expert beauty tips
    
    Start shopping: {settings.SITE_URL}/shop/
    
    Best regards,
    The Emerald Secrets Team
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True,
        )
    except Exception as e:
        print(f"Failed to send welcome email: {e}")

def log_user_activity(user, activity_type, description="", request=None):
    """Helper function to log user activities"""
    try:
        ip_address = None
        user_agent = ""
        
        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')
            else:
                ip_address = request.META.get('REMOTE_ADDR')
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

# Error handlers
def custom_404(request, exception):
    """Custom 404 error handler"""
    return render(request, 'errors/404.html', status=404)

def custom_500(request):
    """Custom 500 error handler"""
    return render(request, 'errors/500.html', status=500)
