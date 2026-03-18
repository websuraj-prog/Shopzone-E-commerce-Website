import os
import json
import uuid
import razorpay
import logging
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse, HttpResponseBadRequest
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import get_template
from products.models import Product, ColorVariant, SizeVariant, Coupon
from home.models import ShippingAddress
from accounts.models import Profile, Cart, CartItem, Order, OrderItem
from accounts.forms import UserUpdateForm, UserProfileForm, ShippingAddressForm, CustomPasswordChangeForm, UPIForm

# Set up logging
logger = logging.getLogger(__name__)

def login_page(request):
    if request.user.is_authenticated:
        return redirect('index')
    next_url = request.GET.get('next')
    if request.method == 'POST':
        username = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            Profile.objects.get_or_create(user=user)
            messages.success(request, 'Login successful.')
            if url_has_allowed_host_and_scheme(url=next_url, allowed_hosts=request.get_host()):
                return redirect(next_url)
            return redirect('index')
        messages.warning(request, 'Invalid email or password.')
        return HttpResponseRedirect(request.path_info)
    return render(request, 'accounts/login.html')

def register_page(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        age = request.POST.get('age')
        email = request.POST.get('email')
        password = request.POST.get('password')
        if not all([first_name, last_name, age, email, password]):
            messages.warning(request, 'Please fill all fields.')
            return HttpResponseRedirect(request.path_info)
        try:
            age = int(age)
            if age < 13:
                messages.warning(request, 'Age must be at least 13.')
                return HttpResponseRedirect(request.path_info)
        except ValueError:
            messages.warning(request, 'Age must be a valid number.')
            return HttpResponseRedirect(request.path_info)
        if User.objects.filter(username=email).exists() or User.objects.filter(email=email).exists():
            messages.info(request, 'Email already exists!')
            return HttpResponseRedirect(request.path_info)
        user = User.objects.create_user(username=email, email=email, password=password, first_name=first_name, last_name=last_name)
        profile, created = Profile.objects.get_or_create(user=user)
        profile.age = age
        profile.is_email_verified = True
        profile.email_token = None
        profile.save()
        user_obj = authenticate(request, username=email, password=password)
        if user_obj:
            login(request, user_obj)
            messages.success(request, 'Registration successful and logged in.')
            return redirect('index')
        messages.error(request, 'Login after registration failed.')
        return HttpResponseRedirect(request.path_info)
    return render(request, 'accounts/register.html')

@login_required
def user_logout(request):
    logout(request)
    messages.warning(request, "Logged Out Successfully!")
    return redirect('index')

@login_required
def add_to_cart(request, uid):
    try:
        product = get_object_or_404(Product, uid=uid)
        variant = request.GET.get('size')
        if not variant:
            first_size = SizeVariant.objects.filter(product=product).first()
            if first_size:
                variant = first_size.size_name
            else:
                messages.warning(request, 'No size available for this product!')
                return redirect(request.META.get('HTTP_REFERER'))
        size_variant, created = SizeVariant.objects.get_or_create(size_name=variant, defaults={'price': 0, 'order': 10})
        if created:
            messages.info(request, f'Size {variant} created.')
        cart, _ = Cart.objects.get_or_create(user=request.user, is_paid=False)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product, size_variant=size_variant)
        if not created:
            cart_item.quantity += 1
            cart_item.save()
        messages.success(request, 'Item added to cart successfully.')
    except Exception as e:
        messages.error(request, f'Error adding item to cart: {str(e)}')
    return redirect(reverse('cart'))

@login_required
def add_sneaker_to_cart(request, name):
    variant = request.GET.get('size')
    if not variant:
        messages.warning(request, 'Please select a size before adding to cart!')
        return redirect(request.META.get('HTTP_REFERER'))
    size_variant, created = SizeVariant.objects.get_or_create(size_name=variant, defaults={'price': 0, 'order': 10})
    if created:
        messages.info(request, f'Size {variant} created.')
    try:
        json_path = os.path.join(settings.BASE_DIR, 'sneakers.json')
        with open(json_path, 'r', encoding='utf-8') as f:
            sneakers_data = json.load(f)
    except Exception as e:
        messages.error(request, f'Error loading sneakers: {str(e)}')
        return redirect('index')
    sneaker = next((item for item in sneakers_data if item.get('name') == name), None)
    if not sneaker:
        messages.error(request, 'Sneaker not found.')
        return redirect('index')
    cart, _ = Cart.objects.get_or_create(user=request.user, is_paid=False)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, sneaker_data=sneaker, size_variant=size_variant, defaults={'product': None, 'color_variant': None})
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    action = 'added' if created else 'quantity increased'
    messages.success(request, f'{sneaker["name"]} size {variant} {action} in cart!')
    return redirect('cart')

