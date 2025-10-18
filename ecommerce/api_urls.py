from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register(r'categories', api_views.CategoryViewSet, basename='category')
router.register(r'products', api_views.ProductViewSet, basename='product')
router.register(r'cart', api_views.CartViewSet, basename='cart')
router.register(r'orders', api_views.OrderViewSet, basename='order')
router.register(r'reviews', api_views.ReviewViewSet, basename='review')
router.register(r'coupons', api_views.CouponViewSet, basename='coupon')

urlpatterns = [
    path('', include(router.urls)),
]
