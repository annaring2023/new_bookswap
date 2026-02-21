from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Listing, UserProfile

FAVORITE_GENRE_CHOICES = [
    ('fantasy', 'Фентезі'),
    ('romance', 'Романтика'),
    ('detective', 'Детектив'),
    ('thriller', 'Трилер'),
    ('scifi', 'Наукова фантастика'),
    ('classic', 'Класика'),
    ('psychology', 'Психологія'),
    ('selfhelp', 'Саморозвиток'),
    ('history', 'Історія'),
    ('business', 'Бізнес'),
]

GENRE_LABELS = dict(FAVORITE_GENRE_CHOICES)


def _normalize_hashtags(raw_text):
    parts = [p.strip().lstrip('#') for p in raw_text.replace(',', ' ').split()]
    clean = []
    for p in parts:
        if p and p not in clean:
            clean.append(p.lower())
    return ' '.join(f'#{p}' for p in clean)

# Головна сторінка
def home(request):
    if request.user.is_authenticated:
        return redirect('catalog')
    return render(request, 'home.html')


def catalog(request):
    if not request.user.is_authenticated:
        messages.error(request, 'Спочатку увійдіть в акаунт')
        return redirect('home')

    query = request.GET.get('q', '').strip()
    search_in_description = request.GET.get('desc') == '1'
    genre_filter = request.GET.get('genre_filter', '').strip()
    condition_filter = request.GET.get('condition_filter', '').strip()
    author_filter = request.GET.get('author_filter', '').strip()
    language_filter = request.GET.get('language_filter', '').strip()
    binding_filter = request.GET.get('binding_filter', '').strip()

    listings = Listing.objects.select_related('owner').all()

    if query:
        if search_in_description:
            listings = listings.filter(Q(title__icontains=query) | Q(description__icontains=query))
        else:
            listings = listings.filter(title__icontains=query)

    if genre_filter:
        listings = listings.filter(genre__icontains=genre_filter)
    if condition_filter:
        listings = listings.filter(condition=condition_filter)
    if author_filter:
        listings = listings.filter(author__icontains=author_filter)
    if language_filter:
        listings = listings.filter(language__icontains=language_filter)
    if binding_filter:
        listings = listings.filter(binding_type=binding_filter)

    return render(request, 'catalog.html', {
        'listings': listings,
        'query': query,
        'search_in_description': search_in_description,
        'genre_filter': genre_filter,
        'condition_filter': condition_filter,
        'author_filter': author_filter,
        'language_filter': language_filter,
        'binding_filter': binding_filter, # Передаємо нове поле
    })


def listing_detail(request, listing_id):
    if not request.user.is_authenticated:
        messages.error(request, 'Спочатку увійдіть в акаунт')
        return redirect('home')

    listing = get_object_or_404(Listing.objects.select_related('owner'), id=listing_id)
    if listing.owner_id == request.user.id:
        messages.info(request, 'Це ваше оголошення. Редагуйте його у профілі.')
        return redirect('profile')

    owner_profile = UserProfile.objects.filter(user=listing.owner).first()
    return render(request, 'listing_detail.html', {
        'listing': listing,
        'owner_profile': owner_profile,
    })


def user_profile_view(request, user_id):
    if not request.user.is_authenticated:
        messages.error(request, 'Спочатку увійдіть в акаунт')
        return redirect('home')

    owner = get_object_or_404(User, id=user_id)
    if owner.id == request.user.id:
        return redirect('profile')

    owner_profile = UserProfile.objects.filter(user=owner).first()
    owner_listings = Listing.objects.filter(owner=owner)
    owner_genres_display = []
    if owner_profile and owner_profile.favorite_genres:
        selected_genres = [g for g in owner_profile.favorite_genres.split(',') if g]
        owner_genres_display = [GENRE_LABELS[g] for g in selected_genres if g in GENRE_LABELS]
    return render(request, 'user_profile.html', {
        'owner': owner,
        'owner_profile': owner_profile,
        'owner_genres_display': owner_genres_display,
        'owner_listings': owner_listings,
    })

# Сторінка профілю (пускає тільки тих, хто увійшов)
def profile(request):
    if not request.user.is_authenticated:
        return redirect('home')  # Якщо не зайшов - викидаємо на головну
    profile_data, _ = UserProfile.objects.get_or_create(user=request.user)
    my_listings = Listing.objects.filter(owner=request.user)
    selected_genres = [g for g in profile_data.favorite_genres.split(',') if g]
    favorite_genres_display = [GENRE_LABELS[g] for g in selected_genres if g in GENRE_LABELS]
    return render(request, 'profile.html', {
        'my_listings': my_listings,
        'profile_data': profile_data,
        'genre_choices': FAVORITE_GENRE_CHOICES,
        'selected_genres': selected_genres,
        'favorite_genres_display': favorite_genres_display,
    })

