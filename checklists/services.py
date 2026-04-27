from django.contrib.contenttypes.models import ContentType

from assignments.models import Assignment
from projects.models import Project

from .models import ChecklistItem

ALLOWED_MODELS = (Assignment, Project)


def allowed_content_types():
    return {model: ContentType.objects.get_for_model(model) for model in ALLOWED_MODELS}


def object_belongs_to_user(obj, user):
    if isinstance(obj, Assignment):
        return obj.user_id == user.id
    if isinstance(obj, Project):
        return obj.user_id == user.id
    return False


def resolve_target(content_type_id, object_id):
    ct = ContentType.objects.filter(id=content_type_id).first()
    if not ct:
        return None
    model_class = ct.model_class()
    if model_class not in ALLOWED_MODELS:
        return None
    return model_class.objects.filter(pk=object_id).first()


def create_item_for_target(*, user, content_type_id, object_id, text):
    target = resolve_target(content_type_id, object_id)
    if not target or not object_belongs_to_user(target, user):
        return None
    ct = ContentType.objects.get_for_model(target.__class__)
    return ChecklistItem.objects.create(
        user=user,
        content_type=ct,
        object_id=target.pk,
        text=text.strip(),
    )


def set_item_done_for_user(*, user, item_id, is_done):
    item = ChecklistItem.objects.filter(pk=item_id, user=user).first()
    if not item:
        return None
    item.is_done = is_done
    item.save(update_fields=["is_done"])
    return item


def delete_item_for_user(*, user, item_id):
    item = ChecklistItem.objects.filter(pk=item_id, user=user).first()
    if not item:
        return False
    item.delete()
    return True


def items_by_target(user, targets):
    if not targets:
        return {}

    ct_map = allowed_content_types()
    by_model_ids = {}
    for target in targets:
        by_model_ids.setdefault(target.__class__, set()).add(target.pk)

    all_items = []
    for model, ids in by_model_ids.items():
        all_items.extend(
            ChecklistItem.objects.filter(
                user=user,
                content_type=ct_map[model],
                object_id__in=ids,
            ).order_by("is_done", "created_at")
        )

    grouped = {}
    for item in all_items:
        grouped.setdefault((item.content_type_id, item.object_id), []).append(item)
    return grouped


def items_for_target(grouped_items, target):
    ct = ContentType.objects.get_for_model(target.__class__)
    return grouped_items.get((ct.id, target.pk), [])