@login_required
def buy_sneaker_now(request, name):
    return add_sneaker_to_cart(request, name)

@login_required
def cart(request):
    cart_obj = None
    user = request.user
    try:
        cart_obj = Cart.objects.get(is_paid=False, user=user)
    except Cart.DoesNotExist:
        messages.warning(request, "Your cart is empty. Please add a product to cart.")
        return redirect(reverse('index'))
    if request.method == 'POST':
        coupon = request.POST.get('coupon')
        coupon_obj = Coupon.objects.filter(coupon_code__exact=coupon).first()
        if not coupon_obj:
            messages.warning(request, 'Invalid coupon code.')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        if cart_obj.coupon:
            messages.warning(request, 'Coupon already exists.')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        if coupon_obj.is_expired:
            messages.warning(request, 'Coupon code expired.')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        if cart_obj.get_cart_total() < coupon_obj.minimum_amount:
            messages.warning(request, f'Amount should be greater than {coupon_obj.minimum_amount}')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        if coupon_obj.for_new_users and Order.objects.filter(user=request.user).exists():
            messages.warning(request, 'NEW10 coupon only for new users (no prior orders).')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        cart_obj.coupon = coupon_obj
        cart_obj.save()
        messages.success(request, 'Coupon applied successfully.')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    context = {'cart': cart_obj, 'quantity_range': range(1, 6)}
    return render(request, 'accounts/cart.html', context)

@require_POST
@login_required
def update_cart_item(request):
    try:
        data = json.loads(request.body)
        cart_item_id = data.get("cart_item_id")
        quantity = int(data.get("quantity"))
        cart_item = CartItem.objects.get(uid=cart_item_id, cart__user=request.user, cart__is_paid=False)
        cart_item.quantity = quantity
        cart_item.save()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})

def remove_cart(request, uid):
    try:
        cart_item = get_object_or_404(CartItem, uid=uid)
        cart_item.delete()
        messages.success(request, 'Item removed from cart.')
    except Exception as e:
        messages.warning(request, 'Error removing item from cart.')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def remove_coupon(request, cart_id):
    cart = Cart.objects.get(uid=cart_id)
    cart.coupon = None
    cart.save()
    messages.success(request, 'Coupon Removed.')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def success(request):
    razorpay_order_id = request.GET.get('order_id') or request.session.get('razorpay_order_id')
    logger.info(f"Success view called with order_id: {razorpay_order_id}")
    if not razorpay_order_id:
        logger.error("No razorpay_order_id in success")
        messages.error(request, 'Payment order not found.')
        return redirect('order_history')
    
    try:
        cart = Cart.objects.get(razorpay_order_id=razorpay_order_id, is_paid=False)
        logger.info(f"Cart found: {cart.pk}, paid={cart.is_paid}")
        address_pk_str = request.session.get('address_pk')
        if address_pk_str:
            address = get_object_or_404(ShippingAddress, pk=uuid.UUID(address_pk_str), user=cart.user)
        else:
            profile = Profile.objects.get(user=cart.user)
            address = profile.shipping_address
            logger.info("Used profile shipping_address")
        
        cart.is_paid = True
        cart.save()
        logger.info(f"Cart {cart.pk} marked paid")
        order = create_order(cart, address, 'Card', 'Paid', razorpay_order_id=razorpay_order_id)
        logger.info(f"Order created: {order.order_id}")
        
        for key in ['cart_pk', 'address_pk', 'razorpay_order_id']:
            request.session.pop(key, None)
        
        messages.success(request, f'Order #{order.order_id} placed successfully!')
        context = {'order': order}
        return render(request, 'payment_success/payment_success.html', context)
    except Cart.DoesNotExist:
        logger.error(f"Cart not found for {razorpay_order_id}")
        messages.error(request, 'Cart not found for this payment.')
        return redirect('order_history')
    except Exception as e:
        logger.error(f'Success view error: {str(e)}')
        messages.error(request, 'Order processing failed.')
        return redirect('order_history')

