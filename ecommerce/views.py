from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods, require_POST
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Count
import logging
import uuid

from .models import (
    Product, Category, Cart, CartItem, Order, OrderItem, Review,
    AffiliateProfile, AffiliateClick, AffiliateReferral, Newsletter
)
from .forms import ReviewForm, CheckoutForm
from ecommerce.emails import (
    send_order_confirmation_email, 
    send_order_notification_to_admin,
    send_affiliate_commission_earned,
    send_contact_email
)

logger = logging.getLogger(__name__)


# ========== UTILITY FUNCTIONS ==========

def generate_unique_order_number():
    """Generate unique order number"""
    return uuid.uuid4().hex.upper()[0:12]


def track_affiliate_click(request, affiliate_code, product_id=None):
    """Track affiliate click and store in session"""
    try:
        affiliate = AffiliateProfile.objects.get(
            affiliate_code=affiliate_code, 
            is_active=True, 
            is_approved=True
        )
        
        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        ip = x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')
        
        # Get product if specified
        product = None
        if product_id:
            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                pass
        
        # Create click record
        AffiliateClick.objects.create(
            affiliate=affiliate,
            product=product,
            ip_address=ip,
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
            referrer=request.META.get('HTTP_REFERER', '')
        )
        
        # Store affiliate code in session (valid for 30 days)
        request.session['affiliate_code'] = affiliate_code
        request.session.set_expiry(30 * 24 * 60 * 60)
        
        return True
    except AffiliateProfile.DoesNotExist:
        return False


# ========== MAIN VIEWS ==========

def home(request):
    """Home page with affiliate tracking"""
    affiliate_code = request.GET.get('ref')
    if affiliate_code:
        track_affiliate_click(request, affiliate_code)
    
    featured_products = Product.objects.filter(is_featured=True, is_active=True)[:6]
    categories = Category.objects.all()[:3]
    latest_products = Product.objects.filter(is_active=True).order_by('-created_at')[:8]
    
    context = {
        'featured_products': featured_products,
        'categories': categories,
        'latest_products': latest_products,
    }
    return render(request, 'home.html', context)


def shop(request):
    """Shop page with affiliate tracking"""
    affiliate_code = request.GET.get('ref')
    if affiliate_code:
        track_affiliate_click(request, affiliate_code)
    
    products = Product.objects.filter(is_active=True)
    categories = Category.objects.all()
    
    # Filter by category
    category_slug = request.GET.get('category')
    if category_slug:
        try:
            category = Category.objects.get(slug=category_slug)
            products = products.filter(category=category)
        except Category.DoesNotExist:
            pass
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Sorting
    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    else:
        products = products.order_by('name')
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'search_query': search_query,
        'sort_by': sort_by,
    }
    return render(request, 'shop.html', context)


def product_detail(request, slug):
    """Product detail page with affiliate tracking"""
    product = get_object_or_404(Product, slug=slug, is_active=True)
    
    affiliate_code = request.GET.get('ref')
    if affiliate_code:
        track_affiliate_click(request, affiliate_code, product.id)
    
    reviews = product.reviews.all().order_by('-created_at')
    related_products = Product.objects.filter(
        category=product.category, 
        is_active=True
    ).exclude(id=product.id)[:4]
    
    # Calculate average rating
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
    if avg_rating:
        avg_rating = round(avg_rating, 1)
    
    # Review form
    review_form = ReviewForm()
    user_review = None
    if request.user.is_authenticated:
        try:
            user_review = Review.objects.get(product=product, user=request.user)
        except Review.DoesNotExist:
            pass
    
    if request.method == 'POST' and request.user.is_authenticated:
        review_form = ReviewForm(request.POST)
        if review_form.is_valid():
            review = review_form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            messages.success(request, 'Your review has been added!')
            return redirect('product_detail', slug=slug)
    
    context = {
        'product': product,
        'reviews': reviews,
        'related_products': related_products,
        'avg_rating': avg_rating,
        'review_form': review_form,
        'user_review': user_review,
    }
    return render(request, 'product_detail.html', context)


