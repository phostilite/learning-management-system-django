from django.contrib import admin
from django.contrib.auth.admin import UserAdmin  

from .models import User, Learner, Administrator, Supervisor, Facilitator, SCORMUserProfile

admin.site.register(Learner)
admin.site.register(Administrator)
admin.site.register(Supervisor)
admin.site.register(Facilitator)
admin.site.register(SCORMUserProfile)

@admin.register(User)
class UserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'gender', 'picture', 'timezone')}),  
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )