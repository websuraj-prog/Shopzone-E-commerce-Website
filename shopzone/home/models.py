from django.contrib.auth.models import User
from shopzone.base.models import BaseModel
from django.urls import reverse
from django.db import models
from django import forms
from django_countries.fields import CountryField
from django.utils import timezone

# Existing models
class ShippingAddress(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    flat_house_building_name = models.CharField(max_length=200, verbose_name="Flat/House/Building name")
    area_sector_locality = models.CharField(max_length=100, verbose_name="Area / Sector / Locality")
    zip_code = models.CharField(max_length=30)
    city = models.CharField(max_length=50)
    country = CountryField()
    phone = models.CharField(max_length=30)
    current_address = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.flat_house_building_name}, {self.area_sector_locality}, {self.city}, {self.country}, {self.zip_code}, {self.phone}'

    def get_absolute_url(self):
        return reverse('shipping-address')

class ShippingAddressForm(forms.ModelForm):
    save_address = forms.BooleanField(required=False, label='Save the billing address')

    class Meta:
        model = ShippingAddress
        fields = [
            'first_name',
            'last_name',
            'flat_house_building_name',
            'area_sector_locality',
            'zip_code',
            'city',
            'country',
            'phone'
        ]

# New Contact Message model
class ContactMessage(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} - {self.subject}'

