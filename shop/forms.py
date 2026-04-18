from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Customer, Review

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=20, required=True)
    address = forms.CharField(widget=forms.Textarea, required=False)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'password1', 'password2']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            Customer.objects.create(
                user=user,
                name=user.username,
                email=user.email,
                phone=self.cleaned_data['phone'],
                address=self.cleaned_data.get('address', '')
            )
        return user

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        
from django import forms
from .models import OfflineSale, Product

class OfflineSaleForm(forms.ModelForm):
    class Meta:
        model = OfflineSale
        fields = ['product', 'quantity', 'cost_price', 'price', 'received_amount', 'shop_name', 'comments']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control', 'id': 'product-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'id': 'quantity', 'min': '1'}),
            'cost_price': forms.NumberInput(attrs={'class': 'form-control', 'id': 'cost-price', 'step': '0.01', 'readonly': 'readonly'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'id': 'sale-price', 'step': '0.01', 'readonly': 'readonly'}),
            'received_amount': forms.NumberInput(attrs={'class': 'form-control', 'id': 'received-amount', 'step': '0.01'}),
            'shop_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Shop Name'}),
            'comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Notes'}),
        }