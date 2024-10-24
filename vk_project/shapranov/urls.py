from django.urls import path, include

from shapranov.views import DonateView, MainPageView, DocsView

urlpatterns = [
    path('', MainPageView.as_view(), name='shapranov'),
    path('smysl-zhizni-cheloveka/', DonateView.as_view()),
    path('docs', DocsView.as_view(), name='docs'),
    path('users/', include("django.contrib.auth.urls")),
]
