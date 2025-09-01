from collections import defaultdict
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.db.models import Count
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid
from .models import User, MenuItem, MealToken, Review, Order, OrderItem
from .forms import MenuForm, RegisterForm
from collections import defaultdict


# =====================
# Role Check Helpers
# =====================
def is_admin(user):
    return user.is_authenticated and user.role == "admin"

def is_canteen_staff(user):
    return user.is_authenticated and user.role == "staff"

def is_student(user):
    return user.is_authenticated and user.role == "student"


# =====================
# Landing & Auth
# =====================
def index(request):
    return render(request, "index.html")

def about(request):
    return render(request, "about.html")

def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully! Please log in.")
            return redirect("login")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = RegisterForm()
    return render(request, "register.html", {"form": form})

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # ✅ Role-based redirection
            if user.role == "admin":
                return redirect("admin_dashboard")
            elif user.role == "staff":
                return redirect("staff_dashboard")
            elif user.role == "student":
                return redirect("user_dashboard")
            else:
                messages.error(request, "Role not recognized.")
                return redirect("login")
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, "login.html")

def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully")
    return redirect("login")


# =====================
# Menu (Shared)
# =====================
from collections import defaultdict

@login_required
def view_menu(request, category=None):
    if request.user.role in ["admin", "staff"]:
        menu_items = MenuItem.objects.all()
    else:
        menu_items = MenuItem.objects.filter(available=True)

    # Group items by category
    categorized_items = defaultdict(list)
    for item in menu_items:
        categorized_items[item.category].append(item)

    return render(request, "menu/view_menu.html", {
        "categorized_items": dict(categorized_items),  # ✅ very important
        "selected_category": category.title() if category else "All",
    })


# =====================
# Student/User Views
# =====================
@login_required
@user_passes_test(is_student)
def user_dashboard(request):
    today = timezone.localdate()
    # students see today’s available items only
    menu_items = MenuItem.objects.filter(date_available=today, available=True)
    tokens = MealToken.objects.filter(order__user=request.user).order_by('-generated_at', 'status')

    context = {
        "tokens": tokens,
        "menu_items": menu_items,
        "selected_category": "All",
    }
    return render(request, "customer/user_dashboard.html", context)


@login_required
@user_passes_test(is_student)
def cart_add(request, item_id):
    cart = request.session.get("cart", {})
    item_id_str = str(item_id)
    cart[item_id_str] = cart.get(item_id_str, 0) + 1
    request.session["cart"] = cart
    messages.success(request, "Item added to cart.")
    return redirect("cart_view")


@login_required
@user_passes_test(is_student)
def cart_view(request):
    cart = request.session.get("cart", {})
    items, total = [], 0

    for item_id, quantity in cart.items():
        menu_item = get_object_or_404(MenuItem, pk=int(item_id))
        item_total = menu_item.price * quantity
        items.append({"item": menu_item, "quantity": quantity, "total": item_total})
        total += item_total

    return render(request, "customer/cart.html", {"items": items, "total": total})


@login_required
@user_passes_test(is_student)
def cart_remove(request, item_id):
    cart = request.session.get("cart", {})
    item_id_str = str(item_id)

    if item_id_str in cart:
        if cart[item_id_str] > 1:
            cart[item_id_str] -= 1
        else:
            del cart[item_id_str]

    request.session["cart"] = cart
    messages.success(request, "Item removed from cart.")
    return redirect("cart_view")


@login_required
@user_passes_test(is_student)
def cart_clear(request):
    request.session["cart"] = {}
    messages.success(request, "Cart cleared.")
    return redirect("cart_view")


@login_required
@user_passes_test(is_student)
def checkout(request, meal_type):
    cart = request.session.get("cart", {})
    if not cart:
        messages.error(request, "Your cart is empty!")
        return redirect("view_menu")

    order = Order.objects.create(user=request.user)

    for item_id, quantity in cart.items():
        menu_item = get_object_or_404(MenuItem, pk=int(item_id))
        OrderItem.objects.create(
            order=order,
            menu_item=menu_item,
            quantity=quantity,
            price=menu_item.price
        )

    request.session["cart"] = {}
    messages.success(request, "Order placed successfully! Token has been generated.")
    return redirect("my_tokens")


@login_required
@user_passes_test(is_student)
def my_tokens(request):
    tokens = MealToken.objects.filter(order__user=request.user).order_by('-generated_at', 'status')
    return render(request, "customer/my_tokens.html", {"tokens": tokens})


