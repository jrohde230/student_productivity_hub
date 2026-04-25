from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from .forms import ProjectForm, ProjectLinkForm
from .models import Project


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
        context['open_link_modal'] = kwargs.get('open_link_modal', False)
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

        return redirect(self.success_url)
