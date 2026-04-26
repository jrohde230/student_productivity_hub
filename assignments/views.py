from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView

from notes.forms import NoteCreateForm, NoteEditForm
from notes.services import (
    allowed_content_types,
    create_note_for_target,
    delete_note_for_user,
    notes_by_target,
    notes_for_target,
    update_note_for_user,
)
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
        assignments = list(Assignment.objects.filter(user=self.request.user).order_by(*SORT_OPTIONS[sort_key]))
        ct_map = allowed_content_types()
        grouped_notes = notes_by_target(self.request.user, assignments)
        for assignment in assignments:
            assignment.notes_list = notes_for_target(grouped_notes, assignment)

        context["selected_sort"] = sort_key
        context["assignments"] = assignments
        context["ct_assignment_id"] = ct_map[Assignment].id
        context["note_form"] = NoteCreateForm()
        context["note_edit_form"] = NoteEditForm()
        return context

    def form_valid(self, form):
        assignment = form.save(commit=False)
        assignment.user = self.request.user
        assignment.save()
        messages.success(self.request, "Assignment added.")
        return super().form_valid(form)

    def post(self, request, *args, **kwargs):
        if request.POST.get("form_type") == "add_note":
            form = NoteCreateForm(request.POST)
            if form.is_valid():
                note = create_note_for_target(
                    user=request.user,
                    content_type_id=request.POST.get("content_type_id"),
                    object_id=request.POST.get("object_id"),
                    body=form.cleaned_data["body"],
                )
                if note:
                    messages.success(request, "Note added.")
                else:
                    messages.error(request, "Unable to attach note to that item.")
            else:
                messages.error(request, "Note cannot be empty.")
            return redirect(self.success_url)
        if request.POST.get("form_type") == "edit_note":
            form = NoteEditForm(request.POST)
            if form.is_valid():
                note = update_note_for_user(
                    user=request.user,
                    note_id=form.cleaned_data["note_id"],
                    body=form.cleaned_data["body"],
                )
                if note:
                    messages.success(request, "Note updated.")
                else:
                    messages.error(request, "Unable to update that note.")
            else:
                messages.error(request, "Note update failed.")
            return redirect(self.success_url)
        if request.POST.get("form_type") == "delete_note":
            deleted = delete_note_for_user(
                user=request.user,
                note_id=request.POST.get("note_id"),
            )
            if deleted:
                messages.success(request, "Note deleted.")
            else:
                messages.error(request, "Unable to delete that note.")
            return redirect(self.success_url)
        return super().post(request, *args, **kwargs)
