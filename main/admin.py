from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from .models import Course
from .models import Enrollment
from .models import DiscussionPost


class CustomUserAdmin(UserAdmin):
    """Custom admin for User model"""
    model = User
    list_display = ('username', 'email', 'role', 'is_staff', 'created_at')
    list_filter = ('role', 'is_staff', 'is_active', 'created_at')
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('role', 'bio', 'profile_picture')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom Fields', {'fields': ('role',)}),
    )
    ordering = ('-created_at',)


admin.site.register(User, CustomUserAdmin)

class CourseAdmin(admin.ModelAdmin):
    """Admin for Course model"""
    list_display = ('title', 'instructor', 'is_published', 'max_students', 'created_at')
    list_filter = ('is_published', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')


admin.site.register(Course, CourseAdmin)


class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'enrolled_at')
    search_fields = ('student__username', 'course__title')
    list_filter = ('enrolled_at',)


admin.site.register(Enrollment, EnrollmentAdmin)


class DiscussionPostAdmin(admin.ModelAdmin):
    list_display = ('course', 'author', 'created_at')
    search_fields = ('course__title', 'author__username', 'body')


admin.site.register(DiscussionPost, DiscussionPostAdmin)
