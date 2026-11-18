from django.db import models
from django.utils import timezone


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


class Thread(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name="threads")
    name = models.CharField(max_length=50, blank=True)
    subject = models.CharField(max_length=150)
    body = models.TextField()
    tags = models.ManyToManyField(Tag, blank=True, related_name="threads")
    is_pinned = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    bumped_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"#{self.pk} {self.subject}"


class Post(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name="posts")
    name = models.CharField(max_length=50, blank=True)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Post #{self.pk} in thread #{self.thread_id}"
