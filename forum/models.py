from django.db import models


class Board(models.Model):
    slug = models.SlugField(max_length=20, unique=True)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"/{self.slug}/ - {self.title}"


class Tag(models.Model):
    slug = models.SlugField(max_length=30, unique=True)
    title = models.CharField(max_length=50)

    def __str__(self):
        return self.title
