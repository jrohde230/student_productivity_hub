from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import FormView

from .forms import AssignmentForm
from .models import Assignment


SORT_OPTIONS = {
    "due_asc": ("due_date", "assignment_name"),
    "due_desc": ("-due_date", "assignment_name"),
    "class_asc": ("class_name", "due_date"),
    "subject_asc": ("subject", "due_date"),
    "name_asc": ("assignment_name", "due_date"),
}


class HomeView(LoginRequiredMixin, FormView):
    template_name = "assignments/home.html"
    form_class = AssignmentForm
    success_url = reverse_lazy("assignments:home")

    def get_sort_key(self):
        sort = self.request.GET.get("sort", "due_asc")
        if sort not in SORT_OPTIONS:
            return "due_asc"
        return sort

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sort_key = self.get_sort_key()
        context["selected_sort"] = sort_key
        context["assignments"] = Assignment.objects.filter(user=self.request.user).order_by(*SORT_OPTIONS[sort_key])
        return context

    def form_valid(self, form):
        assignment = form.save(commit=False)
        assignment.user = self.request.user
        assignment.save()
        messages.success(self.request, "Assignment added.")
        return super().form_valid(form)