def category_products(request, slug):
    """Category products page with affiliate tracking"""
    affiliate_code = request.GET.get('ref')
    if affiliate_code:
        track_affiliate_click(request, affiliate_code)
    
    category = get_object_or_404(Category, slug=slug, is_active=True)
    products = Product.objects.filter(category=category, is_active=True).order_by('-created_at')
    
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'products': page_obj,
        'total_products': products.count(),
    }
    return render(request, 'category_products.html', context)


def collections(request):
    """Display all collections/categories"""
    affiliate_code = request.GET.get('ref')
    if affiliate_code:
        track_affiliate_click(request, affiliate_code)
    
    categories = Category.objects.filter(is_active=True).annotate(
        product_count=Count('products', filter=Q(products__is_active=True))
    )
    
    context = {
        'categories': categories,
    }
    return render(request, 'ecommerce/collections.html', context)


# ========== ABOUT AND CONTACT VIEWS ==========

def about(request):
    """Redirect to home page with about anchor"""
    return redirect('home')


@require_http_methods(["GET", "POST"])
def contact_view(request):
    """Contact form view"""
    if request.method == 'POST':
        try:
            name = request.POST.get('name', '').strip()
            email = request.POST.get('email', '').strip()
            phone = request.POST.get('phone', '').strip()
            subject = request.POST.get('subject', '').strip()
            message = request.POST.get('message', '').strip()
            
            # Validate required fields
            if not all([name, email, subject, message]):
                messages.error(request, '❌ Please fill in all required fields.')
                return redirect('home')
            
            # Send contact email to admin
            send_contact_email(name, email, phone, subject, message)
            
            messages.success(request, '✅ Your message has been sent! We will contact you soon.')
            logger.info(f"Contact form submitted by {email}")
            
            return redirect('home')
        
        except Exception as e:
            logger.error(f"Error processing contact form: {str(e)}")
            messages.error(request, '❌ Error sending message. Please try again.')
            return redirect('home')
    
    return redirect('home')


# ========== NEWSLETTER VIEW ==========

@require_http_methods(["POST"])
def newsletter_subscribe(request):
    """Subscribe to newsletter"""
    try:
        email = request.POST.get('email', '').strip()
        
        if not email:
            messages.error(request, '❌ Please enter an email address.')
            return redirect('home')
        
        newsletter, created = Newsletter.objects.get_or_create(email=email)
        
        if created:
            messages.success(request, '✅ Subscribed to our newsletter!')
            logger.info(f"New newsletter subscription: {email}")
        else:
            messages.info(request, 'This email is already subscribed.')
        
        return redirect('home')
    
    except Exception as e:
        logger.error(f"Error subscribing to newsletter: {str(e)}")
        messages.error(request, '❌ Error subscribing to newsletter.')
        return redirect('home')


# ========== CART VIEWS ==========

@login_required(login_url='login')
def add_to_cart(request, product_id):
    """Add product to cart"""
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 1}
    )
    
    if not created:
        if cart_item.quantity < product.stock:
            cart_item.quantity += 1
            cart_item.save()
            messages.success(request, f'{product.name} quantity updated in cart!')
        else:
            messages.warning(request, f'Sorry, only {product.stock} items available!')
    else:
        messages.success(request, f'{product.name} added to cart!')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'cart_count': cart.total_items})
    
    return redirect('cart')


@login_required(login_url='login')
def cart_view(request):
    """Shopping cart view"""
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.all()
    except Cart.DoesNotExist:
        cart = None
        cart_items = []

    total_price = sum(item.product.price * item.quantity for item in cart_items)
    total_items = sum(item.quantity for item in cart_items)

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total_price': total_price,
        'total_items': total_items,
    }
    return render(request, 'cart.html', context)