def render_to_pdf(template_src, context_dict={}, filename='invoice.pdf'):
    try:
        import weasyprint
        template = get_template(template_src)
        html = template.render(context_dict)
        pdf_bytes = weasyprint.HTML(string=html, base_url=settings.STATIC_URL).write_pdf()
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except (ImportError, Exception) as e:
        return HttpResponse(f"PDF generation unavailable (WeasyPrint issue): {str(e)}. Contact support.", status=503)

def download_invoice(request, order_id):
    order = Order.objects.filter(order_id=order_id).first()
    if not order:
        return HttpResponse("Order not found", status=404)
    order_items = order.order_items.all()
    context = {'order': order, 'order_items': order_items}
    pdf = render_to_pdf('accounts/order_pdf_generate.html', context, filename=f'invoice_{order_id}.pdf')
    return pdf

@login_required
def profile_view(request, username):
    user_name = get_object_or_404(User, username=username)
    user = request.user
    profile, created = Profile.objects.get_or_create(user=user)
    if created:
        messages.info(request, 'Profile created automatically.')
    user_form = UserUpdateForm(instance=user)
    profile_form = UserProfileForm(instance=profile)
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        user_form.fields['age'].initial = profile.age
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile.age = user_form.cleaned_data.get('age')
            profile.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    context = {'user_name': user_name, 'user_form': user_form, 'profile_form': profile_form}
    return render(request, 'accounts/profile.html', context)

@login_required
def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        messages.warning(request, 'Please correct the error below.')
    else:
        form = CustomPasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html', {'form': form})

@login_required
def update_shipping_address(request):
    shipping_address = ShippingAddress.objects.filter(user=request.user, current_address=True).first()
    if request.method == 'POST':
        form = ShippingAddressForm(request.POST, instance=shipping_address)
        if form.is_valid():
            shipping_address = form.save(commit=False)
            shipping_address.user = request.user
            shipping_address.current_address = True
            shipping_address.save()
            messages.success(request, "The Address Has Been Successfully Saved/Updated!")
            form = ShippingAddressForm()
        else:
            form = ShippingAddressForm(request.POST, instance=shipping_address)
    else:
        form = ShippingAddressForm(instance=shipping_address)
    return render(request, 'accounts/shipping_address_form.html', {'form': form})

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-order_date')
    return render(request, 'accounts/order_history.html', {'orders': orders})

@login_required
def order_details(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    order_items = OrderItem.objects.filter(order=order)
    context = {
        'order': order,
        'order_items': order_items,
        'order_total_price': sum(item.get_total_price() for item in order_items),
        'coupon_discount': order.coupon.discount_amount if order.coupon else 0,
        'grand_total': order.get_order_total_price()
    }
    return render(request, 'accounts/order_details.html', context)

@login_required
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, "Your account has been deleted successfully.")
        return redirect('index')

@csrf_exempt
def verify_payment(request):
    logger.info("verify_payment called")
    if request.method == "POST":
        try:
            body = json.loads(request.body)
            razorpay_signature = request.META.get('HTTP_X_RAZORPAY_SIGNATURE', '')
            logger.info(f"Verifying payment: order_id={body.get('razorpay_order_id')}, signature={razorpay_signature[:10]}...")
            
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET_KEY))
            client.utility.verify_payment_signature(body, razorpay_signature)
            logger.info("Signature verified OK")
            
            razorpay_order_id = body.get('razorpay_order_id')
            razorpay_payment_id = body.get('razorpay_payment_id')
            
            cart = Cart.objects.get(razorpay_order_id=razorpay_order_id, is_paid=False)
            cart.razorpay_payment_id = razorpay_payment_id
            cart.save()
            logger.info(f"Payment ID {razorpay_payment_id} saved to cart {cart.pk}")
            
            return JsonResponse({"status": "success"})
        except Exception as e:
            logger.error(f"Payment verification failed: {str(e)}")
            logger.error(f"Body: {request.body}, Signature: {request.META.get('HTTP_X_RAZORPAY_SIGNATURE', '')}")
            return JsonResponse({"status": "failure"}, status=400)
    logger.warning("verify_payment invalid method")
    return JsonResponse({"status": "invalid method"}, status=405)

