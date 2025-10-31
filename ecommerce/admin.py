from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, Cart, CartItem, Order, OrderItem, Review, AffiliateProfile, AffiliateClick, AffiliateReferral, AffiliateWithdrawal

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock', 'is_active', 'is_featured', 'created_at']
    list_filter = ['category', 'is_active', 'is_featured', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['price', 'stock', 'is_active', 'is_featured']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'category')
        }),
        ('Pricing', {
            'fields': ('price', 'compare_price')
        }),
        ('Images', {
            'fields': ('image', 'image2', 'image3')
        }),
        ('Inventory', {
            'fields': ('stock', 'weight')
        }),
        ('Product Details', {
            'fields': ('ingredients', 'how_to_use', 'benefits')
        }),
        ('Status', {
            'fields': ('is_active', 'is_featured')
        }),
    )
    
    def get_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "No Image"
    get_image.short_description = 'Image'

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_items', 'total_price', 'updated_at']
    inlines = [CartItemInline]
    readonly_fields = ['total_price', 'total_items']

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['total_price']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order_number', 'user__username', 'shipping_email']
    list_editable = ['status']
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status', 'total_amount')
        }),
        ('Shipping Information', {
            'fields': ('shipping_name', 'shipping_email', 'shipping_phone', 
                      'shipping_address', 'shipping_city', 'shipping_state', 'shipping_pincode')
        }),
    )
    
    readonly_fields = ['order_number', 'total_amount']

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['product__name', 'user__username']

# Customize admin site
admin.site.site_header = "Emerald Secrets Admin"
admin.site.site_title = "Emerald Secrets Admin Portal"
admin.site.index_title = "Welcome to Emerald Secrets Administration"

@admin.register(AffiliateProfile)
class AffiliateProfileAdmin(admin.ModelAdmin):
    list_display = ['affiliate_code', 'user', 'is_approved', 'is_active', 'total_earnings', 'created_at']
    list_filter = ['is_approved', 'is_active', 'created_at']
    search_fields = ['user__username', 'affiliate_code']
    readonly_fields = ['affiliate_code', 'created_at', 'updated_at']

@admin.register(AffiliateClick)
class AffiliateClickAdmin(admin.ModelAdmin):
    list_display = ['affiliate', 'product', 'clicked_at']
    list_filter = ['clicked_at', 'affiliate']
    readonly_fields = ['clicked_at']

@admin.register(AffiliateReferral)
class AffiliateReferralAdmin(admin.ModelAdmin):
    list_display = ['affiliate', 'order', 'commission_amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    actions = ['approve_referrals', 'mark_as_paid']
    readonly_fields = ['created_at']
    
    def approve_referrals(self, request, queryset):
        for referral in queryset:
            referral.approve()
    approve_referrals.short_description = "Approve selected referrals"
    
    def mark_as_paid(self, request, queryset):
        for referral in queryset.filter(status='approved'):
            referral.mark_as_paid()
    mark_as_paid.short_description = "Mark as paid"

@admin.register(AffiliateWithdrawal)
class AffiliateWithdrawalAdmin(admin.ModelAdmin):
    list_display = ['affiliate', 'amount', 'status', 'requested_at']
    list_filter = ['status', 'requested_at']
    readonly_fields = ['requested_at']