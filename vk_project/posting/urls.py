from django.urls import path

from .views import GroupView, IndexView, UserView, UsersView, ActivateView

app_name = 'posting'
urlpatterns = [
    path('', IndexView.as_view(), name='posting'),
    path('group/<int:pk>/', GroupView.as_view(), name='groups'),
    path('users/', UsersView.as_view(), name='users'),
    path('users/<int:pk>', UserView.as_view(), name='user'),
    path('users/activate/<int:pk>', ActivateView.as_view(), name='activate')
]
