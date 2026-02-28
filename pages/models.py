from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models import Avg
from django.core.validators import MaxValueValidator, MinValueValidator


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

    def is_favored_by(self, user):
        if user.is_anonymous:
            return False
        return self.favored_by.filter(user=user).exists()

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

    @property
    def average_rating(self):
        value = self.reviews.aggregate(avg=Avg('stars'))['avg']
        return round(value, 1) if value else 0

    @property
    def reviews_count(self):
        return self.reviews.count()


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

class Report(models.Model):
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports_sent')
    reported_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports_received')
    conversation = models.ForeignKey('Conversation', on_delete=models.CASCADE)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report from {self.reporter} about {self.reported_user}"

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist_items')
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='favored_by')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'listing')


class ListingReview(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listing_reviews')
    stars = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('listing', 'reviewer')
        ordering = ['-updated_at']

    def __str__(self):
        return f'Review {self.stars}/5 by {self.reviewer.username} for {self.listing.title}'