@login_required
@user_passes_test(is_student)
def reviews_page(request):
    reviews = Review.objects.filter(visible=True)
    return render(request, "customer/reviews.html", {"reviews": reviews})


# =====================
# Signals
# =====================
@receiver(post_save, sender=Order)
def create_meal_token(sender, instance, created, **kwargs):
    if created:
        token_code = str(uuid.uuid4())[:8].upper()
        MealToken.objects.create(
            order=instance,
            code=token_code,
            status="PENDING"   # use your TokenStatus.PENDING
)

        


# =====================
# Staff Views
# =====================
@login_required
@user_passes_test(is_canteen_staff)
def staff_dashboard(request):
    categorized_items = defaultdict(list)
    for item in MenuItem.objects.all():
        categorized_items[item.category].append(item)

    return render(request, "staff/staff_dashboard.html", {"categorized_items": categorized_items})

@login_required
@user_passes_test(is_canteen_staff)
def menu_list(request):
    categorized_items = defaultdict(list)
    for item in MenuItem.objects.all().order_by("category", "name"):
        categorized_items[item.category].append(item)

    return render(request, "staff/menu_list.html", {
        "categorized_items": dict(categorized_items)
    })



from django.contrib import messages

@login_required
@user_passes_test(is_canteen_staff)
def add_menu_item(request):
    if request.method == "POST":
        form = MenuForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Item added successfully!")
            return redirect("menu_list")  # change to your menu page
        else:
            messages.error(request, "❌ Please correct the errors below.")
    else:
        form = MenuForm()
    return render(request, "staff/add_menu_item.html", {"form": form})


@login_required
def edit_menu_item(request, menu_id):
    # ✅ Permission check
    if request.user.role not in ["admin", "staff"]:
        messages.error(request, "You do not have permission to edit menu items.")
        return redirect("view_menu")

    item = get_object_or_404(MenuItem, id=menu_id)

    if request.method == "POST":
        form = MenuForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, f'"{item.name}" updated successfully!')
            return redirect("view_menu")
    else:
        form = MenuForm(instance=item)

    # ✅ Pass the item too (useful in template heading)
    return render(request, "staff/edit_menu_item.html", {"form": form, "item": item})



@login_required
def delete_menu_item(request, menu_id):
    if request.user.role not in ["admin", "staff"]:
        messages.error(request, "You do not have permission to delete menu items.")
        return redirect("view_menu")

    menu = get_object_or_404(MenuItem, id=menu_id)
    menu.delete()
    messages.success(request, "Menu item deleted successfully!")
    return redirect("view_menu")

@login_required
@user_passes_test(is_canteen_staff)
def tokens_today(request):
    today = timezone.localdate()
    tokens = MealToken.objects.filter(generated_at__date=today).order_by("order__order_date")
    return render(request, "staff/tokens_today.html", {"tokens": tokens})



@login_required
@user_passes_test(is_canteen_staff)
def mark_token_used(request, token_id):
    if request.method == "POST":
        token = get_object_or_404(MealToken, pk=token_id)
        token.mark_used(staff_user=request.user)

        if token.order.status == "PLACED":
            token.order.status = "COMPLETED"
            token.order.save()

        messages.success(request, f"Token {token.code} marked as used. ✅")

    return redirect("tokens_today")


# =====================
# Admin Views
# =====================
@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    today = timezone.localdate()
    daily_menus = MenuItem.objects.filter(date_available=today).order_by("category")
    total_tokens = MealToken.objects.filter(generated_at__date=today).count()

    context = {
        "menus": daily_menus,
        "total_tokens": total_tokens,
        "today": today,
    }
    return render(request, "admin/admin_dashboard.html", context)


@login_required
@user_passes_test(is_admin)
def admin_reports(request):
    report = (
        MealToken.objects
        .values("generated_at__date", "meal_type", "status")
        .annotate(count=Count("id"))
        .order_by("-generated_at__date", "meal_type")
    )
    return render(request, "admin/reports.html", {"report": report})


@login_required
@user_passes_test(is_admin)
def admin_reviews(request):
    if request.method == "POST":
        review_id = request.POST.get("review_id")
        review = get_object_or_404(Review, pk=review_id)
        review.visible = not review.visible
        review.save()
        return redirect("admin_reviews")

    reviews = Review.objects.all().order_by("-created_at")
    return render(request, "admin/reviews.html", {"reviews": reviews})
