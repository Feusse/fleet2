from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Tenant, User


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ["nom_agence", "slug_unique", "ville", "plan_abonnement", "date_creation"]
    search_fields = ["nom_agence", "slug_unique"]


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ["username", "email", "tenant", "role", "is_staff"]
    fieldsets = UserAdmin.fieldsets + (
        ("Fleet.cm", {"fields": ("tenant", "role", "telephone")}),
    )
