from django.shortcuts import redirect

from django.views import View

DONATE_URL = 'https://www.donationalerts.com/r/pavelshapranov'


class DonateView(View):
    def get(self, request):
        return redirect(DONATE_URL)
