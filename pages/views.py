from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.db.models import Avg
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .models import Report
from .models import Listing, UserProfile, Conversation, Message
from .models import Listing, UserProfile, Wishlist, ListingReview

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

def _build_conversation_rows(current_user, conversations):
    rows = []
    for conv in conversations:
        other_user = next((u for u in conv.participants.all() if u.id != current_user.id), None)
        avatar_url = ''
        if other_user:
            profile = UserProfile.objects.filter(user=other_user).first()
            if profile and profile.avatar:
                avatar_url = profile.avatar.url
        unread_count = conv.messages.filter(is_read=False).exclude(sender=current_user).count()
        rows.append({
            'conversation': conv,
            'other_user': other_user,
            'avatar_url': avatar_url,
            'unread_count': unread_count,
        })
    return rows

def _unread_messages_count(user):
    return Message.objects.filter(
        conversation__participants=user,
        is_read=False,
    ).exclude(sender=user).count()

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


# def catalog(request):
#     if not request.user.is_authenticated:
#         messages.error(request, 'Спочатку увійдіть в акаунт')
#         return redirect('home')

#     query = request.GET.get('q', '').strip()
#     search_in_description = request.GET.get('desc') == '1'
#     genre_filter = request.GET.get('genre', '').strip()
#     condition_filter = request.GET.get('condition_filter', '').strip()
#     author_filter = request.GET.get('author', '').strip()
#     language_filter = request.GET.get('language', '').strip()
#     binding_filter = request.GET.get('binding_filter', '').strip()
#     pages_filter = request.GET.get('pages_filter', '').strip()

#     listings = Listing.objects.select_related('owner').exclude(owner=request.user)

#     wishlisted_ids = []
#     if request.user.is_authenticated:
#         wishlisted_ids = Wishlist.objects.filter(user=request.user).values_list('listing_id', flat=True)

#     if query:
#         if search_in_description:
#             listings = listings.filter(Q(title__icontains=query) | Q(description__icontains=query))
#         else:
#             listings = listings.filter(title__icontains=query)

#     if genre_filter:
#         listings = listings.filter(genre__icontains=genre_filter)
#     if condition_filter:
#         listings = listings.filter(condition=condition_filter)
#     if author_filter:
#         listings = listings.filter(author__icontains=author_filter)
#     if language_filter:
#         listings = listings.filter(language__icontains=language_filter)
#     if binding_filter:
#         listings = listings.filter(binding_type=binding_filter)
#     if pages_filter and pages_filter.isdigit():
#         listings = listings.filter(pages__lte=int(pages_filter))

#     return render(request, 'catalog.html', {
#         'listings': listings,
#         'query': query,
#         'search_in_description': search_in_description,
#         'genre': genre_filter,
#         'genre_choices': FAVORITE_GENRE_CHOICES,
#         'condition_filter': condition_filter,
#         'author': author_filter,
#         'language': language_filter,
#         'binding_filter': binding_filter,
#         'pages_filter': pages_filter,
#         'wishlisted_ids': wishlisted_ids,
#         'unread_count': _unread_messages_count(request.user),
#     })

def catalog(request):
    if not request.user.is_authenticated:
        messages.error(request, 'Спочатку увійдіть в акаунт')
        return redirect('home')

    query = request.GET.get('q', '').strip()
    search_in_description = request.GET.get('desc') == '1'
    genre_filter = request.GET.get('genre', '').strip()
    condition_filter = request.GET.get('condition', '').strip()
    author_filter = request.GET.get('author', '').strip()
    language_filter = request.GET.get('language', '').strip()
    binding_filter = request.GET.get('binding_filter', '').strip()
    pages_filter = request.GET.get('pages_filter', '').strip()

    listings = Listing.objects.select_related('owner').exclude(owner=request.user)

    wishlisted_ids = []
    if request.user.is_authenticated:
        wishlisted_ids = Wishlist.objects.filter(user=request.user).values_list('listing_id', flat=True)

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

    if pages_filter and pages_filter.isdigit():
        listings = listings.filter(pages__lte=int(pages_filter))

    return render(request, 'catalog.html', {
        'listings': listings,
        'query': query,
        'search_in_description': search_in_description,
        'genre_filter': genre_filter,
        'genre_choices': FAVORITE_GENRE_CHOICES,
        'condition_filter': condition_filter,
        'author_filter': author_filter,
        'language_filter': language_filter,
        'binding_filter': binding_filter,
        'pages_filter': pages_filter,
        'wishlisted_ids': wishlisted_ids,
        'unread_count': _unread_messages_count(request.user),
    })
