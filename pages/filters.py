import django_filters
from .models import Listing

class ListingFilter(django_filters.FilterSet):
    # Фільтри для текстових полів (часткове співпадіння, ігноруючи регістр)
    genre = django_filters.CharFilter(lookup_expr='icontains', label='Жанр')
    author = django_filters.CharFilter(lookup_expr='icontains', label='Автор')
    language = django_filters.CharFilter(lookup_expr='icontains', label='Мова')

    condition = django_filters.ChoiceFilter(
        choices=Listing.CONDITION_CHOICES,
        label='Стан книги'
    )

    # Якщо ви додасте поле ціни пізніше, ці фільтри запрацюють:
    # min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte', label='Ціна від')
    # max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte', label='Ціна до')

    class Meta:
        model = Listing
        # Поля, які будуть оброблятися автоматично
        fields = ['genre', 'author', 'language', 'condition']
