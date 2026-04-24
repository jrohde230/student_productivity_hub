from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from .forms import CourseForm, TextbookForm
from .models import Course


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "courses/home.html"
    success_url = reverse_lazy("courses:home")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["courses"] = (
            Course.objects.filter(user=self.request.user)
            .prefetch_related("textbooks")
            .order_by("name")
        )

        if "course_form" in kwargs:
            context["course_form"] = kwargs["course_form"]
        else:
            context["course_form"] = CourseForm(prefix="add")

        if "course_edit_form" in kwargs:
            context["course_edit_form"] = kwargs["course_edit_form"]
            context["edit_course_id"] = kwargs.get("edit_course_id")
            context["course_edit_modal_open"] = True
        else:
            edit_get = self.request.GET.get("edit")
            course = None
            if edit_get:
                course = Course.objects.filter(pk=edit_get, user=self.request.user).first()
            if course:
                context["course_edit_form"] = CourseForm(prefix="edit", instance=course)
                context["edit_course_id"] = course.pk
                context["course_edit_modal_open"] = True
            else:
                context["course_edit_form"] = CourseForm(prefix="edit")
                context["edit_course_id"] = None
                context["course_edit_modal_open"] = False

        if "textbook_form" in kwargs:
            context["textbook_form"] = kwargs["textbook_form"]
        else:
            context["textbook_form"] = TextbookForm(user=self.request.user)

        context["course_form_errors"] = kwargs.get("course_form_errors", False)
        context["course_edit_errors"] = kwargs.get("course_edit_errors", False)
        context["textbook_form_errors"] = kwargs.get("textbook_form_errors", False)
        context["textbook_course_id"] = kwargs.get("textbook_course_id")
        return context

    def post(self, request, *args, **kwargs):
        form_type = request.POST.get("form_type")

        if form_type == "course":
            form = CourseForm(request.POST, prefix="add")
            if form.is_valid():
                course = form.save(commit=False)
                course.user = request.user
                course.save()
                messages.success(request, "Course added.")
                return redirect(self.success_url)
            return self.render_to_response(
                self.get_context_data(course_form=form, course_form_errors=True)
            )

        if form_type == "edit_course":
            pk = request.POST.get("course_id")
            course = get_object_or_404(Course, pk=pk, user=request.user)
            form = CourseForm(request.POST, prefix="edit", instance=course)
            if form.is_valid():
                form.save()
                messages.success(request, "Course updated.")
                return redirect(self.success_url)
            return self.render_to_response(
                self.get_context_data(
                    course_edit_form=form,
                    edit_course_id=course.pk,
                    course_edit_errors=True,
                )
            )

        if form_type == "textbook":
            form = TextbookForm(request.POST, user=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, "Textbook added.")
                return redirect(self.success_url)
            return self.render_to_response(
                self.get_context_data(
                    textbook_form=form,
                    textbook_form_errors=True,
                    textbook_course_id=request.POST.get("course"),
                )
            )

        return redirect(self.success_url)
