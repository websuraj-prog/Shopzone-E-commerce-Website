from django.urls import path
from home.views import *
from accounts.views import add_sneaker_to_cart, buy_sneaker_now

urlpatterns = [
    path('', index, name="index"),
    path('search/', product_search, name='product_search'),
    path('contact/', contact, name='contact'),
    path('about/', about, name='about'),
    path('terms-and-conditions/', terms_and_conditions, name='terms-and-conditions'),
    path('privacy-policy/', privacy_policy, name='privacy-policy'),
    path('sneaker/add-to-cart/<str:name>/', add_sneaker_to_cart, name='add_sneaker_to_cart'),
    path('sneaker/buy-now/<str:name>/', buy_sneaker_now, name='buy_sneaker_now'),
    path('sneaker/add-to-wishlist/<str:name>/', add_sneaker_to_wishlist, name='add_sneaker_to_wishlist'),
    path('sneaker/<str:name>/', sneaker_detail, name='sneaker_detail'),
]
