from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.views.generic import TemplateView

from assignments.models import Assignment
from courses.models import Course, Textbook
from projects.models import Project
from resources.models import ResourceItem

from .models import Tag


class TagSearchView(LoginRequiredMixin, TemplateView):
    template_name = "tags/search_results.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get("q", "").strip().lower()
        if query and not query.startswith("#"):
            query = f"#{query}"
        context["query"] = query

        course_results = []
        textbook_results = []
        assignment_results = []
        project_results = []
        resource_results = []

        if query:
            tags = Tag.objects.filter(user=self.request.user, label__icontains=query)
            tag_groups = {}
            for tag in tags:
                tag_groups.setdefault((tag.content_type_id, tag.object_id), []).append(tag.label)

            ct_course = ContentType.objects.get_for_model(Course).id
            ct_textbook = ContentType.objects.get_for_model(Textbook).id
            ct_assignment = ContentType.objects.get_for_model(Assignment).id
            ct_project = ContentType.objects.get_for_model(Project).id
            ct_resource = ContentType.objects.get_for_model(ResourceItem).id

            for (ct_id, obj_id), labels in tag_groups.items():
                if ct_id == ct_course:
                    obj = Course.objects.filter(pk=obj_id, user=self.request.user).first()
                    if obj:
                        course_results.append({"obj": obj, "labels": sorted(set(labels))})
                elif ct_id == ct_textbook:
                    obj = Textbook.objects.filter(pk=obj_id, course__user=self.request.user).first()
                    if obj:
                        textbook_results.append({"obj": obj, "labels": sorted(set(labels))})
                elif ct_id == ct_assignment:
                    obj = Assignment.objects.filter(pk=obj_id, user=self.request.user).first()
                    if obj:
                        assignment_results.append({"obj": obj, "labels": sorted(set(labels))})
                elif ct_id == ct_project:
                    obj = Project.objects.filter(pk=obj_id, user=self.request.user).first()
                    if obj:
                        project_results.append({"obj": obj, "labels": sorted(set(labels))})
                elif ct_id == ct_resource:
                    obj = ResourceItem.objects.filter(pk=obj_id, column__user=self.request.user).first()
                    if obj:
                        resource_results.append({"obj": obj, "labels": sorted(set(labels))})

        context["course_results"] = sorted(course_results, key=lambda x: x["obj"].name.lower())
        context["textbook_results"] = sorted(textbook_results, key=lambda x: x["obj"].title.lower())
        context["assignment_results"] = sorted(assignment_results, key=lambda x: x["obj"].assignment_name.lower())
        context["project_results"] = sorted(project_results, key=lambda x: x["obj"].name.lower())
        context["resource_results"] = sorted(resource_results, key=lambda x: x["obj"].name.lower())
        return context
