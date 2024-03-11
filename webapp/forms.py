# forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User
from django.core.exceptions import ValidationError


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2','currency','balance']
        exclude = ['balance']

class LoginForm(AuthenticationForm):
    class Meta:
        model = User
        fields = ['username', 'password']

def validate_user_exists(value):
    if not User.objects.filter(username=value).exists():
        raise ValidationError(f"User {value} does not exist.")

class SendMoneyForm(forms.Form):
    receiver = forms.CharField(max_length=150, validators=[validate_user_exists], help_text="Enter the username of the receiver.")
    amount = forms.DecimalField(max_digits=10, decimal_places=2, help_text="Enter the amount of money to send.")

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise ValidationError("The amount must be greater than 0.")
        return amount