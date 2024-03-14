from django.urls import path
from .views import home, register_user, login_user, logout_user, send_money, request_money, accept_request, deny_request,get_user_transactions,add_admin

app_name = 'webapp'

urlpatterns = [
    path('register/', register_user, name='register'),
    path('login/', login_user, name='login'),
    path('logout/', logout_user, name='logout'),
    path('home/', home, name='my_home'),
    path('send-money/', send_money, name='send_money'),
    path('request-money/', request_money, name='request_money'),
    path('accept-request/<int:request_id>/', accept_request, name='accept_request'),
    path('deny-request/<int:request_id>/', deny_request, name='deny_request'),  # Deny request URL
    path('get_user_transactions/<int:user_id>/', get_user_transactions, name='get_user_transactions'),
    path('add-admin/', add_admin, name='add_admin'),

]
