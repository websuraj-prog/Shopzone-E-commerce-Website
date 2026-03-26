from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from accounts.models import Profile
from shopzone.home.models import ShippingAddress


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_image', 'bio']


class UserUpdateForm(forms.ModelForm):
    age = forms.IntegerField(required=False, min_value=13, label='Age')

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']


class ShippingAddressForm(forms.ModelForm):
    class Meta:
        model = ShippingAddress
        fields = '__all__'
        exclude = ['user']


class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label="Current password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
    new_password1 = forms.CharField(
        label="New password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
    new_password2 = forms.CharField(
        label="New password confirmation",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )


class UPIForm(forms.Form):
    upi_id = forms.CharField(
        max_length=100, 
        label='UPI ID (e.g., yourname@paytm)',
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'yourname@paytm'
        }),
        required=False
    )