@login_required
def checkout_start(request):
    if request.method == 'POST':
        cart = Cart.objects.filter(user=request.user, is_paid=False).first()
        if not cart or not cart.cart_items.exists():
            messages.warning(request, 'Your cart is empty.')
            return redirect('cart')
        request.session['cart_pk'] = str(cart.pk)
        return redirect('checkout_addresses')
    return redirect('cart')

@login_required
def checkout_addresses(request):
    cart_pk_str = request.session.get('cart_pk')
    if not cart_pk_str:
        return redirect('checkout_start')
    try:
        cart_pk = uuid.UUID(cart_pk_str)
        cart = get_object_or_404(Cart, pk=cart_pk, user=request.user, is_paid=False)
    except (ValueError, Cart.DoesNotExist):
        messages.warning(request, 'Invalid cart. Starting fresh.')
        return redirect('checkout_start')
    
    addresses = ShippingAddress.objects.filter(user=request.user)
    address_form = ShippingAddressForm()
    
    if request.method == 'POST':
        address_id = request.POST.get('address_id')
        if address_id:
            address = get_object_or_404(ShippingAddress, pk=address_id, user=request.user)
            request.session['address_pk'] = str(address.pk)
            messages.success(request, 'Address selected.')
            return redirect('checkout_payment')
        
        address_form = ShippingAddressForm(request.POST)
        if address_form.is_valid():
            address = address_form.save(commit=False)
            address.user = request.user
            address.current_address = True
            address.save()
            request.session['address_pk'] = str(address.pk)
            messages.success(request, 'New address added and selected.')
            return redirect('checkout_payment')
    
    context = {'cart': cart, 'addresses': addresses, 'address_form': address_form}
    return render(request, 'accounts/checkout_addresses.html', context)