@login_required(login_url='login')
@require_http_methods(["POST"])
def update_cart_item(request, item_id):
    """Update cart item quantity"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    action = request.POST.get('action')
    
    if action == 'increase':
        if cart_item.quantity < cart_item.product.stock:
            cart_item.quantity += 1
            cart_item.save()
            messages.success(request, 'Quantity updated!')
    elif action == 'decrease':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
            messages.success(request, 'Quantity updated!')
    elif action == 'remove':
        product_name = cart_item.product.name
        cart_item.delete()
        messages.success(request, f'{product_name} removed from cart!')
    
    return redirect('cart')


# ========== CHECKOUT & ORDER VIEWS ==========

@login_required(login_url='login')
def checkout(request):
    """Checkout with affiliate tracking"""
    affiliate_code = request.session.get('affiliate_code')
    
    try:
        cart = Cart.objects.get(user=request.user)
        if not cart.items.exists():
            messages.warning(request, 'Your cart is empty!')
            return redirect('cart')
    except Cart.DoesNotExist:
        messages.warning(request, 'Your cart is empty!')
        return redirect('cart')
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            try:
                # Calculate total
                total_amount = sum(item.product.price * item.quantity for item in cart.items.all())
                
                # Create order
                order = Order.objects.create(
                    user=request.user,
                    order_number=generate_unique_order_number(),
                    shipping_name=form.cleaned_data['name'],
                    shipping_email=form.cleaned_data['email'],
                    shipping_phone=form.cleaned_data['phone'],
                    shipping_address=form.cleaned_data['address'],
                    shipping_city=form.cleaned_data['city'],
                    shipping_state=form.cleaned_data['state'],
                    shipping_pincode=form.cleaned_data['pincode'],
                    affiliate_code=affiliate_code
                )
                
                # Create order items
                for cart_item in cart.items.all():
                    OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        quantity=cart_item.quantity,
                        price=cart_item.product.price
                    )
                    
                    # Update product stock
                    product = cart_item.product
                    product.stock -= cart_item.quantity
                    product.save()
                
                # Create affiliate referral if applicable
                if affiliate_code:
                    try:
                        affiliate = AffiliateProfile.objects.get(
                            affiliate_code=affiliate_code,
                            is_active=True,
                            is_approved=True
                        )
                        
                        commission_amount = total_amount * (affiliate.commission_rate / 100)
                        
                        AffiliateReferral.objects.create(
                            affiliate=affiliate,
                            order=order,
                            commission_amount=commission_amount,
                            status='pending'
                        )
                        
                        send_affiliate_commission_earned(affiliate, commission_amount, order.order_number)
                        
                    except AffiliateProfile.DoesNotExist:
                        pass
                
                # Clear cart
                cart.items.all().delete()
                
                # Send emails
                send_order_confirmation_email(order)
                send_order_notification_to_admin(order)
                
                messages.success(request, f'Order {order.order_number} placed successfully!')
                return redirect('order_confirmation', order_number=order.order_number)
            
            except Exception as e:
                logger.error(f"Error during checkout: {str(e)}")
                messages.error(request, '❌ Error placing order. Please try again.')
    else:
        initial_data = {}
        if hasattr(request.user, 'profile'):
            profile = request.user.profile
            initial_data = {
                'name': request.user.get_full_name(),
                'email': request.user.email,
                'phone': getattr(profile, 'phone', ''),
                'address': getattr(profile, 'address_line1', ''),
                'city': getattr(profile, 'city', ''),
                'state': getattr(profile, 'state', ''),
                'pincode': getattr(profile, 'pincode', ''),
            }
        form = CheckoutForm(initial=initial_data)
    
    context = {
        'cart': cart,
        'form': form,
    }
    return render(request, 'checkout.html', context)


@login_required(login_url='login')
def order_confirmation(request, order_number):
    """Order confirmation page"""
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    has_referral = hasattr(order, 'affiliate_referral')
    
    context = {
        'order': order,
        'has_referral': has_referral,
    }
    return render(request, 'order_confirmation.html', context)


# ========== HELPER FUNCTIONS ==========

def approve_affiliate_commission(order_id):
    """
    Approve affiliate commission after payment confirmation
    Call this after payment is confirmed via payment gateway callback
    """
    try:
        order = Order.objects.get(id=order_id)
        if hasattr(order, 'affiliate_referral'):
            referral = order.affiliate_referral
            if referral.status == 'pending':
                referral.approve()
                logger.info(f"Affiliate commission approved for order {order.order_number}")
                return True
    except Order.DoesNotExist:
        logger.warning(f"Order {order_id} not found for commission approval")
        pass
    return False
