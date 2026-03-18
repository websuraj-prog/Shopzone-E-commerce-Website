from django.db.models import Q
from django.shortcuts import render
from django.utils.text import slugify
from products.models import Product, Category, SizeVariant, Wishlist, ProductImage, ColorVariant
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
import json
import os
from django.conf import settings


# Create your views here.


def index(request):
    query = Product.objects.all().order_by('category_id')
    print(f"Initial products count: {query.count()}")
    categories = Category.objects.all()
    selected_sort = request.GET.get('sort')
    selected_category = request.GET.get('category')
    selected_brand = request.GET.get('brand')
    print(f"Selected category: {selected_category}, Selected sort: {selected_sort}, Selected brand: {selected_brand}")

    if selected_category:
        query = query.filter(category__slug=selected_category)
        print(f"Filtered products count: {query.count()}")

    if selected_sort:
        if selected_sort == 'newest':
            query = query.filter(newest_product=True).order_by('category_id')
        elif selected_sort == 'priceAsc':
            query = query.order_by('price')
        elif selected_sort == 'priceDesc':
            query = query.order_by('-price')

    # Load sneakers.json data
    sneakers_data = []
    try:
        json_path = settings.BASE_DIR / 'sneakers.json'
        with open(json_path, 'r') as f:
            sneakers_data = json.load(f)
    except Exception as e:
        print(f"Error loading sneakers.json: {e}")

    # Filter sneakers_data by selected brand if any
    if selected_brand:
        sneakers_data = [item for item in sneakers_data if item.get('brand', '').lower() == selected_brand.lower()]

    # Extract unique brands from sneakers_data for filter dropdown
    brands = list({item.get('brand', '') for item in sneakers_data if item.get('brand')})

    page = request.GET.get('page', 1)
    paginator = Paginator(query, 20)

    try:
        products = paginator.page(page)
        print(f"Products on page {page}: {products.object_list.count()}")
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    except Exception as e:
        print(e)
        products = paginator.page(1)

    context = {
        'products': products,
        'categories': categories,
        'selected_category': selected_category,
        'selected_sort': selected_sort,
        'sneakers_data': sneakers_data,
        'brands': brands,
        'selected_brand': selected_brand,
    }
    return render(request, 'home/index.html', context)


def sneaker_detail(request, name):
    from products.models import SizeVariant
    sneakers_data = []
    try:
        json_path = settings.BASE_DIR / 'sneakers.json'
        with open(json_path, 'r') as f:
            sneakers_data = json.load(f)
    except Exception as e:
        print(f"Error loading sneakers.json: {e}")

    sneaker = next((item for item in sneakers_data if item.get('name') == name), None)
    if not sneaker:
        return render(request, 'home/sneaker_not_found.html', status=404)

    sizes = ['6', '7', '8', '9', '10', '11', '12']

    return render(request, 'home/sneaker_detail.html', {'sneaker': sneaker, 'sizes': sizes})


def product_search(request):
    query = request.GET.get('q', '')

    if query:
        # Search for products that contain the query string in their product_name field
        products = Product.objects.filter(Q(product_name__icontains=query) | Q(
            product_name__istartswith=query))
    else:
        products = Product.objects.none()

    context = {'query': query, 'products': products}
    return render(request, 'home/search.html', context)


def contact(request):
    from .forms import ContactForm
    from .models import ContactMessage
    from django.core.mail import send_mail
    from django.contrib import messages
    from django.shortcuts import redirect
    from django.conf import settings

    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            name = f"{form.cleaned_data['first_name']} {form.cleaned_data['last_name']}"
            email = form.cleaned_data['email']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']

            # Save to DB
            ContactMessage.objects.create(
                name=name,
                email=email,
                subject=subject,
                message=message
            )

            # Send email
            send_mail(
                subject=f"Contact Form: {subject}",
                message=f"From: {name} ({email})\n\n{message}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=['surajvishawakarma01@gmail.com'],
                fail_silently=False,
            )

            messages.success(request, 'Thank you! Your message has been sent successfully.')
            return redirect('contact')
    else:
        form = ContactForm()

    return render(request, 'home/contact.html', {'form': form})


def about(request):
    return render(request, 'home/about.html')


def terms_and_conditions(request):
    return render(request, 'home/terms_and_conditions.html')


def privacy_policy(request):
    return render(request, 'home/privacy_policy.html')

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from products.models import Product, Category, SizeVariant, Wishlist
from django.urls import reverse
import json
import os
from django.conf import settings

@login_required
def add_sneaker_to_wishlist(request, name):
    size = request.GET.get('size')
    if not size:
        messages.warning(request, 'Please select a size before adding to wishlist!')
        return redirect(request.META.get('HTTP_REFERER'))

    # Load sneaker data
    try:
        json_path = settings.BASE_DIR / 'sneakers.json'
        with open(json_path, 'r') as f:
            sneakers_data = json.load(f)
    except Exception:
        messages.error(request, 'Sneaker data not available.')
        return redirect(reverse('index'))

    sneaker = next((item for item in sneakers_data if item.get('name') == name), None)
    if not sneaker:
        messages.error(request, 'Sneaker not found.')
        return redirect(reverse('index'))

    # Get or create SizeVariant
    size_variant, _ = SizeVariant.objects.get_or_create(size_name=size, defaults={'price': 0})

    # Get or create Category
    category, _ = Category.objects.get_or_create(
        category_name='Sneakers',
        defaults={'slug': 'sneakers'}
    )

    # Get or create Product
    product, created = Product.objects.get_or_create(
        product_name=sneaker['name'],
        defaults={
            'slug': slugify(sneaker['name']),
            'price': sneaker.get('price_inr', 0),
            'product_desription': sneaker.get('description', 'No description available.'),
            'category': category,
        }
    )

    # Handle color_variant and ProductImage
    color_str = sneaker.get('color')
    if color_str:
        color_variant, _ = ColorVariant.objects.get_or_create(
            color_name=color_str, 
            defaults={'price': 0}
        )
        product.color_variant.add(color_variant)

    if sneaker.get('image_url') and not product.product_images.exists():
        image_path = sneaker['image_url'].lstrip('media/')
        ProductImage.objects.create(
            product=product,
            image=image_path
        )

    # Add to wishlist
    wishlist_item, wishlist_created = Wishlist.objects.get_or_create(
        user=request.user,
        product=product,
        size_variant=size_variant
    )
    
    # Set sneaker data consistent with cart
    wishlist_item.sneaker_data = sneaker
    wishlist_item.save()

    if wishlist_created:
        messages.success(request, f"{sneaker['name']} (size {size}) added to your wishlist!")
    else:
        messages.info(request, f"{sneaker['name']} (size {size}) already in your wishlist!")

    return redirect(request.META.get('HTTP_REFERER'))

