from django.db import models
from django.utils import timezone


class BaseModel(models.Model):
    # Fields
    created_dt = models.DateTimeField(editable=False)
    modified_dt = models.DateTimeField(editable=False)

    # Attributes
    objects = models.Manager()

    def save(self, *args, **kwargs):
        if not self.pk:
            self.created_dt = timezone.now()
        self.modified_dt = timezone.now()
        return super().save(*args, **kwargs)

    class Meta:
        abstract = True
