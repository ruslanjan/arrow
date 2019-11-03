from django.db import models


class IndexedModel(models.Model):
    index = models.IntegerField()

    class Meta:
        abstract = True
