# canteen_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # ---------- Auth & Landing ----------
    path("", views.index, name="index"),
    path("about/", views.about, name="about"),
    path("register/", views.register, name="register"),  
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # ---------- Unified Menu (Admin, Staff, Student) ----------
    # ---------- Menu ----------
    path("menu/", views.view_menu, name="view_menu"),
    path("menu/<str:meal_type>/", views.view_menu, name="view_menu_by_type"),
    # meal type


    # ---------- Student/User Module ----------
    path("user/dashboard/", views.user_dashboard, name="user_dashboard"),
    path("user/cart/", views.cart_view, name="cart_view"),
    path("user/cart/add/<int:item_id>/", views.cart_add, name="cart_add"),
    path("user/cart/clear/", views.cart_clear, name="cart_clear"),
    path("user/checkout/<str:meal_type>/", views.checkout, name="checkout"),
    path("user/tokens/", views.my_tokens, name="my_tokens"),
    path("user/reviews/", views.reviews_page, name="reviews_page"),

  # ---------- Staff Module ----------
path("staff/dashboard/", views.staff_dashboard, name="staff_dashboard"),
path("staff/menu/", views.menu_list, name="menu_list"),   # 👈 NEW
path("staff/menu/add/", views.add_menu_item, name="menu_create"),
path("staff/menu/edit/<int:pk>/", views.edit_menu_item, name="menu_edit"),
path("staff/menu/delete/<int:pk>/", views.delete_menu_item, name="menu_delete"),
path("staff/tokens/", views.tokens_today, name="tokens_today"),
path("staff/tokens/mark/<int:token_id>/", views.mark_token_used, name="mark_token_used"),


    # ---------- Admin Module ----------
    path("admin/dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("admin/reports/", views.admin_reports, name="admin_reports"),
    path("admin/reviews/", views.admin_reviews, name="admin_reviews"),
]
