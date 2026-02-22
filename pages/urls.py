from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('catalog/', views.catalog, name='catalog'),
    path('catalog/listing/<int:listing_id>/', views.listing_detail, name='listing_detail'),
    path('users/<int:user_id>/', views.user_profile_view, name='user_profile'),
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('settings/', views.settings_page, name='settings'),
    path('register/', views.register_user, name='register'), # Адреса для реєстрації
    path('login/', views.login_user, name='login_user'),     # Адреса для входу
    path('logout/', views.logout_user, name='logout_user'),
    path('listings/create/', views.create_listing, name='create_listing'),
    path('listings/<int:listing_id>/edit/', views.edit_listing, name='edit_listing'),
    path('listings/<int:listing_id>/delete/', views.delete_listing, name='delete_listing'),
    path('wishlist/toggle/<int:listing_id>/', views.toggle_wishlist, name='toggle_wishlist'),
]