@login_required
def checkout_payment(request):
    cart_pk_str = request.session.get('cart_pk')
    address_pk_str = request.session.get('address_pk')
    
    if not cart_pk_str or not address_pk_str:
        messages.warning(request, 'Please select address first.')
        return redirect('checkout_addresses')
    
    try:
        cart_pk = uuid.UUID(cart_pk_str)
        address_pk = uuid.UUID(address_pk_str)
        cart = get_object_or_404(Cart, pk=cart_pk, user=request.user, is_paid=False)
        address = get_object_or_404(ShippingAddress, pk=address_pk, user=request.user)
    except ValueError:
        logger.error(f"Invalid UUID in session: cart={cart_pk_str}, address={address_pk_str}")
        messages.error(request, 'Session expired. Please restart checkout.')
        return redirect('cart')
    except Exception as e:
        logger.error(f"Cart/Address lookup failed: {str(e)}")
        messages.error(request, 'Cart or address not found.')
        return redirect('checkout_addresses')
    
    total = cart.get_cart_total_price_after_coupon()
    if total <= 0:
        messages.error(request, 'Cart total must be greater than 0.')
        return redirect('cart')

    total_paise = int(total * 100)
    upi_form = UPIForm()
    razorpay_order_id = None

    context = {
        'cart': cart,
        'address': address,
        'total': total,
        'total_paise': total_paise,
        'upi_form': upi_form,
        'razorpay_order_id': None,
        'razorpay_key': settings.RAZORPAY_KEY_ID,
        'merchant_upi': [
            'shopzone@paytm',
            'shopzone@phonepe',
            'shopzone@ybl',
            'shopzone@okaxis',
            'shopzone@okhdfcbank',
            'shopzone@payu',
            'shopzone@icici'
        ],
    }

    if request.method == 'POST':
        payment_mode = request.POST.get('payment_mode')

        try:
            if payment_mode == 'cod':
                logger.info(f"COD order created for cart {cart.pk}, user {cart.user.username}")
                order = create_order(cart, address, 'COD', 'Pending')
                cart.is_paid = True
                cart.save()
                request.session.pop('cart_pk', None)
                request.session.pop('address_pk', None)
                messages.success(request, f'Order #{order.order_id} placed successfully via Cash on Delivery!')
                logger.info(f"COD success: Order {order.order_id}")
                return redirect('order_history')

            elif payment_mode == 'upi':
                upi_option = request.POST.get('upi_option')
                if upi_option == 'id':
                    upi_form = UPIForm(request.POST)
                    if upi_form.is_valid():
                        upi_id = upi_form.cleaned_data['upi_id']
                        logger.info(f"UPI ID payment for cart {cart.pk}, UPI: {upi_id}")
                        order = create_order(cart, address, 'UPI', 'Pending', upi_id)
                        cart.is_paid = True
                        cart.save()
                        request.session.pop('cart_pk', None)
                        request.session.pop('address_pk', None)
                        messages.success(request, f'Order placed! Pay via UPI ID: {upi_id}')
                        logger.info(f"UPI success: Order {order.order_id}")
                        return redirect('order_history')
                    messages.warning(request, 'Invalid UPI ID!')
                elif upi_option == 'app':
                    logger.info(f"UPI app payment for cart {cart.pk}")
                    order = create_order(cart, address, 'UPI', 'Pending')
                    cart.is_paid = True
                    cart.save()
                    request.session.pop('cart_pk', None)
                    request.session.pop('address_pk', None)
                    messages.success(request, 'Order placed! Please complete payment in your UPI App.')
                    logger.info(f"UPI app success: Order {order.order_id}")
                    return redirect('order_history')

            elif payment_mode == 'card':
                total_paise = int(total * 100)
                logger.info(f"Creating Razorpay order for cart {cart.pk}, amount {total_paise}")
                client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET_KEY))
                payment = client.order.create({'amount': total_paise, 'currency': 'INR', 'payment_capture': 1})
                razorpay_order_id = payment['id']
                request.session['razorpay_order_id'] = razorpay_order_id
                cart.razorpay_order_id = razorpay_order_id
                cart.save()
                logger.info(f"Razorpay order created: {razorpay_order_id} for cart {cart.pk}")
                messages.info(request, 'Proceed to complete card payment.')
                context['razorpay_order_id'] = razorpay_order_id

        except Exception as e:
            logger.error(f"Payment error: {str(e)}")
            messages.error(request, 'Payment failed. Please try again.')
    return render(request, 'accounts/checkout_payment.html', context)

def create_order(cart, shipping_address, payment_mode, payment_status, upi_id=None, razorpay_order_id=None):
    if razorpay_order_id:
        order_id = razorpay_order_id
    else:
        while True:
            order_id = f"order_{uuid.uuid4().hex[:8]}"
            if not Order.objects.filter(order_id=order_id).exists():
                break
    
    try:
        order = Order.objects.create(
            user=cart.user,
            order_id=order_id,
            payment_status=payment_status,
            shipping_address=shipping_address,
            payment_mode=payment_mode,
            order_total_price=cart.get_cart_total(),
            coupon=cart.coupon,
            grand_total=cart.get_cart_total_price_after_coupon(),
        )
        if upi_id:
            order.upi_id = upi_id
            order.save()
        
        cart_items = CartItem.objects.filter(cart=cart)
        for item in cart_items:
            product_name = item.sneaker_data.get('name', 'Sneaker') if item.sneaker_data else (item.product.product_name if item.product else 'Unknown')
            color_name = item.sneaker_data.get('color', 'N/A') if item.sneaker_data else (item.color_variant.color_name if item.color_variant else 'N/A')
            unit_price = item.get_product_price() / item.quantity if item.quantity > 0 else 0
            
            OrderItem.objects.create(
                order=order,
                product=item.product,
                size_variant=item.size_variant,
                color_variant=item.color_variant,
                quantity=item.quantity,
                sneaker_data=item.sneaker_data,
                product_name=product_name,
                color_name=color_name,
                product_price=item.get_product_price(),
                unit_price=unit_price
            )
        logger.info(f"Created order {order_id} with {cart_items.count()} items")
        return order
    except Exception as e:
        logger.error(f"create_order failed for {order_id}: {str(e)}")
        raise

