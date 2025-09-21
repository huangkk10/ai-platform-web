from django.contrib import admin
from .models import UserProfile, Project, Task, Employee, DifyEmployee, KnowIssue, ChatUsage


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
    list_display = ('name', 'created_at', 'updated_at')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(DifyEmployee)
class DifyEmployeeAdmin(admin.ModelAdmin):
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
        # 由於 updated_by 現在指向 Employee 而非 User，暫時移除自動設定
        # 管理員需要手動選擇員工
        super().save_model(request, obj, form, change)


@admin.register(ChatUsage)
class ChatUsageAdmin(admin.ModelAdmin):
    list_display = ('user', 'chat_type', 'message_count', 'has_file_upload', 'response_time', 'created_at')
    list_filter = ('chat_type', 'has_file_upload', 'created_at', 'user')
    search_fields = ('user__username', 'session_id', 'ip_address')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('基本資訊', {
            'fields': ('user', 'session_id', 'chat_type', 'message_count')
        }),
        ('使用詳情', {
            'fields': ('has_file_upload', 'response_time')
        }),
        ('技術資訊', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('時間資訊', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )