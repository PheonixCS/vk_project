# Create your views here.
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic

from posting.models import Group


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
