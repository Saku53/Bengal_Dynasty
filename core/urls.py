from django.urls import path
from . import views
from core.views import logout_view

urlpatterns = [
    path('', views.frontpage, name='frontpage'),  # Home page at /
    path('products/', views.product_list, name='product_list'),  # Product list page at /products/
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('add-to-cart/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('checkout/', views.checkout, name='checkout'),
    path('favorite/add/<int:product_id>/', views.add_favorite, name='add_favorite'),
    path('favorite/remove/<int:product_id>/', views.remove_favorite, name='remove_favorite'),
    path('favorites/', views.favorite_list, name='favorite_list'),
    path('profile/', views.user_profile, name='user_profile'),
    path('profile/info/', views.profile_info, name='profile_info'),
    path('profile/orders/', views.order_history, name='order_history'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('not-auth/', views.not_authenticated, name='not_authenticated'),
    path('logout/', logout_view, name='logout'),
    path('signup/', views.signup, name='signup'),
    
]