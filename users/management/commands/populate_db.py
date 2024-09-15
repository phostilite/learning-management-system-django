import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from users.models import User, Role, UserRole, UserOrganizationAssignment, SCORMUserProfile, VisibilityRule, Learner, Administrator, Supervisor, Facilitator
from organization.models import Organization, OrganizationUnit, JobPosition, EmployeeProfile, Location, OrganizationContact, CustomField, CustomFieldValue, OrganizationChange, TeamMembership
from faker import Faker
import json

fake = Faker()

class Command(BaseCommand):
    help = 'Populates the database with sample organizations, users, and roles'

    def add_arguments(self, parser):
        parser.add_argument('--organizations', type=int, default=5, help='Number of organizations to create')
        parser.add_argument('--users', type=int, default=100, help='Number of users to create')

    def handle(self, *args, **options):
        num_organizations = options['organizations']
        num_users = options['users']

        self.stdout.write(self.style.SUCCESS(f'Creating {num_organizations} organizations and {num_users} users...'))

        with transaction.atomic():
            self.create_roles()
            organizations = self.create_organizations(num_organizations)
            users = self.create_users(num_users)
            self.assign_users_to_organizations(users, organizations)
            self.create_additional_data(organizations, users)

        self.stdout.write(self.style.SUCCESS('Database population completed successfully!'))

    def create_roles(self):
        roles = [
            'CEO', 'COO', 'CFO', 'CTO', 'HR Manager', 'Project Manager',
            'Team Lead', 'Senior Developer', 'Junior Developer', 'Designer',
            'Marketing Specialist', 'Sales Representative', 'Customer Support',
            'Data Analyst', 'Product Manager', 'QA Engineer'
        ]
        for role_name in roles:
            Role.objects.get_or_create(name=role_name, defaults={'description': fake.sentence()})
        self.stdout.write(self.style.SUCCESS(f'Created {len(roles)} roles'))

    def create_organizations(self, num_organizations):
        organizations = []
        for _ in range(num_organizations):
            org = Organization.objects.create(
                name=fake.company(),
                description=fake.catch_phrase(),
                website=fake.url(),
                founded_date=fake.date_this_century(before_today=True, after_today=False)
            )
            self.create_organization_units(org)
            self.create_job_positions(org)
            organizations.append(org)
        self.stdout.write(self.style.SUCCESS(f'Created {num_organizations} organizations with units and job positions'))
        return organizations

    def create_organization_units(self, org):
        departments = ['Engineering', 'Marketing', 'Sales', 'Human Resources', 'Finance', 'Operations']
        for dept in departments:
            unit = OrganizationUnit.objects.create(
                organization=org,
                name=dept,
                unit_type='DEPARTMENT',
                description=fake.bs()
            )
            # Create sub-units (teams) for each department
            for _ in range(random.randint(1, 3)):
                OrganizationUnit.objects.create(
                    organization=org,
                    name=f'{fake.word().capitalize()} Team',
                    unit_type='TEAM',
                    parent=unit,
                    description=fake.catch_phrase()
                )

    def create_job_positions(self, org):
        positions = [
            'Software Engineer', 'Marketing Specialist', 'Sales Representative',
            'HR Coordinator', 'Financial Analyst', 'Operations Manager',
            'Product Manager', 'Data Scientist', 'UX Designer', 'Customer Support Representative'
        ]
        for position in positions:
            JobPosition.objects.create(
                organization=org,
                title=position,
                description=f"{fake.sentence()} {fake.sentence()} {fake.sentence()}",  # Generate a 3-sentence description
                is_manager_position=('Manager' in position)
            )

    def create_users(self, num_users):
        users = []
        for _ in range(num_users):
            user = User.objects.create_user(
                username=fake.user_name(),
                email=fake.email(),
                password='password123',  # In a real scenario, use a strong, unique password for each user
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                phone_number=fake.numerify(text='###-###-####'),  # This ensures a 10-digit format
                gender=random.choice(['male', 'female', 'other']),
                timezone=fake.timezone()
            )
            users.append(user)
        self.stdout.write(self.style.SUCCESS(f'Created {num_users} users'))
        return users

    def assign_users_to_organizations(self, users, organizations):
        roles = list(Role.objects.all())
        for user in users:
            org = random.choice(organizations)
            unit = random.choice(OrganizationUnit.objects.filter(organization=org))
            job_position = random.choice(JobPosition.objects.filter(organization=org))
            role = random.choice(roles)

            UserOrganizationAssignment.objects.create(
                user=user,
                organization=org,
                organization_unit=unit,
                job_position=job_position,
                start_date=fake.date_this_year(before_today=True, after_today=False),
                is_active=True
            )

            UserRole.objects.create(
                user=user,
                role=role,
                organization=org,
                organization_unit=unit,
                start_date=fake.date_this_year(before_today=True, after_today=False),
                is_active=True
            )

            user.current_organization = org
            user.current_organization_unit = unit
            user.save()

        self.stdout.write(self.style.SUCCESS('Assigned users to organizations, units, and roles'))

    def create_additional_data(self, organizations, users):
        self.create_employee_profiles(users)
        self.create_locations(organizations)
        self.create_organization_contacts(organizations)
        self.create_custom_fields(organizations)
        self.create_organization_changes(organizations)
        self.create_team_memberships(users)
        self.create_scorm_user_profiles(users)
        self.create_visibility_rules()
        self.create_special_user_types(users)

    def create_employee_profiles(self, users):
        for user in users:
            EmployeeProfile.objects.create(
                user=user,
                organization=user.current_organization,
                employee_id=fake.unique.random_number(digits=6),
                hire_date=fake.date_this_decade(before_today=True, after_today=False),
                job_position=JobPosition.objects.filter(organization=user.current_organization).order_by('?').first(),
                work_phone=fake.numerify(text='###-###-####')[:20],  # Ensure it fits within 20 characters
                work_email=fake.email()[:20]  # Truncate to 20 characters
            )
        self.stdout.write(self.style.SUCCESS(f'Created {len(users)} employee profiles'))

    def create_locations(self, organizations):
        for org in organizations:
            num_locations = random.randint(1, 5)
            for _ in range(num_locations):
                Location.objects.create(
                    organization=org,
                    name=fake.city(),
                    address_line1=fake.street_address(),
                    city=fake.city(),
                    state=fake.state(),
                    country=fake.country(),
                    postal_code=fake.postcode(),
                    is_headquarters=(_ == 0)  # First location is headquarters
                )
        self.stdout.write(self.style.SUCCESS(f'Created locations for {len(organizations)} organizations'))

    def create_organization_contacts(self, organizations):
        for org in organizations:
            num_contacts = random.randint(1, 3)
            for i in range(num_contacts):
                OrganizationContact.objects.create(
                    organization=org,
                    name=fake.name()[:20],  # Limit to 20 characters
                    email=fake.email()[:20],  # Limit to 20 characters
                    phone=fake.numerify(text='###-###-####')[:20],  # Ensure it fits within 20 characters
                    position=fake.job()[:20],  # Limit to 20 characters
                    is_primary=(i == 0)  # First contact is primary
                )
        self.stdout.write(self.style.SUCCESS(f'Created contacts for {len(organizations)} organizations'))

    def create_custom_fields(self, organizations):
        field_types = ['TEXT', 'NUMBER', 'DATE', 'BOOLEAN', 'CHOICE']
        for org in organizations:
            num_fields = random.randint(2, 5)
            for _ in range(num_fields):
                field_type = random.choice(field_types)
                field = CustomField.objects.create(
                    organization=org,
                    name=fake.word()[:50],  # Assuming max_length=50 for name
                    field_type=field_type,
                    is_required=fake.boolean(),
                    choices=fake.words(5) if field_type == 'CHOICE' else None
                )
                # Create some sample values for this custom field
                for _ in range(random.randint(1, 3)):
                    CustomFieldValue.objects.create(
                        custom_field=field,
                        content_type=ContentType.objects.get_for_model(random.choice([Organization, OrganizationUnit, User])),
                        object_id=fake.uuid4(),
                        value=json.dumps(fake.word()[:100] if field_type != 'CHOICE' else random.choice(field.choices))
                    )
        self.stdout.write(self.style.SUCCESS(f'Created custom fields for {len(organizations)} organizations'))

    def create_organization_changes(self, organizations):
        change_types = ['RESTRUCTURE', 'MERGER', 'ACQUISITION', 'SPINOFF', 'RENAME']
        for org in organizations:
            num_changes = random.randint(0, 3)
            for _ in range(num_changes):
                OrganizationChange.objects.create(
                    organization=org,
                    change_type=random.choice(change_types),
                    description=fake.paragraph()[:500],  # Assuming max_length=500 for description
                    effective_date=fake.date_this_year(before_today=True, after_today=False),
                    approved_by=User.objects.order_by('?').first()
                )
        self.stdout.write(self.style.SUCCESS(f'Created organization changes for {len(organizations)} organizations'))

    def create_team_memberships(self, users):
        for user in random.sample(list(users), k=len(users) // 2):  # Assign team memberships to half of the users
            team = OrganizationUnit.objects.filter(organization=user.current_organization, unit_type='TEAM').order_by('?').first()
            if team:
                TeamMembership.objects.create(
                    employee=user.employee_profile,
                    team=team,
                    role=fake.job()[:100],  # Assuming max_length=100 for role
                    start_date=fake.date_this_year(before_today=True, after_today=False)
                )
        self.stdout.write(self.style.SUCCESS('Created team memberships'))

    def create_scorm_user_profiles(self, users):
        for user in users:
            SCORMUserProfile.objects.create(
                user=user,
                scorm_player_id=str(fake.uuid4()),  # Convert UUID to string
                token=fake.sha256()[:100]  # Assuming max_length=100 for token
            )
        self.stdout.write(self.style.SUCCESS(f'Created SCORM user profiles for {len(users)} users'))

    def create_visibility_rules(self):
        roles = Role.objects.all()
        content_types = ContentType.objects.all()
        visibility_levels = ['NONE', 'READ', 'WRITE', 'ADMIN']
        for role in roles:
            for content_type in content_types:
                VisibilityRule.objects.create(
                    role=role,
                    content_type=content_type,
                    visibility_level=random.choice(visibility_levels)
                )
        self.stdout.write(self.style.SUCCESS('Created visibility rules'))

    def create_special_user_types(self, users):
        special_users = random.sample(list(users), k=len(users) // 5)  # 20% of users get special types
        for user in special_users:
            user_type = random.choice([Learner, Administrator, Supervisor, Facilitator])
            if user_type == Learner:
                Learner.objects.create(user=user, token=fake.sha256()[:100])  # Assuming max_length=100 for token
            else:
                user_type.objects.create(user=user)
        self.stdout.write(self.style.SUCCESS('Created special user types'))