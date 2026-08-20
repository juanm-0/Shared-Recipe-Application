from django.db import IntegrityError


def get_or_create_ci(model, name):
    obj = model.objects.filter(name__iexact=name).first()
    if obj is not None:
        return obj
    try:
        return model.objects.create(name=name)
    except IntegrityError:
        return model.objects.filter(name__iexact=name).first()
