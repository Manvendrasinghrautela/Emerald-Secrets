from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from .models import UserProfile, Wishlist

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    extra = 0
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('phone', 'date_of_birth', 'profile_image')
        }),
        ('Address Information', {
            'fields': ('address_line1', 'address_line2', 'city', 'state', 'pincode', 'country'),
            'classes': ('collapse',)
        }),
    )

class UserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline]
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined', 'get_phone']
    list_filter = BaseUserAdmin.list_filter + ('profile__city', 'profile__state')
    
    def get_phone(self, obj):
        try:
            return obj.profile.phone or 'Not provided'
        except UserProfile.DoesNotExist:
            return 'No profile'
    get_phone.short_description = 'Phone'
    get_phone.admin_order_field = 'profile__phone'

# Unregister the existing User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'city', 'state', 'created_at', 'get_profile_image']
    list_filter = ['state', 'city', 'country', 'created_at']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name', 'phone']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Personal Information', {
            'fields': ('phone', 'date_of_birth', 'profile_image')
        }),
        ('Address Information', {
            'fields': ('address_line1', 'address_line2', 'city', 'state', 'pincode', 'country')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_profile_image(self, obj):
        if obj.profile_image and obj.profile_image.name != 'profiles/default.jpg':
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 50%;" />',
                obj.profile_image.url
            )
        return "No Image"
    get_profile_image.short_description = 'Profile Picture'

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'product_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'user__email']
    filter_horizontal = ['products']
    readonly_fields = ['created_at']
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products Count'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

# Custom admin site customization
admin.site.site_header = "Emerald Secrets Admin"
admin.site.site_title = "Emerald Secrets Admin Portal"
admin.site.index_title = "Welcome to Emerald Secrets Administration"

# Add custom CSS to admin
class AdminCustomization:
    class Media:
        css = {
            'all': ('admin/css/custom.css',)
        }
        js = ('admin/js/custom.js',)
