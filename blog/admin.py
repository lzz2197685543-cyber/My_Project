from django.contrib import admin
from .models import Category, Post


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'created_at', 'updated_at', 'total_favorites']
    list_filter = ['category', 'created_at']
    search_fields = ['title', 'summary']
    date_hierarchy = 'created_at'
    list_per_page = 20
    prepopulated_fields = {'slug': ('title',)}

    def total_favorites(self, obj):
        return obj.total_favorites()

    total_favorites.short_description = '收藏数'