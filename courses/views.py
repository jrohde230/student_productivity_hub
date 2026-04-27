from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView

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
from attachments.models import Attachment
from notes.models import Note
from tags.models import Tag

from .forms import CourseForm, EditTextbookForm, TextbookForm
from .models import Course, Textbook


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "courses/home.html"
    success_url = reverse_lazy("courses:home")

    def get_selected_course(self, courses, forced_course_id=None):
        selected = None
        if forced_course_id:
            selected = next((c for c in courses if str(c.pk) == str(forced_course_id)), None)
        if not selected:
            course_id = self.request.GET.get("course")
            if course_id:
                selected = next((c for c in courses if str(c.pk) == str(course_id)), None)
        if not selected and courses:
            selected = courses[0]
        return selected

    def get_context_data(self, **kwargs):
        forced_course_id = kwargs.pop("force_course_id", None)
        context = super().get_context_data(**kwargs)
        courses = list(
            Course.objects.filter(user=self.request.user)
            .prefetch_related("textbooks")
            .order_by("name")
        )
        selected_course = self.get_selected_course(courses, forced_course_id=forced_course_id)
        context["courses"] = courses
        context["selected_course"] = selected_course
        context["note_form"] = NoteCreateForm()
        context["note_edit_form"] = NoteEditForm()

        ct_map = allowed_content_types()
        targets = []
        for course in courses:
            targets.append(course)
            targets.extend(list(course.textbooks.all()))
        grouped_notes = notes_by_target(self.request.user, targets)
        grouped_tags = tags_by_target(self.request.user, targets)
        grouped_attachments = attachments_by_target(self.request.user, targets)

        for course in courses:
            course.notes_list = notes_for_target(grouped_notes, course)
            course.tags_list = tags_for_target(grouped_tags, course)
            course.attachments_list = attachments_for_target(grouped_attachments, course)
            for textbook in course.textbooks.all():
                textbook.notes_list = notes_for_target(grouped_notes, textbook)
                textbook.tags_list = tags_for_target(grouped_tags, textbook)
                textbook.attachments_list = attachments_for_target(grouped_attachments, textbook)

        context["ct_course_id"] = ct_map[Course].id
        context["ct_textbook_id"] = ct_map[Textbook].id
        context["tag_form"] = TagCreateForm()
        context["attachment_form"] = AttachmentUploadForm()

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

        if "textbook_edit_form" in kwargs:
            context["textbook_edit_form"] = kwargs["textbook_edit_form"]
            context["edit_textbook_id"] = kwargs.get("edit_textbook_id")
            context["textbook_edit_modal_open"] = True
        else:
            tb_edit_get = self.request.GET.get("edit_textbook")
            textbook_obj = None
            if tb_edit_get:
                textbook_obj = Textbook.objects.filter(
                    pk=tb_edit_get, course__user=self.request.user
                ).first()
            if textbook_obj:
                context["textbook_edit_form"] = EditTextbookForm(
                    prefix="edit_tb", instance=textbook_obj
                )
                context["edit_textbook_id"] = textbook_obj.pk
                context["textbook_edit_modal_open"] = True
            else:
                context["textbook_edit_form"] = EditTextbookForm(prefix="edit_tb")
                context["edit_textbook_id"] = None
                context["textbook_edit_modal_open"] = False

        context["textbook_edit_errors"] = kwargs.get("textbook_edit_errors", False)
        return context

    def post(self, request, *args, **kwargs):
        form_type = request.POST.get("form_type")
        selected_course_id = request.POST.get("course_context")
        redirect_url = self.success_url
        if selected_course_id:
            redirect_url = f"{self.success_url}?course={selected_course_id}"

        if form_type == "course":
            form = CourseForm(request.POST, prefix="add")
            if form.is_valid():
                course = form.save(commit=False)
                course.user = request.user
                course.save()
                messages.success(request, "Course added.")
                return redirect(f"{self.success_url}?course={course.pk}")
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
                return redirect(f"{self.success_url}?course={course.pk}")
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
                textbook = form.save()
                messages.success(request, "Textbook added.")
                return redirect(f"{self.success_url}?course={textbook.course_id}")
            return self.render_to_response(
                self.get_context_data(
                    textbook_form=form,
                    textbook_form_errors=True,
                    textbook_course_id=request.POST.get("course"),
                )
            )

        if form_type == "edit_textbook":
            textbook = get_object_or_404(
                Textbook.objects.select_related("course"),
                pk=request.POST.get("textbook_id"),
                course__user=request.user,
            )
            form = EditTextbookForm(
                request.POST, prefix="edit_tb", instance=textbook
            )
            if form.is_valid():
                form.save()
                messages.success(request, "Textbook updated.")
                return redirect(f"{self.success_url}?course={textbook.course_id}")
            return self.render_to_response(
                self.get_context_data(
                    textbook_edit_form=form,
                    edit_textbook_id=textbook.pk,
                    textbook_edit_errors=True,
                    force_course_id=textbook.course_id,
                )
            )

        if form_type == "delete_textbook":
            textbook = Textbook.objects.filter(
                pk=request.POST.get("textbook_id"),
                course__user=request.user,
            ).first()
            course_pk = selected_course_id or (
                textbook.course_id if textbook else None
            )
            if textbook:
                ct_tb = ContentType.objects.get_for_model(Textbook)
                oid = textbook.pk
                uid = request.user.pk
                Note.objects.filter(user_id=uid, content_type=ct_tb, object_id=oid).delete()
                Tag.objects.filter(user_id=uid, content_type=ct_tb, object_id=oid).delete()
                for att in Attachment.objects.filter(
                    user_id=uid, content_type=ct_tb, object_id=oid
                ):
                    if att.file:
                        att.file.delete(save=False)
                    att.delete()
                textbook.delete()
                messages.success(request, "Textbook removed.")
            else:
                messages.error(request, "Unable to remove that textbook.")
            if course_pk:
                return redirect(f"{self.success_url}?course={course_pk}")
            return redirect(self.success_url)

        if form_type == "add_note":
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

        if form_type == "add_tag":
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

        if form_type == "add_attachment":
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
            return redirect(redirect_url)

        if form_type == "delete_attachment":
            deleted = delete_attachment_for_user(
                user=request.user,
                attachment_id=request.POST.get("attachment_id"),
            )
            if deleted:
                messages.success(request, "Attachment removed.")
            else:
                messages.error(request, "Unable to remove attachment.")
            return redirect(redirect_url)

        if form_type == "delete_tag":
            deleted = delete_tag_for_user(user=request.user, tag_id=request.POST.get("tag_id"))
            if deleted:
                messages.success(request, "Tag removed.")
            else:
                messages.error(request, "Unable to remove that tag.")
            return redirect(redirect_url)

        if form_type == "edit_note":
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

        if form_type == "delete_note":
            deleted = delete_note_for_user(
                user=request.user,
                note_id=request.POST.get("note_id"),
            )
            if deleted:
                messages.success(request, "Note deleted.")
            else:
                messages.error(request, "Unable to delete that note.")
            return redirect(redirect_url)

        return redirect(self.success_url)
