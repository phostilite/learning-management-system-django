import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.db import IntegrityError, transaction
from django.contrib.contenttypes.models import ContentType
from faker import Faker
from users.models import User, SCORMUserProfile
from organization.models import (
    Organization,
    OrganizationUnit,
    Location,
    JobPosition,
    EmployeeProfile,
    OrganizationContact,
    CustomField,
    CustomFieldValue,
    OrganizationChange,
    TeamMembership
)
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Populates the database with sample data using Faker'

    def handle(self, *args, **options):
        fake = Faker()
        
        # Create groups
        groups = ['administrator', 'learner', 'facilitator', 'instructor']
        for group_name in groups:
            Group.objects.get_or_create(name=group_name)
        
        # Create organization
        organization, _ = Organization.objects.get_or_create(
            name='Acme Inc.',
            defaults={
                'legal_name': 'Acme Incorporated',
                'tax_id': fake.ssn(),
                'registration_number': fake.ssn(),
                'founded_date': fake.date_between(start_date='-30y', end_date='today'),
                'description': fake.paragraph(),
                'website': fake.url(),
                'industry': fake.job(),
                'logo': None,
            }
        )
        
        # Create organization units
        unit_types = ['COMPANY', 'DIVISION', 'DEPARTMENT', 'TEAM', 'SUB_TEAM', 'PROJECT', 'OTHER']
        parent_units = []
        for _ in range(10):
            unit_type = random.choice(unit_types)
            parent = random.choice(parent_units) if parent_units else None
            try:
                with transaction.atomic():
                    unit = OrganizationUnit.objects.create(
                        organization=organization,
                        name=fake.job(),
                        unit_type=unit_type,
                        code=fake.ssn()[:10],
                        parent=parent,
                    )
                    parent_units.append(unit)
            except IntegrityError:
                logger.warning(f"Skipped creating duplicate organization unit: {unit.name}")
        
        # Create locations
        for _ in range(5):
            Location.objects.get_or_create(
                organization=organization,
                name=fake.city(),
                defaults={
                    'address_line1': fake.street_address(),
                    'address_line2': fake.secondary_address(),
                    'city': fake.city(),
                    'state': fake.state(),
                    'country': fake.country(),
                    'postal_code': fake.postcode(),
                    'latitude': fake.latitude(),
                    'longitude': fake.longitude(),
                    'is_headquarters': False,
                }
            )
        
        # Create job positions
        levels = list(range(1, 6))
        for _ in range(10):
            JobPosition.objects.get_or_create(
                organization=organization,
                title=fake.job(),
                defaults={
                    'code': fake.ssn()[:10],
                    'description': fake.paragraph(),
                    'is_manager_position': fake.boolean(chance_of_getting_true=25),
                    'level': random.choice(levels),
                }
            )
        
        # Create users and employee profiles
        job_positions = list(JobPosition.objects.all())
        organization_units = list(OrganizationUnit.objects.all())
        groups = Group.objects.all()

        for _ in range(50):
            user = User.objects.create_user(
                username=fake.user_name(),
                email=fake.email(),
                password='password',
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                phone_number=fake.phone_number()[:15],
                gender=random.choice(['male', 'female', 'other']),
                picture=None,
                timezone=fake.timezone(),
            )
            user.groups.add(random.choice(groups))

            SCORMUserProfile.objects.create(
                user=user,
                scorm_player_id=fake.uuid4(),
            )

            EmployeeProfile.objects.create(
                user=user,
                organization=organization,
                employee_id=fake.ssn()[:10],
                job_position=random.choice(job_positions),
                organization_unit=random.choice(organization_units),
                manager=None,  # Assign managers later
                hire_date=fake.date_between(start_date='-10y', end_date='today'),
                termination_date=None,
                is_active=fake.boolean(chance_of_getting_true=80),
                work_phone=fake.phone_number()[:20],
                work_email=fake.company_email(),
            )
        
        # Assign managers to employee profiles
        employee_profiles = list(EmployeeProfile.objects.all())
        for profile in employee_profiles:
            if not profile.manager:
                profile.manager = random.choice(employee_profiles).user
                profile.save()
        
        # Create organization contacts
        for _ in range(5):
            OrganizationContact.objects.create(
                organization=organization,
                name=fake.name(),
                email=fake.email(),
                phone=fake.phone_number()[:20],
                position=fake.job(),
                is_primary=fake.boolean(chance_of_getting_true=20),
            )
        
        # Create custom fields and values
        field_types = ['TEXT', 'NUMBER', 'DATE', 'BOOLEAN', 'CHOICE']
        for _ in range(5):
            field_type = random.choice(field_types)
            choices = [fake.word() for _ in range(3)] if field_type == 'CHOICE' else None
            custom_field = CustomField.objects.create(
                organization=organization,
                name=fake.word(),
                field_type=field_type,
                is_required=fake.boolean(chance_of_getting_true=30),
                choices=choices,
            )
            for profile in employee_profiles:
                if field_type == 'TEXT':
                    value = fake.sentence()
                elif field_type == 'NUMBER':
                    value = fake.random_int(min=0, max=100)
                elif field_type == 'DATE':
                    value = fake.date_between(start_date='-10y', end_date='today').isoformat()
                elif field_type == 'BOOLEAN':
                    value = fake.boolean()
                else:  # CHOICE
                    value = random.choice(choices)
                CustomFieldValue.objects.create(
                    custom_field=custom_field,
                    content_type=ContentType.objects.get_for_model(EmployeeProfile),
                    object_id=profile.id,
                    value=value,
                )
        
        # Create organization changes
        change_types = ['RESTRUCTURE', 'MERGER', 'ACQUISITION']
        for _ in range(3):
            OrganizationChange.objects.create(
                organization=organization,
                change_type=random.choice(change_types),
                description=fake.paragraph(),
                effective_date=fake.date_between(start_date='-5y', end_date='today'),
                approved_by=random.choice(employee_profiles).user,
            )
        
        # Create team memberships
        teams = OrganizationUnit.objects.filter(unit_type='TEAM')
        for profile in employee_profiles:
            for _ in range(random.randint(0, 2)):
                team = random.choice(teams)
                TeamMembership.objects.create(
                    employee=profile,
                    team=team,
                    role=fake.job(),
                    start_date=fake.date_between(start_date='-5y', end_date='today'),
                    end_date=None,
                    is_active=fake.boolean(chance_of_getting_true=80),
                )
        
        logger.info("Database populated with sample data.")