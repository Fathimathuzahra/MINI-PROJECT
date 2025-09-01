# canteen_app/forms.py
from django import forms
from django.contrib.auth import get_user_model
from .models import MenuItem

from django.contrib.auth.forms import AuthenticationForm
User = get_user_model()


class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")
    role = forms.ChoiceField(choices=User.ROLE_CHOICES)

    class Meta:
        model = User
        fields = ['username', 'phone', 'email', 'role']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


# -------------------
# Login Form
# -------------------
class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )


# -------------------
# Menu Form (Staff/Admin)
# -------------------
# canteen_app/forms.py
from django import forms
from .models import MenuItem

class MenuForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = [
            "name",
            "description",
            "price",
            "category",
            "image",
            "available",
        ]


# -------------------
# Order Form (Student Checkout)
# -------------------
class OrderForm(forms.Form):
    items = forms.ModelMultipleChoiceField(
        queryset=MenuItem.objects.filter(available=True),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Select Menu Items"
    )
