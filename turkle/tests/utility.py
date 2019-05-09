def save_model(obj):
    """
    Imitates Django saving the model from a form.
    form.is_valid() calls clean methods including the model's full_clean
    See Django's forms/forms.py for details.
    """
    obj.full_clean(validate_unique=False)
    obj.save()
