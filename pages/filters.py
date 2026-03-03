import django_filters
from .models import Listing

class ListingFilter(django_filters.FilterSet):
    genre = django_filters.CharFilter(lookup_expr='icontains', label='Жанр')
    author = django_filters.CharFilter(lookup_expr='icontains', label='Автор')
    language = django_filters.CharFilter(lookup_expr='icontains', label='Мова')

    condition = django_filters.ChoiceFilter(
        choices=Listing.CONDITION_CHOICES,
        label='Стан книги'
    )

    class Meta:
        model = Listing
        fields = ['genre', 'author', 'language', 'condition']