# Логіка реєстрації
def register_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']

        # Перевірка, чи існує такий юзер
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Таке ім\'я вже зайняте!')
            return redirect('home')

        # Створення користувача
        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user) # Одразу входимо
        return redirect('catalog')

    return redirect('home')

# Логіка входу
def login_user(request):
    if request.method == 'POST':
        username = request.POST['username'] # Тут беремо дані з форми
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('catalog')
        else:
            messages.error(request, 'Невірний логін або пароль')
            return redirect('home')

    return redirect('home')


def create_listing(request):
    if not request.user.is_authenticated:
        messages.error(request, 'Спочатку увійдіть в акаунт')
        return redirect('home')

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        author = request.POST.get('author', '').strip()
        publication_year_raw = request.POST.get('publication_year', '').strip()
        language = request.POST.get('language', '').strip()
        pages_raw = request.POST.get('pages', '').strip()
        genre = request.POST.get('genre', '').strip()
        condition = request.POST.get('condition', '').strip()
        hashtags_raw = request.POST.get('hashtags', '').strip()
        description = request.POST.get('description', '').strip()
        image_url = request.POST.get('image_url', '').strip()
        image_file = request.FILES.get('image')

        if not title or not description:
            messages.error(request, 'Заповніть назву та опис оголошення')
            return redirect('profile')

        Listing.objects.create(
            owner=request.user,
            title=title,
            author=author,
            publication_year=int(publication_year_raw) if publication_year_raw.isdigit() else None,
            language=language,
            pages=int(pages_raw) if pages_raw.isdigit() else None,
            genre=genre,
            condition=condition,
            hashtags=_normalize_hashtags(hashtags_raw),
            description=description,
            image=image_file,
            image_url=image_url,
        )
        messages.success(request, 'Оголошення додано в каталог')
    return redirect('profile')


def edit_listing(request, listing_id):
    if not request.user.is_authenticated:
        return redirect('home')

    listing = get_object_or_404(Listing, id=listing_id, owner=request.user)

    if request.method == 'POST':
        listing.title = request.POST.get('title', '').strip()
        listing.author = request.POST.get('author', '').strip()
        publication_year_raw = request.POST.get('publication_year', '').strip()
        listing.publication_year = int(publication_year_raw) if publication_year_raw.isdigit() else None
        listing.language = request.POST.get('language', '').strip()
        pages_raw = request.POST.get('pages', '').strip()
        listing.pages = int(pages_raw) if pages_raw.isdigit() else None
        listing.genre = request.POST.get('genre', '').strip()
        listing.condition = request.POST.get('condition', '').strip()
        listing.hashtags = _normalize_hashtags(request.POST.get('hashtags', '').strip())
        listing.description = request.POST.get('description', '').strip()

        image_url = request.POST.get('image_url', '').strip()
        if image_url:
            listing.image_url = image_url
        if request.FILES.get('image'):
            listing.image = request.FILES['image']
            listing.image_url = ''

        if not listing.title or not listing.description:
            messages.error(request, 'Назва та опис обовʼязкові')
            return redirect('edit_listing', listing_id=listing.id)

        listing.save()
        messages.success(request, 'Оголошення оновлено')
        return redirect('profile')

    return render(request, 'edit_listing.html', {'listing': listing})


def delete_listing(request, listing_id):
    if not request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        listing = get_object_or_404(Listing, id=listing_id, owner=request.user)
        listing.delete()
        messages.success(request, 'Оголошення видалено')
    return redirect('profile')


def update_profile(request):
    if not request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', '').strip()
        request.user.last_name = request.POST.get('last_name', '').strip()
        request.user.email = request.POST.get('email', '').strip()
        request.user.save()

        profile_data, _ = UserProfile.objects.get_or_create(user=request.user)
        age_raw = request.POST.get('age', '').strip()
        profile_data.age = int(age_raw) if age_raw.isdigit() else None
        profile_data.gender = request.POST.get('gender', '').strip()
        profile_data.city = request.POST.get('city', '').strip()
        selected_genres = [g for g in request.POST.getlist('favorite_genres') if g in GENRE_LABELS]
        profile_data.favorite_genres = ','.join(selected_genres)
        if request.FILES.get('avatar'):
            profile_data.avatar = request.FILES['avatar']
            profile_data.avatar_url = ''
        profile_data.save()

        messages.success(request, 'Профіль оновлено')
    return redirect('profile')


def settings_page(request):
    if not request.user.is_authenticated:
        messages.error(request, 'Спочатку увійдіть в акаунт')
        return redirect('home')
    return render(request, 'settings.html')


def logout_user(request):
    if request.method == 'POST':
        logout(request)
        return redirect('home')
    return redirect('settings')
