# canteen_app/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import random
import string


# -------------------
# Custom User Model
# -------------------
class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('staff', 'Staff'),
        ('student', 'Student'),
    )
    phone = models.CharField(max_length=15, blank=True, default="9999999999")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.role})"


# -------------------
# Menu Items
# -------------------
class MealType(models.TextChoices):
    BREAKFAST = "breakfast", "Breakfast"
    LUNCH = "lunch", "Lunch"
    DINNER = "dinner", "Dinner"
    SNACKS = "snacks", "Snacks"
    DRINKS = "drinks", "Drinks"


# models.py
class MenuItem(models.Model):
    CATEGORY_CHOICES = [
    ('breakfast', 'Breakfast'),
    ('lunch', 'Lunch'),
    ('snacks', 'Snacks'),
    ('drinks', 'Drinks'),
]
   
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("ready", "Ready"),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    image = models.ImageField(upload_to="menu_images/", blank=True, null=True)  # fixed upload path
    available = models.BooleanField(default=True)
    date_available = models.DateField(default=timezone.now, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.category})"





# -------------------
# Orders & Cart
# -------------------
class Order(models.Model):
    MEAL_TYPES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('snacks', 'Snacks'),
        ('dinner', 'Dinner'),
    ]
    
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("preparing", "Preparing"),
        ("ready", "Ready for Pickup"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    order_date = models.DateTimeField(auto_now_add=True)
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPES)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"

    def calculate_total(self):
        """Calculate the total amount for this order"""
        total = sum(item.subtotal() for item in self.items.all())
        self.total_amount = total
        self.save()
        return total


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of order

    def subtotal(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.menu_item.name}"

    def save(self, *args, **kwargs):
        # Set the price to the current menu item price when saving
        if not self.price:
            self.price = self.menu_item.price
        super().save(*args, **kwargs)
        # Update the order total
        self.order.calculate_total()


# -------------------
# Meal Tokens
# -------------------
class TokenStatus(models.TextChoices):
    PENDING = "PENDING", "Pending/Unserved"
    USED = "USED", "Used"
    EXPIRED = "EXPIRED", "Expired"


class MealToken(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="meal_token")
    code = models.CharField(max_length=10, unique=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=10, choices=TokenStatus.choices, default=TokenStatus.PENDING
    )
    served_at = models.DateTimeField(null=True, blank=True)
    served_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="served_tokens",
    )

    def mark_used(self, staff_user):
        self.status = TokenStatus.USED
        self.served_at = timezone.now()
        self.served_by = staff_user
        self.save()

    def __str__(self):
        return f"Token {self.code} for Order #{self.order.id}"

    # -------------------
    # Helper function to generate token code
    # -------------------
    @staticmethod
    def generate_token_code(length=8):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_token_code()
        super().save(*args, **kwargs)


# -------------------
# Reviews
# -------------------
class Review(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    visible = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Review by {self.user} ★{self.rating}"