def listing_detail(request, listing_id):
    if not request.user.is_authenticated:
        messages.error(request, 'Спочатку увійдіть в акаунт')
        return redirect('home')

    listing = get_object_or_404(Listing.objects.select_related('owner'), id=listing_id)
    is_in_wishlist = Wishlist.objects.filter(user=request.user, listing=listing).exists()

    if listing.owner_id == request.user.id:
        messages.info(request, 'Це ваше оголошення. Редагуйте його у профілі.')
        return redirect('profile')

    owner_profile = UserProfile.objects.filter(user=listing.owner).first()
    review_aggregate = listing.reviews.aggregate(avg=Avg('stars'))
    average_rating = round(review_aggregate['avg'], 1) if review_aggregate['avg'] else 0
    reviews_count = listing.reviews.count()
    user_review = ListingReview.objects.filter(listing=listing, reviewer=request.user).first()
    filled_stars = int(round(average_rating)) if average_rating else 0
    return render(request, 'listing_detail.html', {
        'listing': listing,
        'owner_profile': owner_profile,
        'is_in_wishlist': is_in_wishlist,
        'average_rating': average_rating,
        'reviews_count': reviews_count,
        'filled_stars': filled_stars,
        'user_review': user_review,
    })


@require_POST
def submit_listing_review(request, listing_id):
    if not request.user.is_authenticated:
        messages.error(request, 'Спочатку увійдіть в акаунт')
        return redirect('home')

    listing = get_object_or_404(Listing, id=listing_id)
    if listing.owner_id == request.user.id:
        messages.error(request, 'Ви не можете оцінювати власну книгу')
        return redirect('listing_detail', listing_id=listing_id)

    stars_raw = request.POST.get('stars', '').strip()
    if not stars_raw.isdigit():
        messages.error(request, 'Оберіть кількість зірок від 1 до 5')
        return redirect('listing_detail', listing_id=listing_id)

    stars = int(stars_raw)
    if stars < 1 or stars > 5:
        messages.error(request, 'Оцінка має бути від 1 до 5')
        return redirect('listing_detail', listing_id=listing_id)

    ListingReview.objects.update_or_create(
        listing=listing,
        reviewer=request.user,
        defaults={'stars': stars},
    )
    messages.success(request, 'Відгук збережено')
    return redirect('listing_detail', listing_id=listing_id)


def start_conversation(request, listing_id):
    if not request.user.is_authenticated:
        messages.error(request, 'Спочатку увійдіть в акаунт')
        return redirect('home')

    listing = get_object_or_404(Listing, id=listing_id)
    if listing.owner_id == request.user.id:
        messages.info(request, 'Це ваше оголошення')
        return redirect('profile')

    conversation = (
        Conversation.objects.filter(listing=listing, participants=request.user)
        .filter(participants=listing.owner)
        .distinct()
        .first()
    )
    if not conversation:
        conversation = Conversation.objects.create(listing=listing)
        conversation.participants.add(request.user, listing.owner)

    return redirect('conversation_detail', conversation_id=conversation.id)


def request_exchange(request, listing_id):
    if not request.user.is_authenticated:
        messages.error(request, 'Спочатку увійдіть в акаунт')
        return redirect('home')
    if request.method != 'POST':
        return redirect('listing_detail', listing_id=listing_id)

    listing = get_object_or_404(Listing, id=listing_id)
    if listing.owner_id == request.user.id:
        messages.info(request, 'Не можна надіслати запит на власну книгу')
        return redirect('profile')

    conversation = (
        Conversation.objects.filter(listing=listing, participants=request.user)
        .filter(participants=listing.owner)
        .distinct()
        .first()
    )
    if not conversation:
        conversation = Conversation.objects.create(listing=listing)
        conversation.participants.add(request.user, listing.owner)

    auto_text = (
        f"Привіт! Користувач @{request.user.username} хоче обміняти книгу "
        f"«{listing.title}». Напишіть, будь ласка, умови обміну."
    )
    Message.objects.create(conversation=conversation, sender=request.user, text=auto_text)
    conversation.save(update_fields=['updated_at'])
    return redirect('conversation_detail', conversation_id=conversation.id)


def messages_inbox(request):
    if not request.user.is_authenticated:
        return redirect('home')

    conversations = list(
        Conversation.objects.filter(participants=request.user)
        .select_related('listing')
        .prefetch_related('participants', 'messages')
        .distinct()
    )
    selected = conversations[0] if conversations else None
    if selected:
        selected.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
    conversation_rows = _build_conversation_rows(request.user, conversations)
    selected_peer = next((r['other_user'] for r in conversation_rows if selected and r['conversation'].id == selected.id), None)
    selected_peer_avatar = next((r['avatar_url'] for r in conversation_rows if selected and r['conversation'].id == selected.id), '')
    selected_messages = selected.messages.select_related('sender') if selected else []
    return render(request, 'messages.html', {
        'conversation_rows': conversation_rows,
        'selected': selected,
        'selected_peer': selected_peer,
        'selected_peer_avatar': selected_peer_avatar,
        'selected_messages': selected_messages,
        'unread_total': _unread_messages_count(request.user),
    })


