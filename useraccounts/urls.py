from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Authentication URLs
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(
        template_name='useraccounts/login.html',
        redirect_authenticated_user=True
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Profile URLs
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/password-change/', views.change_password, name='change_password'),
    
    # Order URLs
    path('orders/', views.order_list, name='order_list'),
    path('order/<str:order_number>/', views.order_detail, name='order_detail'),
    
    # Address management URLs
    path('addresses/', views.address_list, name='address_list'),
    path('addresses/add/', views.add_address, name='add_address'),
    path('addresses/<int:address_id>/edit/', views.edit_address, name='edit_address'),
    path('addresses/<int:address_id>/delete/', views.delete_address, name='delete_address'),
    path('addresses/<int:address_id>/set-default/', views.set_default_address, name='set_default_address'),
    
    # Wishlist URLs
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    
    # Newsletter and contact
    path('newsletter/subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),
    path('newsletter/unsubscribe/<str:token>/', views.newsletter_unsubscribe, name='newsletter_unsubscribe'),
    path('contact/', views.contact_view, name='contact'),
    
    # Account management
    path('delete-account/', views.delete_account, name='delete_account'),
    path('download-data/', views.download_user_data, name='download_user_data'),
    
    # Password reset URLs (custom templates)
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='useraccounts/password_reset.html',
             email_template_name='useraccounts/password_reset_email.html',
             subject_template_name='useraccounts/password_reset_subject.txt'
         ),
         name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='useraccounts/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='useraccounts/password_reset_confirm.html'
         ),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='useraccounts/password_reset_complete.html'
         ),
         name='password_reset_complete'),
    
    # Email verification (if needed)
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),
    
    # Activity and preferences
    path('activity/', views.user_activity, name='user_activity'),
    path('preferences/', views.user_preferences, name='user_preferences'),
]

# Custom error handlers
handler404 = 'useraccounts.views.custom_404'
handler500 = 'useraccounts.views.custom_500'
