from django.urls import path

from shapranov.views import DonateView, MainPageView

urlpatterns = [
    path('', MainPageView.as_view()),
    path('smysl-zhizni-cheloveka/', DonateView.as_view()),
]
