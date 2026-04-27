from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView

from checklists.forms import ChecklistItemCreateForm
from checklists.services import (
    create_item_for_target,
    delete_item_for_user,
    items_by_target,
    items_for_target,
    set_item_done_for_user,
)
from attachments.forms import AttachmentUploadForm
from attachments.services import (
    attachments_by_target,
    attachments_for_target,
    create_attachment_for_target,
    delete_attachment_for_user,
)
from notes.forms import NoteCreateForm, NoteEditForm
from notes.services import (
    allowed_content_types,
    create_note_for_target,
    delete_note_for_user,
    notes_by_target,
    notes_for_target,
    update_note_for_user,
)
from tags.forms import TagCreateForm
from tags.services import (
    create_tag_for_target,
    delete_tag_for_user,
    tags_by_target,
    tags_for_target,
)
from .forms import AssignmentForm, EditAssignmentForm
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

    def get_selected_assignment(self, assignments):
        assignment_id = self.request.GET.get("assignment")
        selected = None
        if assignment_id:
            selected = next((a for a in assignments if str(a.pk) == str(assignment_id)), None)
        if not selected and assignments:
            selected = assignments[0]
        return selected

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sort_key = self.get_sort_key()
        assignments = list(Assignment.objects.filter(user=self.request.user).order_by(*SORT_OPTIONS[sort_key]))
        ct_map = allowed_content_types()
        grouped_notes = notes_by_target(self.request.user, assignments)
        grouped_tags = tags_by_target(self.request.user, assignments)
        grouped_items = items_by_target(self.request.user, assignments)
        grouped_attachments = attachments_by_target(self.request.user, assignments)
        for assignment in assignments:
            assignment.notes_list = notes_for_target(grouped_notes, assignment)
            assignment.tags_list = tags_for_target(grouped_tags, assignment)
            assignment.checklist_items = items_for_target(grouped_items, assignment)
            assignment.attachments_list = attachments_for_target(grouped_attachments, assignment)
        selected_assignment = self.get_selected_assignment(assignments)

        context["selected_sort"] = sort_key
        context["assignments"] = assignments
        context["selected_assignment"] = selected_assignment
        context["ct_assignment_id"] = ct_map[Assignment].id
        context["note_form"] = NoteCreateForm()
        context["note_edit_form"] = NoteEditForm()
        context["tag_form"] = TagCreateForm()
        context["checklist_form"] = ChecklistItemCreateForm()
        context["attachment_form"] = AttachmentUploadForm()
        context["edit_assignment_form"] = kwargs.get(
            "edit_assignment_form",
            EditAssignmentForm(prefix="editassign", user=self.request.user),
        )
        context["open_edit_assignment_modal"] = kwargs.get("open_edit_assignment_modal", False)
        return context

    def form_valid(self, form):
        assignment = form.save(commit=False)
        assignment.user = self.request.user
        assignment.save()
        messages.success(self.request, "Assignment added.")
        return redirect(f"{self.success_url}?assignment={assignment.pk}")

    def post(self, request, *args, **kwargs):
        selected_assignment_id = request.POST.get("assignment_context")
        redirect_url = self.success_url
        if selected_assignment_id:
            redirect_url = f"{self.success_url}?assignment={selected_assignment_id}"

        if request.POST.get("form_type") == "edit_assignment":
            form = EditAssignmentForm(request.POST, prefix="editassign", user=request.user)
            if form.is_valid():
                assignment = form.save()
                messages.success(request, "Assignment updated.")
                return redirect(f"{self.success_url}?assignment={assignment.pk}")
            messages.error(request, "Unable to update assignment.")
            return self.render_to_response(
                self.get_context_data(
                    edit_assignment_form=form,
                    open_edit_assignment_modal=True,
                )
            )

        if request.POST.get("form_type") == "delete_assignment":
            assignment = Assignment.objects.filter(
                pk=request.POST.get("assignment_id"),
                user=request.user,
            ).first()
            if assignment:
                if str(assignment.pk) == str(selected_assignment_id):
                    selected_assignment_id = None
                assignment.delete()
                messages.success(request, "Assignment deleted.")
            else:
                messages.error(request, "Unable to delete that assignment.")
            return redirect(self.success_url)

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
            return redirect(redirect_url)
        if request.POST.get("form_type") == "add_checklist_item":
            form = ChecklistItemCreateForm(request.POST)
            if form.is_valid():
                item = create_item_for_target(
                    user=request.user,
                    content_type_id=request.POST.get("content_type_id"),
                    object_id=request.POST.get("object_id"),
                    text=form.cleaned_data["text"],
                )
                if item:
                    messages.success(request, "Checklist item added.")
                else:
                    messages.error(request, "Unable to add checklist item.")
            else:
                messages.error(request, "Checklist item cannot be empty.")
            return redirect(redirect_url)
        if request.POST.get("form_type") == "add_attachment":
            form = AttachmentUploadForm(request.POST, request.FILES)
            if form.is_valid():
                attachment = create_attachment_for_target(
                    user=request.user,
                    content_type_id=request.POST.get("content_type_id"),
                    object_id=request.POST.get("object_id"),
                    file_obj=form.cleaned_data["file"],
                )
                if attachment:
                    messages.success(request, "Attachment uploaded.")
                else:
                    messages.error(request, "Unable to upload attachment.")
            else:
                messages.error(request, "Please choose a file to upload.")
            return redirect(self.success_url)
        if request.POST.get("form_type") == "delete_attachment":
            deleted = delete_attachment_for_user(
                user=request.user,
                attachment_id=request.POST.get("attachment_id"),
            )
            if deleted:
                messages.success(request, "Attachment removed.")
            else:
                messages.error(request, "Unable to remove attachment.")
            return redirect(redirect_url)
        if request.POST.get("form_type") == "toggle_checklist_item":
            item = set_item_done_for_user(
                user=request.user,
                item_id=request.POST.get("item_id"),
                is_done=request.POST.get("is_done") == "1",
            )
            if not item:
                messages.error(request, "Unable to update checklist item.")
            return redirect(redirect_url)
        if request.POST.get("form_type") == "delete_checklist_item":
            deleted = delete_item_for_user(user=request.user, item_id=request.POST.get("item_id"))
            if deleted:
                messages.success(request, "Checklist item removed.")
            else:
                messages.error(request, "Unable to remove checklist item.")
            return redirect(redirect_url)
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
            return redirect(redirect_url)
        if request.POST.get("form_type") == "delete_note":
            deleted = delete_note_for_user(
                user=request.user,
                note_id=request.POST.get("note_id"),
            )
            if deleted:
                messages.success(request, "Note deleted.")
            else:
                messages.error(request, "Unable to delete that note.")
            return redirect(redirect_url)
        if request.POST.get("form_type") == "add_tag":
            form = TagCreateForm(request.POST)
            if form.is_valid():
                tag = create_tag_for_target(
                    user=request.user,
                    content_type_id=request.POST.get("content_type_id"),
                    object_id=request.POST.get("object_id"),
                    label=form.cleaned_data["label"],
                )
                if tag:
                    messages.success(request, "Tag added.")
                else:
                    messages.error(request, "Unable to attach tag to that item.")
            else:
                messages.error(request, "Tag cannot be empty.")
            return redirect(redirect_url)
        if request.POST.get("form_type") == "delete_tag":
            deleted = delete_tag_for_user(user=request.user, tag_id=request.POST.get("tag_id"))
            if deleted:
                messages.success(request, "Tag removed.")
            else:
                messages.error(request, "Unable to remove that tag.")
            return redirect(redirect_url)
        return super().post(request, *args, **kwargs)
