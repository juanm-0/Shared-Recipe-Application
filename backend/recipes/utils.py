def get_or_create_ci(model, name):
    obj = model.objects.filter(name__iexact=name).first()
    if obj is not None:
        return obj
    return model.objects.create(name=name)
