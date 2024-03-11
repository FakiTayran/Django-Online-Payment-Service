from django.contrib import admin
from django.urls import path, include
from webapp import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path('webapp/', include('webapp.urls')),
    path('', views.login_user, name='login_user'),
]

