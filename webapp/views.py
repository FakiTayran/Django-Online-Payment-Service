# views.py
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.db import transaction
from decimal import Decimal
from django.db.models import Q
from .models import User, Transaction, RequestedMoney
from .forms import RegisterForm, LoginForm, SendMoneyForm, RequestedMoneyForm
import requests

import logging

logger = logging.getLogger(__name__)

def home(request):
    logger.info(f"Request user type: {type(request.user)}")  # Debug log
    logger.info(f"Request user: {request.user}")  # Debug log

    if not isinstance(request.user, User):
        raise ValueError("request.user is not an instance of your custom User model.")

    if request.user.is_superuser:
        transactions = Transaction.objects.all().order_by('-timestamp')
        users = User.objects.all()
        context = {'transactions': transactions, 'users': users}
        return render(request, 'admin_home.html',context)

    user_balance = request.user.balance
    user_currency = request.user.currency
    logger.info(f"User balance: {user_balance}")

    transactions = Transaction.objects.filter(Q(sender=request.user) | Q(receiver=request.user)).order_by('-timestamp')
    unseen_requests = RequestedMoney.objects.filter(receiver=request.user, completed=False).order_by('-timestamp')
    sent_money_requests = RequestedMoney.objects.filter(requester=request.user).order_by('-timestamp')

    context = {'user_balance': user_balance, 'user_currency': user_currency, 'transactions': transactions, 'notifications': unseen_requests, 'sent_money_requests': sent_money_requests}
    return render(request, 'home.html', context)

@login_required
@transaction.atomic
def send_money(request):
    if request.method == 'POST':
        form = SendMoneyForm(request.POST)
        if form.is_valid():
            receiver_username = form.cleaned_data['receiver']
            amount = form.cleaned_data['amount']

            try:
                sender_currency = request.user.currency
                receiver = User.objects.get(username=receiver_username)
                receiver_currency = receiver.currency

                # Get exchange rate
                exchange_rate = get_exchange_rate(sender_currency, receiver_currency)
                exchange_currency_format = f"{sender_currency} => {receiver_currency}"

                if exchange_rate:
                    converted_amount = amount * exchange_rate

                    if request.user.balance >= amount:
                        request.user.balance -= amount
                        receiver.balance += converted_amount
                        request.user.save()
                        receiver.save()

                        Transaction.objects.create(sender=request.user, receiver=receiver, amount=amount,
                                                   exchange_currency=exchange_currency_format,
                                                   exchange_rate=exchange_rate, converted_amount=converted_amount)
                        messages.success(request, 'Money sent successfully.')
                        logger.info(
                            f"Money transfer successful: {amount} {sender_currency} from {request.user.username} to {receiver.username}")
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
                logger.exception(f"Error in send_money: {str(e)}")

            return redirect('webapp:my_home')
    else:
        form = SendMoneyForm()

    transactions = Transaction.objects.filter(sender=request.user).order_by('-timestamp')
    context = {'form': form, 'transactions': transactions}
    return render(request, 'home.html', context)


@login_required
def request_money(request):
    logger.info(f"Money requested function triggered.")  # Debug log
    if request.method == 'POST':
        form = RequestedMoneyForm(request.POST)
        if form.is_valid():
            receiver_username = form.cleaned_data['receiver']
            amount = form.cleaned_data['amount']
            logger.info(f"Money requested function inside if.")
            try:
                receiver = User.objects.get(username=receiver_username)
                RequestedMoney.objects.create(requester=request.user, receiver=receiver, amount=amount,currency=request.user.currency)
                messages.success(request, 'Money request sent successfully.')
                return redirect('webapp:my_home')
            except User.DoesNotExist:
                messages.error(request, 'Receiver not found.')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
                    logger.info(field + error)  # Debug log
    else:
        form = RequestedMoneyForm()

    return render(request, 'home.html', {'form': form})



@login_required
@transaction.atomic
def accept_request(request, request_id):
    requested_money = get_object_or_404(RequestedMoney, id=request_id, receiver=request.user, completed=False)

    if request.method == 'POST':


        sender = requested_money.requester
        amount = requested_money.amount

        exchange_rate = get_exchange_rate(sender.currency, request.user.currency)

        if exchange_rate is not None:
            converted_amount = amount * exchange_rate

            if request.user.balance >= converted_amount:
                request.user.balance -= converted_amount
                sender.balance += amount
                request.user.save()
                sender.save()

                Transaction.objects.create(sender=request.user, receiver=sender, amount=amount,
                                               exchange_currency=f"{sender.currency} => {request.user.currency}",
                                               exchange_rate=exchange_rate, converted_amount=converted_amount)

                requested_money.accepted = True
                requested_money.completed = True
                requested_money.save()

                messages.success(request, 'Request accepted successfully.')
                return redirect('webapp:my_home')
            else:
                messages.error(request, 'Insufficient balance.')
        else:
            messages.error(request, 'Exchange rate not found.')

    return render(request, 'home.html')

@login_required
@transaction.atomic
def deny_request(request, request_id):
    requested_money = get_object_or_404(RequestedMoney, id=request_id, receiver=request.user, completed=False)

    if request.method == 'POST':
        requested_money.accepted = False
        requested_money.completed = True
        requested_money.save()

        messages.success(request, 'Request denied successfully.')
        return redirect('webapp:my_home')

    context = {'requested_money': requested_money}
    return render(request, 'home.html', {context})

def get_exchange_rate(base_currency, target_currency):
    try:
        response = requests.get(f"https://open.er-api.com/v6/latest/{base_currency}")
        data = response.json()

        if data['result'] == 'success':
            rates = data['rates']
            exchange_rate = rates.get(target_currency)

            if exchange_rate is not None:
                exchange_rate = Decimal(str(exchange_rate))
                return exchange_rate
            else:
                logger.error(f"Exchange rate not found for {base_currency} to {target_currency}.")
                return None
        else:
            logger.error(f"Failed to retrieve exchange rate for {base_currency} to {target_currency}.")
            return None
    except Exception as e:
        logger.exception(f"Error in get_exchange_rate: {str(e)}")
        return None


def get_user_transactions(request, user_id):
    if request.user.is_authenticated and request.user.is_superuser:
        user = User.objects.filter(pk=user_id).first()
        if user:
            transactions = Transaction.objects.filter(Q(sender=user) | Q(receiver=user))
            transaction_data = [{
                'sender': transaction.sender.username,
                'receiver': transaction.receiver.username,
                'amount': transaction.amount,
                'timestamp': transaction.timestamp,
                'exchange_currency':transaction.exchange_currency,
                'converted_amount':transaction.converted_amount
            } for transaction in transactions]
            return JsonResponse(transaction_data, safe=False)
    return JsonResponse({'error': 'Unauthorized'}, status=403)

def add_admin(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_staff = True
            user.is_superuser = True
            user.save()
            messages.success(request, 'Admin user created successfully.')
            return redirect('webapp:my_home')
        else:
            messages.error(request, 'Error creating admin user.')
    else:
        form = RegisterForm()
    return render(request, 'add_admin.html', {'form': form})

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
