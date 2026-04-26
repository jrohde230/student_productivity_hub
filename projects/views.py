from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from .forms import EditProjectForm, EditProjectLinkForm, ProjectForm, ProjectLinkForm
from .models import Project, ProjectLink


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'projects/home.html'
    success_url = reverse_lazy('projects:home')

    def get_selected_project(self):
        project_id = self.request.GET.get('project')
        projects = Project.objects.filter(user=self.request.user)
        selected = None
        if project_id:
            selected = projects.filter(pk=project_id).first()
        if not selected:
            selected = projects.order_by('name').first()
        return selected

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        projects = Project.objects.filter(user=self.request.user).order_by('name')
        selected_project = kwargs.get('selected_project')
        if selected_project is None:
            selected_project = self.get_selected_project()

        context['projects'] = projects
        context['selected_project'] = selected_project
        context['project_form'] = kwargs.get('project_form', ProjectForm(prefix='project'))

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
            project_obj = Project.objects.filter(
                pk=request.POST.get('editproject-project_id'),
                user=request.user,
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

        if form_type == 'link':
            form = ProjectLinkForm(request.POST, prefix='link', user=request.user)
            if form.is_valid():
                project_link = form.save()
                messages.success(request, 'Project link added.')
                return redirect(f"{self.success_url}?project={project_link.project_id}")

            selected_project = form.data.get('link-project')
            project_obj = Project.objects.filter(pk=selected_project, user=request.user).first()
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
                pk=request.POST.get('editlink-link_id'),
                project__user=request.user,
            ).first()
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
                pk=request.POST.get('link_id'),
                project__user=request.user,
            ).first()
            if link:
                project_id = link.project_id
                link.delete()
                messages.success(request, 'Project link deleted.')
                return redirect(f"{self.success_url}?project={project_id}")
            return redirect(self.success_url)

        return redirect(self.success_url)
