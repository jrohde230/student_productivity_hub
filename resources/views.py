import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Max
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from .forms import AddResourceForm, EditResourceForm, RenameColumnForm
from .models import ResourceColumn, ResourceItem


def ensure_resource_columns(user):
    for slot in range(3):
        ResourceColumn.objects.get_or_create(
            user=user,
            slot=slot,
            defaults={"title": f"Column {slot + 1}"},
        )


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "resources/home.html"
    success_url = reverse_lazy("resources:home")

    def get_context_data(self, **kwargs):
        ensure_resource_columns(self.request.user)
        context = super().get_context_data(**kwargs)
        context["columns"] = (
            ResourceColumn.objects.filter(user=self.request.user)
            .prefetch_related("items")
            .order_by("slot")
        )

        if "rename_form" in kwargs:
            context["rename_form"] = kwargs["rename_form"]
        else:
            context["rename_form"] = RenameColumnForm(prefix="rename", user=self.request.user)

        if "add_resource_form" in kwargs:
            context["add_resource_form"] = kwargs["add_resource_form"]
        else:
            context["add_resource_form"] = AddResourceForm(prefix="additem", user=self.request.user)

        if "edit_resource_form" in kwargs:
            context["edit_resource_form"] = kwargs["edit_resource_form"]
        else:
            context["edit_resource_form"] = EditResourceForm(prefix="editres", user=self.request.user)

        context["rename_form_errors"] = kwargs.get("rename_form_errors", False)
        context["rename_column_id"] = kwargs.get("rename_column_id")
        context["add_resource_form_errors"] = kwargs.get("add_resource_form_errors", False)
        context["add_resource_column_id"] = kwargs.get("add_resource_column_id")
        context["edit_resource_form_errors"] = kwargs.get("edit_resource_form_errors", False)
        context["edit_resource_id"] = kwargs.get("edit_resource_id")
        return context

    def post(self, request, *args, **kwargs):
        ensure_resource_columns(request.user)
        form_type = request.POST.get("form_type")

        if form_type == "rename_column":
            form = RenameColumnForm(request.POST, prefix="rename", user=request.user)
            if form.is_valid():
                column = form.cleaned_data["column"]
                column.title = form.cleaned_data["title"]
                column.save(update_fields=["title"])
                messages.success(request, "Column name updated.")
                return redirect(self.success_url)
            col = form.data.get("rename-column")
            return self.render_to_response(
                self.get_context_data(
                    rename_form=form,
                    rename_form_errors=True,
                    rename_column_id=col,
                )
            )

        if form_type == "add_resource":
            form = AddResourceForm(request.POST, prefix="additem", user=request.user)
            if form.is_valid():
                item = form.save(commit=False)
                agg = ResourceItem.objects.filter(column=item.column).aggregate(m=Max("sort_order"))
                max_order = agg["m"]
                item.sort_order = (max_order + 1) if max_order is not None else 0
                item.save()
                messages.success(request, "Resource added.")
                return redirect(self.success_url)
            return self.render_to_response(
                self.get_context_data(
                    add_resource_form=form,
                    add_resource_form_errors=True,
                    add_resource_column_id=request.POST.get("additem-column"),
                )
            )

        if form_type == "edit_resource":
            form = EditResourceForm(request.POST, prefix="editres", user=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, "Resource updated.")
                return redirect(self.success_url)
            return self.render_to_response(
                self.get_context_data(
                    edit_resource_form=form,
                    edit_resource_form_errors=True,
                    edit_resource_id=request.POST.get("editres-resource_id"),
                )
            )

        if form_type == "delete_resource":
            try:
                rid = int(request.POST.get("resource_id", ""))
            except ValueError:
                return redirect(self.success_url)
            item = ResourceItem.objects.filter(pk=rid, column__user=request.user).first()
            if item:
                item.delete()
                messages.success(request, "Resource removed.")
            return redirect(self.success_url)

        return redirect(self.success_url)


@method_decorator(require_POST, name="dispatch")
class ReorderResourcesView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({"error": "Invalid JSON."}, status=400)

        column_id = data.get("column_id")
        order = data.get("order")
        if column_id is None or not isinstance(order, list):
            return JsonResponse({"error": "Invalid payload."}, status=400)

        column = ResourceColumn.objects.filter(pk=column_id, user=request.user).first()
        if not column:
            return JsonResponse({"error": "Column not found."}, status=404)

        try:
            ordered_ids = [int(pk) for pk in order]
        except (TypeError, ValueError):
            return JsonResponse({"error": "Invalid order list."}, status=400)

        existing = set(
            ResourceItem.objects.filter(column=column).values_list("pk", flat=True)
        )
        if set(ordered_ids) != existing or len(ordered_ids) != len(existing):
            return JsonResponse({"error": "Order does not match column items."}, status=400)

        for index, pk in enumerate(ordered_ids):
            ResourceItem.objects.filter(pk=pk, column=column).update(sort_order=index)

        return JsonResponse({"ok": True})
