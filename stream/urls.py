from django.urls import path

from stream.views import DonateView

urlpatterns = [
    path('', DonateView.as_view()),
    path('donate/', DonateView.as_view()),
]
