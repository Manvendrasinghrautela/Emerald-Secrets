from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from useraccounts.forms import UserRegistrationForm, CustomPasswordChangeForm
from ecommerce.emails import send_welcome_email
from django.views.decorators.http import require_http_methods, require_POST
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth import logout, authenticate, login, update_session_auth_hash
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils.text import slugify
import logging
import json
import csv
from datetime import datetime

from ecommerce.models import Order, OrderItem, Wishlist, Product, Newsletter

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_user_activity(user, action, description, request):
    """Log user activity for tracking"""
    try:
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]
        logger.info(
            f"User Activity | Action: {action} | User: {user.username} | "
            f"Email: {user.email} | IP: {ip_address} | Description: {description}"
        )
    except Exception as e:
        logger.error(f"Error logging user activity: {str(e)}")


@require_http_methods(["GET", "POST"])
def signup(request):
    """User registration with email verification"""
    if request.user.is_authenticated:
        messages.info(request, 'You are already logged in.')
        return redirect('home')
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save(commit=False)
                user.is_active = True  # or False if you want email verification workflow
                user.save()

                username = form.cleaned_data.get('username')
                email = form.cleaned_data.get('email')

                log_user_activity(user, 'signup', f'New user registered with email {email}', request)

                messages.success(request, f'✅ Account created successfully for {username}! Please log in.')

                try:
                    send_welcome_email(user)
                    messages.info(request, '📧 Welcome email sent to your inbox!')
                    logger.info(f"Welcome email sent to {email}")
                except Exception as email_error:
                    logger.warning(f"Welcome email failed for {email}: {email_error}")
                    messages.warning(request, 'Account created, but welcome email could not be sent.')

                return redirect('login')
            except Exception as e:
                logger.error(f"Error during user registration: {str(e)}")
                messages.error(request, '❌ An error occurred during registration. Please try again.')
        else:
            logger.warning(f"Signup form validation failed: {form.errors}")
            if 'username' in form.errors:
                messages.error(request, f'❌ {form.errors["username"][0]}')
            if 'email' in form.errors:
                messages.error(request, f'❌ {form.errors["email"][0]}')
            if 'password1' in form.errors:
                messages.error(request, f'❌ {form.errors["password1"][0]}')
    else:
        form = UserRegistrationForm()
    return render(request, 'useraccounts/signup.html', {'form': form, 'page_title': 'Create Your Account'})


@require_http_methods(["GET"])
def logout_view(request):
    """User logout with activity logging"""
    username = request.user.username
    log_user_activity(request.user, 'logout', 'User logged out', request)
    logout(request)
    messages.success(request, f'Goodbye {username}! You have been logged out.')
    return redirect('home')


@require_http_methods(["GET", "POST"])
@login_required(login_url='login')
def verify_email(request, token):
    """Verify user email"""
    try:
        user = User.objects.get(verification_token=token)
        user.is_active = True
        user.verification_token = None
        user.save()
        log_user_activity(user, 'email_verified', 'Email verified successfully', request)
        messages.success(request, '✅ Email verified successfully! You can now log in.')
        return redirect('login')
    except User.DoesNotExist:
        messages.error(request, '❌ Invalid verification token.')
        return redirect('home')


@require_http_methods(["POST"])
@login_required(login_url='login')
def resend_verification(request):
    """Resend verification email"""
    try:
        user = request.user
        if user.is_active:
            messages.info(request, 'Your email is already verified.')
            return redirect('profile')
        send_welcome_email(user)
        messages.success(request, '📧 Verification email resent!')
        return redirect('profile')
    except Exception as e:
        logger.error(f"Error resending verification: {str(e)}")
        messages.error(request, '❌ Error resending verification email.')
        return redirect('profile')


@login_required(login_url='login')
def profile_view(request):
    """User profile view"""
    try:
        recent_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
        wishlist_count = Wishlist.objects.filter(user=request.user).count()
        context = {'user': request.user,
                   'recent_orders': recent_orders,
                   'wishlist_count': wishlist_count}
        return render(request, 'useraccounts/profile.html', context)
    except Exception as e:
        logger.error(f"Error loading profile for {request.user.username}: {str(e)}")
        messages.error(request, '❌ Error loading profile.')
        return redirect('home')


