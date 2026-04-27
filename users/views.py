from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, FormView, TemplateView

from .forms import EmailAuthenticationForm, SignUpForm, UsernameChangeForm


class EmailLoginView(FormView):
    template_name = "users/login.html"
    form_class = EmailAuthenticationForm
    success_url = reverse_lazy("dashboard")

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


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "users/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if "username_form" in kwargs:
            context["username_form"] = kwargs["username_form"]
        else:
            context["username_form"] = UsernameChangeForm(instance=user)
        if "password_form" in kwargs:
            context["password_form"] = kwargs["password_form"]
        else:
            context["password_form"] = PasswordChangeForm(user=user)
        return context

    def post(self, request, *args, **kwargs):
        form_type = request.POST.get("form_type")
        user = request.user

        if form_type == "password":
            form = PasswordChangeForm(user=user, data=request.POST)
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Your password has been updated.")
                return redirect("profile")
            messages.error(request, "Please fix the errors below.")
            return self.render_to_response(
                self.get_context_data(password_form=form)
            )

        form = UsernameChangeForm(data=request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your username has been updated.")
            return redirect("profile")
        messages.error(request, "Please fix the errors below.")
        return self.render_to_response(self.get_context_data(username_form=form))
