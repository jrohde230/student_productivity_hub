from django.contrib.contenttypes.models import ContentType

from assignments.models import Assignment
from courses.models import Course, Textbook
from projects.models import Project
from resources.models import ResourceItem

from .models import Attachment

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


def create_attachment_for_target(*, user, content_type_id, object_id, file_obj):
    target = resolve_target(content_type_id, object_id)
    if not target or not object_belongs_to_user(target, user):
        return None
    ct = ContentType.objects.get_for_model(target.__class__)
    return Attachment.objects.create(
        user=user,
        content_type=ct,
        object_id=target.pk,
        file=file_obj,
        original_name=getattr(file_obj, "name", ""),
    )


def delete_attachment_for_user(*, user, attachment_id):
    attachment = Attachment.objects.filter(pk=attachment_id, user=user).first()
    if not attachment:
        return False
    if attachment.file:
        attachment.file.delete(save=False)
    attachment.delete()
    return True


def attachments_by_target(user, targets):
    if not targets:
        return {}

    ct_map = allowed_content_types()
    by_model_ids = {}
    for target in targets:
        by_model_ids.setdefault(target.__class__, set()).add(target.pk)

    all_attachments = []
    for model, ids in by_model_ids.items():
        all_attachments.extend(
            Attachment.objects.filter(
                user=user,
                content_type=ct_map[model],
                object_id__in=ids,
            ).order_by("-created_at")
        )

    grouped = {}
    for attachment in all_attachments:
        grouped.setdefault((attachment.content_type_id, attachment.object_id), []).append(attachment)
    return grouped


def attachments_for_target(grouped_attachments, target):
    ct = ContentType.objects.get_for_model(target.__class__)
    return grouped_attachments.get((ct.id, target.pk), [])
