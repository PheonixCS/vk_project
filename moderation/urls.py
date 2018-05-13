from django.urls import path

from moderation import views

urlpatterns = [
    path('webhook', views.webhook, name='webhook'),
]