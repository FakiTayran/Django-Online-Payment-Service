# webapp/urls.py

from django.urls import path
from .views import home,register_user, login_user, logout_user,sendMoney

app_name = 'webapp'

urlpatterns = [
    path('register/', register_user, name='register'),
    path('login/', login_user, name='login'),
    path('logout/', logout_user, name='logout'),
    path('home/', home, name='my_home'),
    path('send-money/', sendMoney, name='send_money')
]
