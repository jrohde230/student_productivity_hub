from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import RedirectView


class HomeView(LoginRequiredMixin, RedirectView):
    pattern_name = "dashboard"
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        year = self.request.GET.get("year")
        month = self.request.GET.get("month")
        base_url = reverse_lazy(self.pattern_name)
        query_parts = []
        if year:
            query_parts.append(f"year={year}")
        if month:
            query_parts.append(f"month={month}")
        if query_parts:
            return f"{base_url}?{'&'.join(query_parts)}"
        return base_url
