from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from .models import (
    AffiliateProfile, AffiliateClick, AffiliateReferral, 
    AffiliateWithdrawal, Product
)
from .forms import AffiliateProfileForm, AffiliateWithdrawalForm
from ecommerce.emails import send_affiliate_signup_email, send_affiliate_notification_to_admin

def affiliate_info(request):
    """Affiliate program information page"""
    return render(request, 'ecommerce/affiliate/info.html')


@login_required
def affiliate_signup(request):
    """Affiliate signup page"""
    # Check if user already has affiliate profile
    if hasattr(request.user, 'affiliate_profile'):
        return redirect('affiliate_dashboard')
    
    if request.method == 'POST':
        form = AffiliateProfileForm(request.POST)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            # Send confirmation email to affiliate
            send_affiliate_signup_email(profile)
            
            # Send notification email to admin
            send_affiliate_notification_to_admin(profile)
            messages.success(request, 'Your affiliate application has been submitted! We will review and approve it soon.')
            return redirect('affiliate_dashboard')
    else:
        form = AffiliateProfileForm()
    
    return render(request, 'ecommerce/affiliate/signup.html', {'form': form})


@login_required
def affiliate_dashboard(request):
    """Affiliate dashboard"""
    try:
        affiliate = request.user.affiliate_profile
    except AffiliateProfile.DoesNotExist:
        return redirect('affiliate_signup')
    
    # Statistics
    total_clicks = affiliate.clicks.count()
    total_referrals = affiliate.referrals.count()
    approved_referrals = affiliate.referrals.filter(status='approved').count()
    
    # Recent activity
    recent_clicks = affiliate.clicks.order_by('-clicked_at')[:10]
    recent_referrals = affiliate.referrals.order_by('-created_at')[:10]
    
    # Monthly stats
    thirty_days_ago = timezone.now() - timedelta(days=30)
    monthly_clicks = affiliate.clicks.filter(clicked_at__gte=thirty_days_ago).count()
    monthly_referrals = affiliate.referrals.filter(created_at__gte=thirty_days_ago).count()
    monthly_earnings = affiliate.referrals.filter(
        created_at__gte=thirty_days_ago, 
        status__in=['approved', 'paid']
    ).aggregate(total=Sum('commission_amount'))['total'] or 0
    
    context = {
        'affiliate': affiliate,
        'total_clicks': total_clicks,
        'total_referrals': total_referrals,
        'approved_referrals': approved_referrals,
        'recent_clicks': recent_clicks,
        'recent_referrals': recent_referrals,
        'monthly_clicks': monthly_clicks,
        'monthly_referrals': monthly_referrals,
        'monthly_earnings': monthly_earnings,
    }
    return render(request, 'ecommerce/affiliate/dashboard.html', context)


@login_required
def affiliate_links(request):
    """Generate affiliate links"""
    try:
        affiliate = request.user.affiliate_profile
    except AffiliateProfile.DoesNotExist:
        return redirect('affiliate_signup')
    
    products = Product.objects.filter(is_active=True)
    
    context = {
        'affiliate': affiliate,
        'products': products,
    }
    return render(request, 'ecommerce/affiliate/links.html', context)


@login_required
def affiliate_earnings(request):
    """View earnings and referrals"""
    try:
        affiliate = request.user.affiliate_profile
    except AffiliateProfile.DoesNotExist:
        return redirect('affiliate_signup')
    
    referrals = affiliate.referrals.order_by('-created_at')
    withdrawals = affiliate.withdrawals.order_by('-requested_at')
    
    context = {
        'affiliate': affiliate,
        'referrals': referrals,
        'withdrawals': withdrawals,
    }
    return render(request, 'ecommerce/affiliate/earnings.html', context)


@login_required
def affiliate_withdraw(request):
    """Request withdrawal"""
    try:
        affiliate = request.user.affiliate_profile
    except AffiliateProfile.DoesNotExist:
        return redirect('affiliate_signup')
    
    if request.method == 'POST':
        form = AffiliateWithdrawalForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            
            # Validate withdrawal amount
            if amount > affiliate.pending_earnings:
                messages.error(request, 'Insufficient balance for withdrawal.')
            elif amount < 500:
                messages.error(request, 'Minimum withdrawal amount is ₹500.')
            else:
                withdrawal = form.save(commit=False)
                withdrawal.affiliate = affiliate
                withdrawal.save()
                messages.success(request, 'Withdrawal request submitted successfully!')
                return redirect('affiliate_earnings')
    else:
        form = AffiliateWithdrawalForm()
    
    context = {
        'affiliate': affiliate,
        'form': form,
    }
    return render(request, 'ecommerce/affiliate/withdraw.html', context)


@login_required
def affiliate_profile_edit(request):
    """Edit affiliate profile"""
    try:
        affiliate = request.user.affiliate_profile
    except AffiliateProfile.DoesNotExist:
        return redirect('affiliate_signup')
    
    if request.method == 'POST':
        form = AffiliateProfileForm(request.POST, instance=affiliate)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('affiliate_dashboard')
    else:
        form = AffiliateProfileForm(instance=affiliate)
    
    context = {
        'affiliate': affiliate,
        'form': form,
    }
    return render(request, 'ecommerce/affiliate/profile_edit.html', context)
