from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import FormView

from .forms import CourseLinkForm
from .models import CourseLink


class HomeView(LoginRequiredMixin, FormView):
    template_name = "courses/home.html"
    form_class = CourseLinkForm
    success_url = reverse_lazy("courses:home")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["course_links"] = CourseLink.objects.filter(user=self.request.user)
        return context

    def form_valid(self, form):
        course_link = form.save(commit=False)
        course_link.user = self.request.user
        course_link.save()
        messages.success(self.request, "Link saved successfully.")
        return super().form_valid(form)
