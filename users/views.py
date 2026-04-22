from django.contrib import messages
from django.contrib.auth import login
from django.urls import reverse_lazy
from django.views.generic import FormView, CreateView

from .forms import EmailAuthenticationForm, SignUpForm


class EmailLoginView(FormView):
    template_name = "users/login.html"
    form_class = EmailAuthenticationForm
    success_url = reverse_lazy("login")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def form_valid(self, form):
        login(self.request, form.get_user())
        messages.success(self.request, "You are now logged in.")
        return super().form_valid(form)


class SignUpView(CreateView):
    template_name = "users/signup.html"
    form_class = SignUpForm
    success_url = reverse_lazy("login")

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Account created. You can now log in.")
        return redirect(self.success_url)
