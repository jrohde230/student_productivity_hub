from django.contrib.contenttypes.models import ContentType

from assignments.models import Assignment
from courses.models import Course, Textbook
from projects.models import Project
from resources.models import ResourceItem

from .models import Note

ALLOWED_MODELS = (Course, Textbook, Assignment, Project, ResourceItem)


def allowed_content_types():
    return {
        model: ContentType.objects.get_for_model(model)
        for model in ALLOWED_MODELS
    }


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


def create_note_for_target(*, user, content_type_id, object_id, body):
    target = resolve_target(content_type_id, object_id)
    if not target or not object_belongs_to_user(target, user):
        return None
    ct = ContentType.objects.get_for_model(target.__class__)
    return Note.objects.create(
        user=user,
        content_type=ct,
        object_id=target.pk,
        body=body,
    )


def get_user_note(user, note_id):
    return Note.objects.filter(pk=note_id, user=user).first()


def update_note_for_user(*, user, note_id, body):
    note = get_user_note(user, note_id)
    if not note:
        return None
    note.body = body
    note.save(update_fields=["body", "updated_at"])
    return note


def delete_note_for_user(*, user, note_id):
    note = get_user_note(user, note_id)
    if not note:
        return False
    note.delete()
    return True


def notes_by_target(user, targets):
    if not targets:
        return {}

    ct_map = allowed_content_types()
    by_model_ids = {}
    for target in targets:
        model = target.__class__
        by_model_ids.setdefault(model, set()).add(target.pk)

    all_notes = []
    for model, ids in by_model_ids.items():
        all_notes.extend(
            Note.objects.filter(
                user=user,
                content_type=ct_map[model],
                object_id__in=ids,
            ).order_by("-created_at")
        )

    grouped = {}
    for note in all_notes:
        grouped.setdefault((note.content_type_id, note.object_id), []).append(note)
    return grouped


def notes_for_target(grouped_notes, target):
    ct = ContentType.objects.get_for_model(target.__class__)
    return grouped_notes.get((ct.id, target.pk), [])
