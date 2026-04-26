from django.contrib.contenttypes.models import ContentType

from assignments.models import Assignment
from courses.models import Course, Textbook
from projects.models import Project
from resources.models import ResourceItem

from .models import Tag

ALLOWED_MODELS = (Course, Textbook, Assignment, Project, ResourceItem)


def allowed_content_types():
    return {model: ContentType.objects.get_for_model(model) for model in ALLOWED_MODELS}


def object_belongs_to_user(obj, user):
    if isinstance(obj, Course):
        return obj.user_id == user.id
    if isinstance(obj, Textbook):
        return obj.course.user_id == user.id
    if isinstance(obj, Assignment):
        return obj.user_id == user.id
    if isinstance(obj, Project):
        return obj.user_id == user.id
    if isinstance(obj, ResourceItem):
        return obj.column.user_id == user.id
    return False


def resolve_target(content_type_id, object_id):
    ct = ContentType.objects.filter(id=content_type_id).first()
    if not ct:
        return None
    model_class = ct.model_class()
    if model_class not in ALLOWED_MODELS:
        return None
    return model_class.objects.filter(pk=object_id).first()


def create_tag_for_target(*, user, content_type_id, object_id, label):
    target = resolve_target(content_type_id, object_id)
    if not target or not object_belongs_to_user(target, user):
        return None
    ct = ContentType.objects.get_for_model(target.__class__)
    normalized = label.strip().lower()
    if not normalized.startswith("#"):
        normalized = f"#{normalized}"
    tag, _ = Tag.objects.get_or_create(
        user=user,
        content_type=ct,
        object_id=target.pk,
        label=normalized,
    )
    return tag


def delete_tag_for_user(*, user, tag_id):
    tag = Tag.objects.filter(pk=tag_id, user=user).first()
    if not tag:
        return False
    tag.delete()
    return True


def tags_by_target(user, targets):
    if not targets:
        return {}

    ct_map = allowed_content_types()
    by_model_ids = {}
    for target in targets:
        by_model_ids.setdefault(target.__class__, set()).add(target.pk)

    all_tags = []
    for model, ids in by_model_ids.items():
        all_tags.extend(
            Tag.objects.filter(
                user=user,
                content_type=ct_map[model],
                object_id__in=ids,
            ).order_by("label")
        )

    grouped = {}
    for tag in all_tags:
        grouped.setdefault((tag.content_type_id, tag.object_id), []).append(tag)
    return grouped


def tags_for_target(grouped_tags, target):
    ct = ContentType.objects.get_for_model(target.__class__)
    return grouped_tags.get((ct.id, target.pk), [])
