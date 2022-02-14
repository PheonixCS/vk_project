# Create your views here.
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.views import generic

from posting.models import Group, User, AuthCode
from services.vk.core import activate_two_factor


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

        result = AuthCode.objects.create(
            code=request.POST.get('code'),
            user_id=int(request.POST.get('user_pk'))
        )

        return JsonResponse(data={'result': result.pk})


class ActivateView(LoginRequiredMixin, generic.View):
    raise_exception = True

    def post(self, request, *args, **kwargs):
        print(request)
        user = User.objects.get(pk=int(request.POST.get('user_pk')[0]))
        result = activate_two_factor(user)

        return JsonResponse(data={'result': result})
