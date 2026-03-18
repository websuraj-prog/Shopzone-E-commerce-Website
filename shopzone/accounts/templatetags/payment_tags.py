from django import template

register = template.Library()

@register.filter
def razorpay_is_test(key):
    """
    Custom template filter to check if Razorpay key is test mode.
    Returns True if key starts with 'rzp_test', False otherwise.
    Usage: {% if razorpay_key|razorpay_is_test %}Test mode{% endif %}
    """
    if not key:
        return False
    return key.startswith('rzp_test')

