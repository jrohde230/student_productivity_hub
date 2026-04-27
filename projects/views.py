from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView

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
from .forms import (
    CollaboratorInviteForm,
    EditProjectForm,
    EditProjectLinkForm,
    ProjectCommentForm,
    ProjectForm,
    ProjectLinkForm,
)
from .models import Project, ProjectCollaborator, ProjectComment, ProjectLink

User = get_user_model()


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'projects/home.html'
    success_url = reverse_lazy('projects:home')

    def accessible_projects_qs(self):
        return Project.objects.filter(
            Q(user=self.request.user) | Q(collaborators__user=self.request.user)
        ).distinct()

    def can_edit_project(self, project):
        return project and (
            project.user_id == self.request.user.id
            or project.collaborators.filter(user=self.request.user).exists()
        )

    def can_manage_collaborators(self, project):
        return project and project.user_id == self.request.user.id

    def get_selected_project(self):
        project_id = self.request.GET.get('project')
        projects = self.accessible_projects_qs()
        selected = None
        if project_id:
            selected = projects.filter(pk=project_id).first()
        if not selected:
            selected = projects.order_by('name').first()
        return selected

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        projects = self.accessible_projects_qs().order_by('name')
        selected_project = kwargs.get('selected_project')
        if selected_project is None:
            selected_project = self.get_selected_project()

        context['projects'] = projects
        context['selected_project'] = selected_project
        context['project_form'] = kwargs.get('project_form', ProjectForm(prefix='project'))
        context['note_form'] = NoteCreateForm()
        context['note_edit_form'] = NoteEditForm()
        context["tag_form"] = TagCreateForm()
        context["checklist_form"] = ChecklistItemCreateForm()
        context["attachment_form"] = AttachmentUploadForm()
        context["collaborator_invite_form"] = kwargs.get("collaborator_invite_form", CollaboratorInviteForm())
        context["project_comment_form"] = kwargs.get("project_comment_form", ProjectCommentForm(prefix="comment"))

        if selected_project:
            context['project_link_form'] = kwargs.get(
                'project_link_form',
                ProjectLinkForm(prefix='link', user=self.request.user, initial={'project': selected_project.pk}),
            )
        else:
            context['project_link_form'] = kwargs.get(
                'project_link_form',
                ProjectLinkForm(prefix='link', user=self.request.user),
            )

        context['open_project_modal'] = kwargs.get('open_project_modal', False)
        context['open_edit_project_modal'] = kwargs.get('open_edit_project_modal', False)
        context['open_link_modal'] = kwargs.get('open_link_modal', False)
        context['open_edit_link_modal'] = kwargs.get('open_edit_link_modal', False)
        context['edit_project_form'] = kwargs.get(
            'edit_project_form',
            EditProjectForm(prefix='editproject', user=self.request.user),
        )
        context['edit_project_link_form'] = kwargs.get(
            'edit_project_link_form',
            EditProjectLinkForm(prefix='editlink', user=self.request.user),
        )
        ct_map = allowed_content_types()
        context["ct_project_id"] = ct_map[Project].id
        if selected_project:
            grouped_notes = notes_by_target(self.request.user, [selected_project])
            grouped_tags = tags_by_target(self.request.user, [selected_project])
            grouped_items = items_by_target(self.request.user, [selected_project])
            grouped_attachments = attachments_by_target(self.request.user, [selected_project])
            selected_project.notes_list = notes_for_target(grouped_notes, selected_project)
            selected_project.tags_list = tags_for_target(grouped_tags, selected_project)
            selected_project.checklist_items = items_for_target(grouped_items, selected_project)
            selected_project.attachments_list = attachments_for_target(grouped_attachments, selected_project)
            selected_project.collaborators_list = selected_project.collaborators.select_related("user").order_by("created_at")
            selected_project.comments_list = selected_project.comments.select_related("user").all()
            context["can_manage_collaborators"] = self.can_manage_collaborators(selected_project)
            context["can_edit_project"] = self.can_edit_project(selected_project)
        else:
            context["can_manage_collaborators"] = False
            context["can_edit_project"] = False
        return context

    def post(self, request, *args, **kwargs):
        form_type = request.POST.get('form_type')

        if form_type == 'project':
            form = ProjectForm(request.POST, prefix='project')
            if form.is_valid():
                project = form.save(commit=False)
                project.user = request.user
                project.save()
                messages.success(request, 'Project added.')
                return redirect(f"{self.success_url}?project={project.pk}")
            return self.render_to_response(
                self.get_context_data(project_form=form, open_project_modal=True)
            )

        if form_type == 'edit_project':
            form = EditProjectForm(request.POST, prefix='editproject', user=request.user)
            if form.is_valid():
                project = form.save()
                messages.success(request, 'Project updated.')
                return redirect(f"{self.success_url}?project={project.pk}")
            project_obj = self.accessible_projects_qs().filter(
                pk=request.POST.get('editproject-project_id'),
            ).first()
            return self.render_to_response(
                self.get_context_data(
                    edit_project_form=form,
                    open_edit_project_modal=True,
                    selected_project=project_obj,
                )
            )

        if form_type == 'delete_project':
            project = Project.objects.filter(
                pk=request.POST.get('project_id'),
                user=request.user,
            ).first()
            if project:
                project.delete()
                messages.success(request, 'Project deleted.')
            return redirect(self.success_url)

        if form_type == "invite_collaborator":
            selected_project_id = request.POST.get("project_context")
            redirect_url = self.success_url
            if selected_project_id:
                redirect_url = f"{self.success_url}?project={selected_project_id}"
            project = Project.objects.filter(pk=selected_project_id, user=request.user).first()
            form = CollaboratorInviteForm(request.POST)
            if not project:
                messages.error(request, "Only the project owner can invite collaborators.")
                return redirect(redirect_url)
            if form.is_valid():
                email = form.cleaned_data["email"]
                collaborator = User.objects.filter(email__iexact=email).first()
                if not collaborator:
                    messages.error(request, "No user found with that email.")
                elif collaborator.id == project.user_id:
                    messages.error(request, "The project owner is already part of the project.")
                else:
                    rel, created = ProjectCollaborator.objects.get_or_create(
                        project=project,
                        user=collaborator,
                        defaults={"added_by": request.user},
                    )
                    if created:
                        messages.success(request, f"{collaborator.get_username()} added as collaborator.")
                    else:
                        messages.info(request, "That user is already a collaborator.")
            else:
                messages.error(request, "Enter a valid collaborator email.")
            return redirect(redirect_url)

        if form_type == "remove_collaborator":
            selected_project_id = request.POST.get("project_context")
            redirect_url = self.success_url
            if selected_project_id:
                redirect_url = f"{self.success_url}?project={selected_project_id}"
            project = Project.objects.filter(pk=selected_project_id, user=request.user).first()
            if not project:
                messages.error(request, "Only the project owner can remove collaborators.")
                return redirect(redirect_url)
            removed = ProjectCollaborator.objects.filter(
                project=project,
                user_id=request.POST.get("collaborator_id"),
            ).delete()[0]
            if removed:
                messages.success(request, "Collaborator removed.")
            else:
                messages.error(request, "Unable to remove collaborator.")
            return redirect(redirect_url)

        if form_type == "add_project_comment":
            selected_project_id = request.POST.get("project_context")
            redirect_url = self.success_url
            if selected_project_id:
                redirect_url = f"{self.success_url}?project={selected_project_id}"
            project = self.accessible_projects_qs().filter(pk=selected_project_id).first()
            form = ProjectCommentForm(request.POST, prefix="comment")
            if not project:
                messages.error(request, "Project not found.")
                return redirect(redirect_url)
            if form.is_valid():
                ProjectComment.objects.create(
                    project=project,
                    user=request.user,
                    body=form.cleaned_data["body"],
                )
                messages.success(request, "Comment added.")
            else:
                messages.error(request, "Comment cannot be empty.")
            return redirect(redirect_url)

        if form_type == 'link':
            form = ProjectLinkForm(request.POST, prefix='link', user=request.user)
            if form.is_valid():
                project_link = form.save()
                messages.success(request, 'Project link added.')
                return redirect(f"{self.success_url}?project={project_link.project_id}")

            selected_project = form.data.get('link-project')
            project_obj = self.accessible_projects_qs().filter(pk=selected_project).first()
            return self.render_to_response(
                self.get_context_data(
                    project_link_form=form,
                    open_link_modal=True,
                    selected_project=project_obj,
                )
            )

        if form_type == 'edit_link':
            form = EditProjectLinkForm(request.POST, prefix='editlink', user=request.user)
            if form.is_valid():
                link = form.save()
                messages.success(request, 'Project link updated.')
                return redirect(f"{self.success_url}?project={link.project_id}")
            link_obj = ProjectLink.objects.filter(
                Q(pk=request.POST.get('editlink-link_id')),
                Q(project__user=request.user) | Q(project__collaborators__user=request.user),
            ).distinct().first()
            selected_project = link_obj.project if link_obj else self.get_selected_project()
            return self.render_to_response(
                self.get_context_data(
                    edit_project_link_form=form,
                    open_edit_link_modal=True,
                    selected_project=selected_project,
                )
            )

        if form_type == 'delete_link':
            link = ProjectLink.objects.filter(
                Q(pk=request.POST.get('link_id')),
                Q(project__user=request.user) | Q(project__collaborators__user=request.user),
            ).distinct().first()
            if link:
                project_id = link.project_id
                link.delete()
                messages.success(request, 'Project link deleted.')
                return redirect(f"{self.success_url}?project={project_id}")
            return redirect(self.success_url)

        if form_type == "add_note":
            form = NoteCreateForm(request.POST)
            selected_project_id = request.POST.get("project_context")
            redirect_url = self.success_url
            if selected_project_id:
                redirect_url = f"{self.success_url}?project={selected_project_id}"
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
        if form_type == "add_checklist_item":
            selected_project_id = request.POST.get("project_context")
            redirect_url = self.success_url
            if selected_project_id:
                redirect_url = f"{self.success_url}?project={selected_project_id}"
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
        if form_type == "add_attachment":
            selected_project_id = request.POST.get("project_context")
            redirect_url = self.success_url
            if selected_project_id:
                redirect_url = f"{self.success_url}?project={selected_project_id}"
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
            selected_project_id = request.POST.get("project_context")
            redirect_url = self.success_url
            if selected_project_id:
                redirect_url = f"{self.success_url}?project={selected_project_id}"
            deleted = delete_attachment_for_user(
                user=request.user,
                attachment_id=request.POST.get("attachment_id"),
            )
            if deleted:
                messages.success(request, "Attachment removed.")
            else:
                messages.error(request, "Unable to remove attachment.")
            return redirect(redirect_url)
        if form_type == "toggle_checklist_item":
            selected_project_id = request.POST.get("project_context")
            redirect_url = self.success_url
            if selected_project_id:
                redirect_url = f"{self.success_url}?project={selected_project_id}"
            item = set_item_done_for_user(
                user=request.user,
                item_id=request.POST.get("item_id"),
                is_done=request.POST.get("is_done") == "1",
            )
            if not item:
                messages.error(request, "Unable to update checklist item.")
            return redirect(redirect_url)
        if form_type == "delete_checklist_item":
            selected_project_id = request.POST.get("project_context")
            redirect_url = self.success_url
            if selected_project_id:
                redirect_url = f"{self.success_url}?project={selected_project_id}"
            deleted = delete_item_for_user(user=request.user, item_id=request.POST.get("item_id"))
            if deleted:
                messages.success(request, "Checklist item removed.")
            else:
                messages.error(request, "Unable to remove checklist item.")
            return redirect(redirect_url)

        if form_type == "add_tag":
            selected_project_id = request.POST.get("project_context")
            redirect_url = self.success_url
            if selected_project_id:
                redirect_url = f"{self.success_url}?project={selected_project_id}"
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

        if form_type == "delete_tag":
            selected_project_id = request.POST.get("project_context")
            redirect_url = self.success_url
            if selected_project_id:
                redirect_url = f"{self.success_url}?project={selected_project_id}"
            deleted = delete_tag_for_user(user=request.user, tag_id=request.POST.get("tag_id"))
            if deleted:
                messages.success(request, "Tag removed.")
            else:
                messages.error(request, "Unable to remove that tag.")
            return redirect(redirect_url)

        if form_type == "edit_note":
            form = NoteEditForm(request.POST)
            selected_project_id = request.POST.get("project_context")
            redirect_url = self.success_url
            if selected_project_id:
                redirect_url = f"{self.success_url}?project={selected_project_id}"
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
            selected_project_id = request.POST.get("project_context")
            redirect_url = self.success_url
            if selected_project_id:
                redirect_url = f"{self.success_url}?project={selected_project_id}"
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
