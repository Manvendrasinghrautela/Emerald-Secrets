from django.urls import path, include
from . import views
from . import affiliate_views

urlpatterns = [
    path('', views.home, name='home'),
    path('shop/', views.shop, name='shop'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('category/<slug:slug>/', views.category_products, name='category_products'),
    path('collections/', views.collections, name='collections'),
    path('collection/<slug:slug>/', views.category_products, name='category_products'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('checkout/', views.checkout, name='checkout'),
    path('order-confirmation/<str:order_number>/', views.order_confirmation, name='order_confirmation'),
    path('affiliate/', affiliate_views.affiliate_info, name='affiliate_info'),
    path('affiliate/signup/', affiliate_views.affiliate_signup, name='affiliate_signup'),
    path('affiliate/dashboard/', affiliate_views.affiliate_dashboard, name='affiliate_dashboard'),
    path('affiliate/links/', affiliate_views.affiliate_links, name='affiliate_links'),
    path('affiliate/earnings/', affiliate_views.affiliate_earnings, name='affiliate_earnings'),
    path('affiliate/withdraw/', affiliate_views.affiliate_withdraw, name='affiliate_withdraw'),
    path('affiliate/profile/edit/', affiliate_views.affiliate_profile_edit, name='affiliate_profile_edit'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact_view, name='contact_view'),
    path('newsletter/subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),

]
