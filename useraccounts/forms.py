from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm, PasswordChangeForm as DjangoPasswordChangeForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import re
import logging


logger = logging.getLogger(__name__)


# ========== UTILITY FUNCTIONS ==========

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
            f"User Activity: {action} | User: {user.username} | "
            f"Email: {user.email} | IP: {ip_address} | Description: {description}"
        )
    except Exception as e:
        logger.error(f"Error logging user activity: {str(e)}")


# ========== AUTHENTICATION FORMS ==========

class UserRegistrationForm(UserCreationForm):
    """
    Custom user registration form with enhanced validation
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address',
            'autocomplete': 'email',
        }),
        help_text='Required. Enter a valid email address.'
    )
    
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name',
            'autocomplete': 'given-name',
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name',
            'autocomplete': 'family-name',
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Username field
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Username',
            'autocomplete': 'username',
        })
        self.fields['username'].help_text = 'Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'
        
        # Password1 field
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password',
            'autocomplete': 'new-password',
        })
        self.fields['password1'].help_text = '''
        <ul class="small text-muted mb-0">
            <li>Your password can't be too similar to your other personal information.</li>
            <li>Your password must contain at least 8 characters.</li>
            <li>Your password can't be a commonly used password.</li>
            <li>Your password can't be entirely numeric.</li>
        </ul>
        '''
        
        # Password2 field
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm Password',
            'autocomplete': 'new-password',
        })
        self.fields['password2'].help_text = 'Enter the same password as before, for verification.'
    
    def clean_email(self):
        """Validate email uniqueness"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('❌ This email address is already registered. Please use a different email or log in.')
        return email
    
    def clean_username(self):
        """Validate username uniqueness and format"""
        username = self.cleaned_data.get('username')
        
        if User.objects.filter(username=username).exists():
            raise ValidationError('❌ This username is already taken. Please choose a different username.')
        
        if len(username) < 3:
            raise ValidationError('❌ Username must be at least 3 characters long.')
        
        return username
    
    def clean_first_name(self):
        """Validate first name"""
        first_name = self.cleaned_data.get('first_name')
        if first_name and len(first_name.strip()) == 0:
            raise ValidationError('First name cannot be empty.')
        return first_name
    
    def clean_last_name(self):
        """Validate last name"""
        last_name = self.cleaned_data.get('last_name')
        if last_name and len(last_name.strip()) == 0:
            raise ValidationError('Last name cannot be empty.')
        return last_name
    
    def clean(self):
        """Overall form validation"""
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise ValidationError('❌ Passwords do not match. Please try again.')
        
        return cleaned_data
    
    def save(self, commit=True):
        """Save user with additional fields"""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            logger.info(f"New user registered: {user.username} ({user.email})")
        
        return user


