# views.py

from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse
from django.shortcuts import render, redirect
from webapp.forms import RegisterForm, LoginForm,SendMoneyForm
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from  django.db import transaction
from decimal import Decimal
from django.db.models import Q


import requests


# views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import User,Transaction

import logging

logger = logging.getLogger(__name__)

@login_required
def home(request):
    logger.info(f"Request user type: {type(request.user)}")  # Debug log
    logger.info(f"Request user: {request.user}")  # Debug log

    if not isinstance(request.user, User):
        raise ValueError("request.user is not an instance of your custom User model.")

    user_balance = request.user.balance
    user_currency = request.user.currency
    logger.info(f"User balance: {user_balance}")

    transactions = Transaction.objects.filter(Q(sender=request.user) | Q(receiver=request.user)).order_by('-timestamp')

    context = {'user_balance': user_balance, 'user_currency':user_currency,'transactions': transactions}
    return render(request, 'home.html', context)

@login_required
@transaction.atomic
def sendMoney(request):
    if request.method == 'POST':
        form = SendMoneyForm(request.POST)
        if form.is_valid():
            receiver_username = form.cleaned_data['receiver']
            amount = form.cleaned_data['amount']

            try:
                sender_currency = request.user.currency
                receiver = User.objects.get(username=receiver_username)
                receiver_currency = receiver.currency

                if sender_currency == receiver_currency:
                    # If the currencies are the same, the exchange rate is considered 1.
                    exchange_rate = 1
                    logger.info(f"Same currency transfer: {sender_currency} to {receiver_currency}, rate=1")
                else:
                    # Get exchange rates from API for different currencies
                    response = requests.get(f"https://open.er-api.com/v6/latest/{sender_currency}")
                    data = response.json()

                    if data['result'] == 'success':
                        rates = data['rates']
                        exchange_rate = rates.get(receiver_currency)
                        logger.info(f"Exchange rate from {sender_currency} to {receiver_currency}: {exchange_rate}")
                    else:
                        exchange_rate = None
                        logger.error("Failed to retrieve exchange rate.")

                exchange_currency_format = f"{sender_currency} => {receiver_currency}"

                if exchange_rate:
                    exchange_rate_decimal = Decimal(str(exchange_rate))
                    converted_amount = amount * exchange_rate_decimal

                    if request.user.balance >= amount:
                        request.user.balance -= amount
                        receiver.balance += converted_amount
                        request.user.save()
                        receiver.save()

                        Transaction.objects.create(sender=request.user, receiver=receiver, amount=amount,exchange_currency = exchange_currency_format,exchange_rate=exchange_rate_decimal,converted_amount = converted_amount)
                        messages.success(request, 'Money sent successfully.')
                        logger.info(f"Money transfer successful: {amount} {sender_currency} from {request.user.username} to {receiver.username}")
                    else:
                        messages.error(request, 'Insufficient balance.')
                        logger.warning(f"Insufficient balance for {request.user.username}.")
                else:
                    messages.error(request, 'Exchange rate not found.')
                    logger.error(f"Exchange rate not found from {sender_currency} to {receiver_currency}.")

            except User.DoesNotExist:
                messages.error(request, 'Receiver not found.')
                logger.error(f"Receiver not found: {receiver_username}")
            except Exception as e:
                messages.error(request, str(e))
                logger.exception(f"Error in sendMoney: {str(e)}")

            return redirect('webapp:my_home')
    else:
        form = SendMoneyForm()

    transactions = Transaction.objects.filter(sender=request.user).order_by('-timestamp')
    context = {'form': form, 'transactions': transactions}
    return render(request, 'home.html', context)




def register_user(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Registration successful.")
            return redirect("webapp:login")
        else:
            messages.error(request, "Unsuccessful registration. Invalid information.")
    else:
        form = RegisterForm()
    return render(request, "register.html", {"register_user": form})

def login_user(request):
    if request.method == "POST":
        form = LoginForm(request, request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"You are now logged in as {username}.")
                return redirect('webapp:my_home')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()
    return render(request, "login.html", {"login_user": form})

def logout_user(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect("webapp:login")

