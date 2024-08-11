from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.conf import settings
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates initial superuser, groups, and users'

    def handle(self, *args, **kwargs):
        self.create_superuser()
        self.create_groups()
        self.create_users()

    def create_superuser(self):
        username = settings.DJANGO_SUPERUSER_USERNAME
        email = settings.DJANGO_SUPERUSER_EMAIL
        password = settings.DJANGO_SUPERUSER_PASSWORD

        if not all([username, email, password]):
            self.stdout.write(self.style.ERROR("Error: Superuser credentials not found in settings."))
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f"Superuser '{username}' already exists."))
            return

        try:
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' created successfully."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred while creating the superuser: {str(e)}"))

    def create_groups(self):
        group_names = ['administrator', 'learner', 'facilitator', 'supervisor']
        for name in group_names:
            group, created = Group.objects.get_or_create(name=name)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Group '{name}' created successfully."))
            else:
                self.stdout.write(self.style.WARNING(f"Group '{name}' already exists."))

        # Commit the transaction to ensure groups are available
        transaction.commit()

    def create_users(self):
        users_data = [
            ('testadministrator@test.com', 'administrator'),
            ('testlearner@test.com', 'learner'),
            ('testfacilitator@test.com', 'facilitator'),
            ('testsupervisor@test.com', 'supervisor'),
        ]

        for username, group_name in users_data:
            self.create_user_and_profile(username, group_name)

    def create_user_and_profile(self, username, group_name):
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f"User '{username}' already exists. Skipping creation."))
            return

        try:
            user = User.objects.create_user(
                username=username,
                email=username,
                password='Test@123',
                first_name=group_name.capitalize(),
                last_name='User'
            )
            group = Group.objects.get(name=group_name)
            user.groups.add(group)
            
            # Create corresponding profile object
            if group_name == 'administrator':
                from users.models import Administrator
                Administrator.objects.get_or_create(user=user)
            elif group_name == 'learner':
                from users.models import Learner
                Learner.objects.get_or_create(user=user)
            elif group_name == 'facilitator':
                from users.models import Facilitator
                Facilitator.objects.get_or_create(user=user)
            elif group_name == 'supervisor':
                from users.models import Supervisor
                Supervisor.objects.get_or_create(user=user)

            self.stdout.write(self.style.SUCCESS(f"{group_name.capitalize()} user '{username}' created successfully."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred while creating user '{username}': {str(e)}"))