
from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission

class User(AbstractUser):
    email = models.EmailField(unique=True)
    currency_choices = [('GBP', 'British Pounds'), ('USD', 'US Dollars'), ('EUR', 'Euros')]
    currency = models.CharField(max_length=3, choices=currency_choices, default='GBP')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=1000.00)
    groups = models.ManyToManyField(Group, related_name='webapp_users')  # related_name eklenmiş
    user_permissions = models.ManyToManyField(Permission, related_name='webapp_users_permissions')  # related_name eklenmiş

    def __str__(self):
        return self.username


class Transaction(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_transactions')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_transactions')
    timestamp = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    exchange_currency = models.CharField(max_length=15, null=True, blank=True)  # exp => "USD => GBP"
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=6, default=1)
    converted_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

# models.py

class RequestedMoney(models.Model):
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requested_money')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_money')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='GBP')
    timestamp = models.DateTimeField(auto_now_add=True)
    accepted = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.requester} requested {self.amount} from {self.receiver} on {self.timestamp}"



    def __str__(self):
        return f"{self.sender} to {self.receiver} - {self.amount} on {self.timestamp}"