class CustomAuthenticationForm(AuthenticationForm):
    """
    Custom login form with enhanced styling
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Username or Email',
            'autocomplete': 'username',
        })
        
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password',
            'autocomplete': 'current-password',
        })


# ========== PROFILE FORMS ==========

class UserProfileForm(forms.Form):
    """
    User profile form for editing personal information
    """
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name'
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name'
        })
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address',
            'readonly': 'readonly'
        })
    )
    
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Phone Number (e.g., +91 9876543210)'
        })
    )
    
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    profile_image = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )
    
    address_line1 = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Address Line 1'
        })
    )
    
    address_line2 = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Address Line 2 (Optional)'
        })
    )
    
    city = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'City'
        })
    )
    
    state = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'State/Province'
        })
    )
    
    pincode = forms.CharField(
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Postal Code (6 digits)'
        })
    )
    
    country = forms.CharField(
        max_length=100,
        required=False,
        initial='India',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Country'
        })
    )
    
    def clean_phone(self):
        """Validate phone number"""
        phone = self.cleaned_data.get('phone')
        if phone:
            phone_digits = re.sub(r'\D', '', phone)
            if len(phone_digits) < 10:
                raise ValidationError('❌ Phone number must be at least 10 digits long.')
            if len(phone_digits) > 15:
                raise ValidationError('❌ Phone number cannot be more than 15 digits.')
        return phone
    
    def clean_pincode(self):
        """Validate pincode"""
        pincode = self.cleaned_data.get('pincode')
        if pincode:
            if not pincode.isdigit():
                raise ValidationError('❌ Pincode must contain only numbers.')
            if len(pincode) != 6:
                raise ValidationError('❌ Pincode must be exactly 6 digits.')
        return pincode
    
    def clean_profile_image(self):
        """Validate profile image"""
        image = self.cleaned_data.get('profile_image')
        if image:
            # Check file size (max 5MB)
            if image.size > 5 * 1024 * 1024:
                raise ValidationError('❌ Image file size must be less than 5MB.')
            
            # Check file extension
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            if not any(image.name.lower().endswith(ext) for ext in valid_extensions):
                raise ValidationError('❌ Only JPG, JPEG, PNG, GIF and WebP files are allowed.')
        
        return image


# ========== PASSWORD CHANGE FORM ==========

class CustomPasswordChangeForm(DjangoPasswordChangeForm):
    """
    Custom password change form with Bootstrap styling
    """
    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
        
        self.fields['old_password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Current Password'
        })
        
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'New Password'
        })
        self.fields['new_password1'].help_text = '✓ At least 8 characters<br>✓ Cannot be entirely numeric'
        
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm New Password'
        })


# ========== CONTACT FORM ==========

class ContactForm(forms.Form):
    """
    Contact form for user inquiries
    """
    name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your Full Name'
        })
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your Email Address'
        })
    )
    
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Phone Number (Optional)'
        })
    )
    
    subject = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Subject'
        })
    )
    
    message = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 6,
            'placeholder': 'Your Message (Please be detailed)'
        })
    )
    
    def clean_phone(self):
        """Validate phone number"""
        phone = self.cleaned_data.get('phone')
        if phone:
            phone_digits = re.sub(r'\D', '', phone)
            if len(phone_digits) < 10:
                raise ValidationError('❌ Please enter a valid phone number with at least 10 digits.')
        return phone
    
    def clean_message(self):
        """Validate message length"""
        message = self.cleaned_data.get('message')
        if message and len(message) < 10:
            raise ValidationError('❌ Message must be at least 10 characters long.')
        return message


# ========== NEWSLETTER FORM ==========

class NewsletterSubscriptionForm(forms.Form):
    """
    Newsletter subscription form
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
            'autocomplete': 'email',
        })
    )
    
    def clean_email(self):
        """Validate email"""
        email = self.cleaned_data.get('email')
        return email


# ========== ADDRESS FORM ==========

class AddressForm(forms.Form):
    """
    Address form for shipping and billing
    """
    address_type = forms.ChoiceField(
        required=True,
        choices=[
            ('shipping', 'Shipping Address'),
            ('billing', 'Billing Address'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    full_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Full Name'
        })
    )
    
    phone = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Phone Number'
        })
    )
    
    address_line1 = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Address Line 1'
        })
    )
    
    address_line2 = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Address Line 2 (Optional)'
        })
    )
    
    city = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'City'
        })
    )
    
    state = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'State/Province'
        })
    )
    
    pincode = forms.CharField(
        max_length=10,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Postal Code'
        })
    )
    
    country = forms.CharField(
        max_length=100,
        required=True,
        initial='India',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Country'
        })
    )
    
    is_default = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    def clean_phone(self):
        """Validate phone number"""
        phone = self.cleaned_data.get('phone')
        phone_digits = re.sub(r'\D', '', phone)
        
        if len(phone_digits) < 10:
            raise ValidationError('❌ Phone number must be at least 10 digits.')
        
        return phone
    
    def clean_pincode(self):
        """Validate pincode"""
        pincode = self.cleaned_data.get('pincode')
        
        if not pincode.isdigit():
            raise ValidationError('❌ Pincode must contain only numbers.')
        
        if len(pincode) != 6:
            raise ValidationError('❌ Pincode must be exactly 6 digits.')
        
        return pincode


# ========== ACCOUNT DELETION FORM ==========

class DeleteAccountForm(forms.Form):
    """
    Form for account deletion confirmation
    """
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password to confirm deletion'
        })
    )
    
    confirmation = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='I understand this action cannot be undone'
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_password(self):
        """Verify password"""
        password = self.cleaned_data.get('password')
        
        if not self.user.check_password(password):
            raise ValidationError('❌ Incorrect password.')
        
        return password


# ========== PREFERENCES FORM ==========

class UserPreferencesForm(forms.Form):
    """
    User preferences form for notifications and settings
    """
    email_notifications = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Receive email notifications'
    )
    
    order_updates = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Order status updates'
    )
    
    promotional_emails = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Promotional emails and offers'
    )
    
    newsletter = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Subscribe to newsletter'
    )
    
    two_factor_auth = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Enable two-factor authentication'
    )
