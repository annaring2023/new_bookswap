from django.db import models
from django.contrib.auth.models import User


class Listing(models.Model):
    CONDITION_CHOICES = [
        ('almost_new', 'Майже нова'),
        ('average', 'Середній стан'),
        ('poor', 'Поганий стан'),
    ]
    BINDING_CHOICES = [
        ('hard', 'Тверда'),
        ('soft', 'М’яка'),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings')
    title = models.CharField(max_length=150)
    author = models.CharField(max_length=150, blank=True)
    publication_year = models.PositiveSmallIntegerField(null=True, blank=True)
    language = models.CharField(max_length=60, blank=True)
    pages = models.PositiveIntegerField(null=True, blank=True)
    genre = models.CharField(max_length=120, blank=True)
    condition = models.CharField(max_length=20,
        choices=CONDITION_CHOICES,
        blank=True)
    hashtags = models.CharField(max_length=255, blank=True)
    description = models.TextField()
    image = models.FileField(upload_to='listing_images/', blank=True, null=True)
    image_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    binding_type = models.CharField(max_length=10,
        choices=BINDING_CHOICES,
        blank=True,
        null=True,
        verbose_name="Тип палітурки")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} ({self.owner.username})'


class UserProfile(models.Model):
    GENDER_CHOICES = [
        ('female', 'Жіноча'),
        ('male', 'Чоловіча'),
        ('other', 'Інше'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile_data')
    age = models.PositiveSmallIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    city = models.CharField(max_length=80, blank=True)
    favorite_genres = models.CharField(max_length=255, blank=True)
    avatar = models.FileField(upload_to='avatars/', blank=True, null=True)
    avatar_url = models.URLField(blank=True)

    def __str__(self):
        return f'Profile: {self.user.username}'


class Conversation(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='conversations')
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f'Conversation #{self.id} - {self.listing.title}'


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    text = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Message #{self.id} by {self.sender.username}'
