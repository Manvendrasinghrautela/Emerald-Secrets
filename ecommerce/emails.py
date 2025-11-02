from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_welcome_email(user):
    """Send welcome email when new user registers"""
    subject = f'Welcome to {settings.SITE_URL} - Emerald Secrets'
    html_message = render_to_string('emails/welcome.html', {
        'user': user,
        'site_name': 'Emerald Secrets',
    })
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
        fail_silently=False,
    )

def send_contact_email(name, email, phone, subject, message):
    """Send contact form email to admin"""
    try:
        subject_line = f"New Contact Form Submission: {subject}"
        
        html_message = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; background-color: #f5f5f5; }}
                    .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; }}
                    .header {{ background-color: #d63384; color: white; padding: 20px; border-radius: 5px; text-align: center; }}
                    .content {{ padding: 20px; }}
                    .info-box {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 15px 0; border-left: 4px solid #d63384; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>📧 New Contact Form Submission</h2>
                    </div>
                    
                    <div class="content">
                        <h3>Message Details:</h3>
                        
                        <div class="info-box">
                            <p><strong>Name:</strong> {name}</p>
                            <p><strong>Email:</strong> <a href="mailto:{email}">{email}</a></p>
                            <p><strong>Phone:</strong> {phone if phone else 'Not provided'}</p>
                            <p><strong>Subject:</strong> {subject}</p>
                        </div>
                        
                        <div class="info-box">
                            <h4>Message:</h4>
                            <p>{message}</p>
                        </div>
                        
                        <p style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd;">
                            <strong>Please respond to this message at your earliest convenience.</strong>
                        </p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        plain_message = f"""
        Contact Form Submission:
        
        Name: {name}
        Email: {email}
        Phone: {phone if phone else 'Not provided'}
        Subject: {subject}
        
        Message:
        {message}
        """
        
        send_mail(
            subject_line,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.COMPANY_EMAIL],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Contact form email sent from {email}")
    except Exception as e:
        logger.error(f"Error sending contact email: {str(e)}")


def send_order_confirmation_email(order):
    """Send order confirmation to customer"""
    subject = f'Order Confirmation #{order.order_number}'
    html_message = render_to_string('emails/order_confirmation.html', {
        'order': order,
        'customer_name': order.user.get_full_name() or order.user.username,
    })
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [order.user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_order_notification_to_admin(order):
    """Send order notification to company admin with full order details"""
    try:
        subject = f'🎉 New Order Received - #{order.order_number}'
        
        # Build order items details
        order_items_html = ""
        for item in order.items.all():
            order_items_html += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{item.product.name}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: center;">{item.quantity}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right;">₹{item.price}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right;">₹{item.total_price}</td>
            </tr>
            """
        
        html_message = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; background-color: #f5f5f5; }}
                    .container {{ max-width: 800px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; }}
                    .header {{ background-color: #28a745; color: white; padding: 20px; border-radius: 5px; text-align: center; }}
                    .content {{ padding: 20px; }}
                    .order-summary {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                    .order-details {{ margin: 20px 0; }}
                    table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                    th {{ background-color: #f0f0f0; padding: 10px; text-align: left; font-weight: bold; }}
                    .total-row {{ background-color: #f0f0f0; font-weight: bold; }}
                    .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #999; border-top: 1px solid #ddd; margin-top: 20px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎉 New Order Received!</h1>
                    </div>
                    
                    <div class="content">
                        <h2>Order Summary</h2>
                        
                        <div class="order-summary">
                            <p><strong>Order Number:</strong> {order.order_number}</p>
                            <p><strong>Order Date:</strong> {order.created_at.strftime('%d %b %Y, %H:%M:%S')}</p>
                            <p><strong>Order Status:</strong> {order.get_status_display()}</p>
                        </div>
                        
                        <h3>Customer Information</h3>
                        <div class="order-details">
                            <p><strong>Name:</strong> {order.shipping_name}</p>
                            <p><strong>Email:</strong> {order.shipping_email}</p>
                            <p><strong>Phone:</strong> {order.shipping_phone}</p>
                            <p><strong>Username:</strong> {order.user.username}</p>
                        </div>
                        
                        <h3>Shipping Address</h3>
                        <div class="order-details">
                            <p>
                                {order.shipping_address}<br>
                                {order.shipping_city}, {order.shipping_state} - {order.shipping_pincode}
                            </p>
                        </div>
                        
                        <h3>Order Items</h3>
                        <table>
                            <tr>
                                <th>Product Name</th>
                                <th>Quantity</th>
                                <th>Unit Price</th>
                                <th>Total</th>
                            </tr>
                            {order_items_html}
                            <tr class="total-row">
                                <td colspan="3" style="text-align: right; padding: 10px;">Total Amount:</td>
                                <td style="text-align: right; padding: 10px;">₹{order.total_amount}</td>
                            </tr>
                        </table>
                        
                        <div class="order-summary">
                            <p><strong>Total Items:</strong> {order.items.count()}</p>
                            <p><strong>Total Amount:</strong> ₹{order.total_amount}</p>
                            {f'<p><strong>Affiliate Code:</strong> {order.affiliate_code}</p>' if order.affiliate_code else ''}
                        </div>
                        
                        <p style="margin-top: 20px; color: #666;">
                            Please log in to your admin panel to process this order and manage shipment details.
                        </p>
                    </div>
                    
                    <div class="footer">
                        <p>&copy; 2025 Emerald Secrets. All rights reserved.</p>
                        <p>This is an automated notification email. Do not reply to this email.</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.COMPANY_EMAIL],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Admin order notification sent for order {order.order_number}")
    except Exception as e:
        logger.error(f"Error sending admin order notification: {str(e)}")


def send_affiliate_signup_email(affiliate):
    """Send confirmation email to affiliate"""
    subject = 'Welcome to Emerald Secrets Affiliate Program'
    html_message = render_to_string('emails/affiliate_signup.html', {
        'affiliate': affiliate,
        'affiliate_code': affiliate.affiliate_code,
    })
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [affiliate.user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_affiliate_notification_to_admin(affiliate):
    """Send affiliate signup notification to company admin"""
    subject = f'New Affiliate Signup - {affiliate.user.username}'
    html_message = render_to_string('emails/admin_affiliate_notification.html', {
        'affiliate': affiliate,
        'user': affiliate.user,
    })
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [settings.COMPANY_EMAIL],
        html_message=html_message,
        fail_silently=False,
    )


def send_affiliate_commission_earned(affiliate, commission_amount, order_number):
    """Send email when affiliate earns commission"""
    subject = f'You Earned ₹{commission_amount} Commission!'
    html_message = render_to_string('emails/affiliate_commission.html', {
        'affiliate': affiliate,
        'commission_amount': commission_amount,
        'order_number': order_number,
    })
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [affiliate.user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_withdrawal_request_email(withdrawal):
    """Send withdrawal request confirmation"""
    subject = f'Withdrawal Request Received - ₹{withdrawal.amount}'
    html_message = render_to_string('emails/withdrawal_request.html', {
        'withdrawal': withdrawal,
        'affiliate': withdrawal.affiliate,
    })
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [withdrawal.affiliate.user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_withdrawal_processed_email(withdrawal):
    """Send confirmation when withdrawal is processed"""
    subject = f'Withdrawal Processed - ₹{withdrawal.amount}'
    html_message = render_to_string('emails/withdrawal_processed.html', {
        'withdrawal': withdrawal,
        'affiliate': withdrawal.affiliate,
    })
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [withdrawal.affiliate.user.email],
        html_message=html_message,
        fail_silently=False,
    )