def conversation_detail(request, conversation_id):
    if not request.user.is_authenticated:
        return redirect('home')

    selected = get_object_or_404(
        Conversation.objects.select_related('listing').prefetch_related('participants'),
        id=conversation_id,
        participants=request.user,
    )

    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        if text:
            Message.objects.create(conversation=selected, sender=request.user, text=text)
            selected.save(update_fields=['updated_at'])
        return redirect('conversation_detail', conversation_id=selected.id)

    selected.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)

    conversations = list(
        Conversation.objects.filter(participants=request.user)
        .select_related('listing')
        .prefetch_related('participants', 'messages')
        .distinct()
    )
    conversation_rows = _build_conversation_rows(request.user, conversations)
    selected_peer = next((r['other_user'] for r in conversation_rows if r['conversation'].id == selected.id), None)
    selected_peer_avatar = next((r['avatar_url'] for r in conversation_rows if r['conversation'].id == selected.id), '')
    selected_messages = selected.messages.select_related('sender')
    return render(request, 'messages.html', {
        'conversation_rows': conversation_rows,
        'selected': selected,
        'selected_peer': selected_peer,
        'selected_peer_avatar': selected_peer_avatar,
        'selected_messages': selected_messages,
        'unread_total': _unread_messages_count(request.user),
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
    my_wishlist = Wishlist.objects.filter(user=request.user).select_related('listing')

    selected_genres = [g for g in profile_data.favorite_genres.split(',') if g]
    favorite_genres_display = [GENRE_LABELS[g] for g in selected_genres if g in GENRE_LABELS]
    return render(request, 'profile.html', {
        'my_listings': my_listings,
        'my_wishlist': my_wishlist,
        'profile_data': profile_data,
        'genre_choices': FAVORITE_GENRE_CHOICES,
        'selected_genres': selected_genres,
        'favorite_genres_display': favorite_genres_display,
        'unread_count': _unread_messages_count(request.user),
    })

# Логіка реєстрації
def register_user(request):
    # if request.method == 'POST':
    #     username = request.POST['username']
    #     email = request.POST['email']
    #     password = request.POST['password']

    #     # Перевірка, чи існує такий юзер
    #     if User.objects.filter(username=username).exists():
    #         messages.error(request, 'Таке ім\'я вже зайняте!')
    #         return redirect('home')

    #     # Створення користувача
    #     user = User.objects.create_user(username=username, email=email, password=password)
    #     login(request, user) # Одразу входимо
    #     return redirect('catalog')

    # return redirect('home')
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Таке ім\'я вже зайняте!')
            return render(request, 'home.html', {
                'auth_open': True,
                'auth_tab': 'signup',
            })


        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user)
        return redirect('catalog')

    return render(request, 'home.html', {
        'auth_open': True,
        'auth_tab': 'signup',
    })

# Логіка входу
def login_user(request):
    # if request.method == 'POST':
    #     username = request.POST['username'] # Тут беремо дані з форми
    #     password = request.POST['password']

    #     user = authenticate(request, username=username, password=password)

    #     if user is not None:
    #         login(request, user)
    #         return redirect('catalog')
    #     else:
    #         messages.error(request, 'Невірний логін або пароль')
    #         return redirect('home')

    # return redirect('home')
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('catalog')

        messages.error(request, 'Невірний логін або пароль')
        return render(request, 'home.html', {
            'auth_open': True,
            'auth_tab': 'login',
        })

    return render(request, 'home', {
        'auth_open': True,
        'auth_tab': 'login',
    })



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
        binding_type = request.POST.get('binding_type', '').strip()

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
            binding_type=binding_type,
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


@require_POST
def report_user(request, conversation_id):
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'Not authenticated'}, status=401)

    reason = request.POST.get('reason', '').strip()
    if not reason:
        return JsonResponse({'ok': False, 'error': 'Empty reason'}, status=400)

    conversation = get_object_or_404(Conversation, id=conversation_id)
    other_user = conversation.participants.exclude(id=request.user.id).first()
    if not other_user:
        return JsonResponse({'ok': False, 'error': 'No other user'}, status=400)

    Report.objects.create(
        reporter=request.user,
        reported_user=other_user,
        conversation=conversation,
        reason=reason,
    )

    return JsonResponse({'ok': True})


def toggle_wishlist(request, listing_id):
    if not request.user.is_authenticated:
        return redirect('home')

    listing = get_object_or_404(Listing, id=listing_id)
    wish_item, created = Wishlist.objects.get_or_create(user=request.user, listing=listing)
    if not created:
        wish_item.delete()

    return redirect('listing_detail', listing_id=listing_id)
