# Create your views here.
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.views import generic

from posting.models import Group, User, AuthCode
from services.vk.core import create_vk_session_using_login_password


class IndexView(LoginRequiredMixin, generic.ListView):
    raise_exception = True
    template_name = 'posting/index.html'
    context_object_name = 'groups'

    def get_queryset(self):
        return Group.objects.all()


class GroupView(LoginRequiredMixin, generic.DetailView):
    raise_exception = True
    template_name = 'posting/group.html'

    model = Group


class UsersView(LoginRequiredMixin, generic.ListView):
    raise_exception = True
    template_name = 'posting/users.html'
    context_object_name = 'users'

    def get_queryset(self):
        return User.objects.all()


class UserView(LoginRequiredMixin, generic.DetailView):
    raise_exception = True
    template_name = 'posting/user.html'

    model = User

    def post(self, request, *args, **kwargs):
        print(request)
        print(dict(request.POST))

        AuthCode.objects.create(
            code=request.POST.get('code'),
            user_id=int(request.POST.get('user_pk'))
        )

        return HttpResponseRedirect(self.request.path_info)


class ActivateView(LoginRequiredMixin, generic.View):
    raise_exception = True

    def post(self, request, *args, **kwargs):
        print(request)
        user = User.objects.get(pk=int(request.POST.get('user_pk')[0]))
        create_vk_session_using_login_password(user.login, user.password, user.app_id)

        return HttpResponse(201)