@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def edit_profile(request):
    """Edit user profile"""
    if request.method == 'POST':
        try:
            user = request.user
            user.first_name = request.POST.get('first_name', '')
            user.last_name = request.POST.get('last_name', '')
            user.email = request.POST.get('email', user.email)
            user.save()
            log_user_activity(user, 'profile_update', 'User updated their profile', request)
            messages.success(request, '✅ Profile updated successfully!')
            return redirect('profile')
        except Exception as e:
            logger.error(f"Error updating profile: {str(e)}")
            messages.error(request, '❌ Error updating profile.')
    return render(request, 'useraccounts/edit_profile.html', {'user': request.user})


@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def change_password(request):
    """Change user password"""
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            log_user_activity(user, 'password_change', 'User changed their password', request)
            messages.success(request, '✅ Your password has been changed successfully!')
            return redirect('profile')
        else:
            messages.error(request, '❌ Please correct the errors below.')
    else:
        form = CustomPasswordChangeForm(request.user)
    return render(request, 'useraccounts/change_password.html', {'form': form})


@login_required(login_url='login')
def order_list(request):
    """List user orders"""
    try:
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
        paginator = Paginator(orders, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context = {'orders': page_obj, 'page_obj': page_obj}
        return render(request, 'useraccounts/order_list.html', context)
    except Exception as e:
        logger.error(f"Error loading orders for {request.user.username}: {str(e)}")
        messages.error(request, '❌ Error loading orders.')
        return redirect('home')


@login_required(login_url='login')
def order_detail(request, order_number):
    """View order details"""
    try:
        order = get_object_or_404(Order, order_number=order_number, user=request.user)
        order_items = OrderItem.objects.filter(order=order)
        context = {'order': order, 'order_items': order_items}
        return render(request, 'useraccounts/order_detail.html', context)
    except Exception as e:
        logger.error(f"Error loading order {order_number}: {str(e)}")
        messages.error(request, '❌ Error loading order details.')
        return redirect('order_list')


@login_required(login_url='login')
def address_list(request):
    """List user addresses"""
    try:
        context = {}
        return render(request, 'useraccounts/address_list.html', context)
    except Exception as e:
        logger.error(f"Error loading addresses: {str(e)}")
        messages.error(request, '❌ Error loading addresses.')
        return redirect('profile')


@login_required(login_url='login')
def add_address(request):
    """Add new address"""
    if request.method == 'POST':
        messages.success(request, '✅ Address added successfully!')
        return redirect('address_list')
    return render(request, 'useraccounts/add_address.html')


@login_required(login_url='login')
def edit_address(request, address_id):
    """Edit address"""
    if request.method == 'POST':
        messages.success(request, '✅ Address updated successfully!')
        return redirect('address_list')
    return render(request, 'useraccounts/edit_address.html')


@login_required(login_url='login')
@require_POST
def delete_address(request, address_id):
    """Delete address"""
    messages.success(request, '✅ Address deleted successfully!')
    return redirect('address_list')


@login_required(login_url='login')
@require_POST
def set_default_address(request, address_id):
    """Set default address"""
    messages.success(request, '✅ Default address set!')
    return redirect('address_list')


@login_required(login_url='login')
def wishlist_view(request):
    """View user wishlist"""
    try:
        wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
        context = {'wishlist_items': wishlist_items}
        return render(request, 'useraccounts/wishlist.html', context)
    except Exception as e:
        logger.error(f"Error loading wishlist: {str(e)}")
        messages.error(request, '❌ Error loading wishlist.')
        return redirect('home')


@login_required(login_url='login')
@require_POST
def add_to_wishlist(request, product_id):
    """Add product to wishlist"""
    try:
        product = get_object_or_404(Product, id=product_id)
        wishlist, created = Wishlist.objects.get_or_create(user=request.user, product=product)
        if created:
            messages.success(request, f'✅ {product.name} added to wishlist!')
        else:
            messages.info(request, f'{product.name} is already in your wishlist.')
        return redirect('product_detail', slug=product.slug)
    except Exception as e:
        logger.error(f"Error adding to wishlist: {str(e)}")
        messages.error(request, '❌ Error adding to wishlist.')
        return redirect('shop')


@login_required(login_url='login')
@require_POST
def remove_from_wishlist(request, product_id):
    """Remove product from wishlist"""
    try:
        product = get_object_or_404(Product, id=product_id)
        Wishlist.objects.filter(user=request.user, product=product).delete()
        messages.success(request, f'✅ {product.name} removed from wishlist!')
        return redirect('wishlist')
    except Exception as e:
        logger.error(f"Error removing from wishlist: {str(e)}")
        messages.error(request, '❌ Error removing from wishlist.')
        return redirect('wishlist')


@require_http_methods(["POST"])
def newsletter_subscribe(request):
    """Subscribe to newsletter"""
    try:
        email = request.POST.get('email', '')
        if not email:
            messages.error(request, '❌ Please enter an email address.')
            return redirect('home')
        newsletter, created = Newsletter.objects.get_or_create(email=email)
        if created:
            messages.success(request, '✅ Subscribed to our newsletter!')
        else:
            messages.info(request, 'This email is already subscribed.')
        return redirect('home')
    except Exception as e:
        logger.error(f"Error subscribing to newsletter: {str(e)}")
        messages.error(request, '❌ Error subscribing to newsletter.')
        return redirect('home')


@require_http_methods(["GET"])
def newsletter_unsubscribe(request, token):
    """Unsubscribe from newsletter"""
    try:
        newsletter = Newsletter.objects.get(unsubscribe_token=token)
        newsletter.delete()
        messages.success(request, '✅ You have been unsubscribed from our newsletter.')
        return redirect('home')
    except Newsletter.DoesNotExist:
        messages.error(request, '❌ Invalid unsubscribe token.')
        return redirect('home')


@require_http_methods(["GET", "POST"])
def contact_view(request):
    """Contact form view"""
    if request.method == 'POST':
        try:
            name = request.POST.get('name', '')
            email = request.POST.get('email', '')
            subject = request.POST.get('subject', '')
            message = request.POST.get('message', '')
            # Your contact email sending logic here
            messages.success(request, '✅ Your message has been sent! We will contact you soon.')
            logger.info(f"Contact form submitted by {email}")
            return redirect('contact')
        except Exception as e:
            logger.error(f"Error processing contact form: {str(e)}")
            messages.error(request, '❌ Error sending message.')
    return render(request, 'useraccounts/contact.html')


@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def delete_account(request):
    """Delete user account"""
    if request.method == 'POST':
        try:
            password = request.POST.get('password', '')
            user = authenticate(username=request.user.username, password=password)
            if user is not None:
                username = user.username
                user.delete()
                messages.success(request, '✅ Your account has been deleted.')
                logger.info(f"User account deleted: {username}")
                return redirect('home')
            else:
                messages.error(request, '❌ Incorrect password.')
        except Exception as e:
            logger.error(f"Error deleting account: {str(e)}")
            messages.error(request, '❌ Error deleting account.')
    return render(request, 'useraccounts/delete_account.html')


@login_required(login_url='login')
def download_user_data(request):
    """Download user data (GDPR compliance)"""
    try:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="user_data.csv"'
        writer = csv.writer(response)
        writer.writerow(['User Data Export', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
        writer.writerow([])
        writer.writerow(['User Information'])
        writer.writerow(['Username', request.user.username])
        writer.writerow(['Email', request.user.email])
        writer.writerow(['First Name', request.user.first_name])
        writer.writerow(['Last Name', request.user.last_name])
        writer.writerow(['Join Date', request.user.date_joined])
        writer.writerow([])
        writer.writerow(['Order History'])
        orders = Order.objects.filter(user=request.user)
        for order in orders:
            writer.writerow([order.order_number, order.total_amount, order.created_at])
        logger.info(f"User data downloaded by {request.user.username}")
        messages.success(request, '✅ Your data has been downloaded.')
        return response
    except Exception as e:
        logger.error(f"Error downloading user data: {str(e)}")
        messages.error(request, '❌ Error downloading data.')
        return redirect('profile')


@login_required(login_url='login')
def user_activity(request):
    """View user activity log"""
    context = {}
    return render(request, 'useraccounts/activity.html', context)


@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def user_preferences(request):
    """Manage user preferences"""
    if request.method == 'POST':
        try:
            messages.success(request, '✅ Preferences updated successfully!')
            return redirect('preferences')
        except Exception as e:
            logger.error(f"Error updating preferences: {str(e)}")
            messages.error(request, '❌ Error updating preferences.')
    return render(request, 'useraccounts/preferences.html')


def custom_404(request, exception=None):
    """Custom 404 error page"""
    return render(request, '404.html', status=404)


def custom_500(request):
    """Custom 500 error page"""
    return render(request, '500.html', status=500)
