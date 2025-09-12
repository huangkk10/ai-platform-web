from django.contrib import admin
from .models import UserProfile, Project, Task, Employee, KnowIssue


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'location', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__username', 'user__email', 'location')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at', 'updated_at')
    search_fields = ('name', 'description', 'owner__username')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('members',)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'assignee', 'status', 'priority', 'due_date', 'created_at')
    list_filter = ('status', 'priority', 'project', 'created_at', 'due_date')
    search_fields = ('title', 'description', 'project__name')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'position', 'email', 'is_active', 'hire_date')
    list_filter = ('department', 'position', 'is_active', 'hire_date')
    search_fields = ('name', 'email', 'department', 'position', 'skills')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'hire_date'


@admin.register(KnowIssue)
class KnowIssueAdmin(admin.ModelAdmin):
    list_display = ('issue_id', 'project', 'issue_type', 'status', 'test_version', 'updated_by', 'updated_at')
    list_filter = ('issue_type', 'status', 'project', 'created_at', 'updated_at')
    search_fields = ('issue_id', 'project', 'jira_number', 'error_message', 'supplement')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('基本資訊', {
            'fields': ('issue_id', 'test_version', 'jira_number', 'updated_by', 'project')
        }),
        ('技術資訊', {
            'fields': ('issue_type', 'status', 'script')
        }),
        ('問題描述', {
            'fields': ('error_message', 'supplement')
        }),
        ('時間資訊', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # 新建時
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)