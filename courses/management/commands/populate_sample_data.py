import random
import uuid
from django.core.management.base import BaseCommand
from faker import Faker
from courses.models import Course, Program, CourseCategory, Tag, Review
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate the database with fake courses and programs'

    def handle(self, *args, **kwargs):
        fake = Faker()

        # Create fake users
        users = [User.objects.create(username=fake.user_name(), email=fake.email()) for _ in range(5)]

        # Create fake course categories
        categories = [CourseCategory.objects.create(name=fake.word()) for _ in range(5)]

        # Create fake tags
        tags = [Tag.objects.create(name=fake.word()) for _ in range(10)]

        # Create fake courses
        for _ in range(10):
            course = Course.objects.create(
                id=uuid.uuid4(),
                title=fake.sentence(nb_words=4),
                description=fake.text(),
                short_description=fake.sentence(nb_words=10),
                category=random.choice(categories),
                cover_image=None,
                created_by=random.choice(users),
                is_published=fake.boolean(),
                duration=fake.time(),
                language=fake.language_name(),
                difficulty_level=random.choice(['BEGINNER', 'INTERMEDIATE', 'ADVANCED']),
            )
            course.tags.set(random.sample(tags, 3))
            course.prerequisites.set(random.sample(list(Course.objects.all()), 2))
            course.save()

        # Create fake programs
        for _ in range(10):
            program = Program.objects.create(
                id=uuid.uuid4(),
                title=fake.sentence(nb_words=4),
                description=fake.text(),
                short_description=fake.sentence(nb_words=10),
                cover_image=None,
                created_by=random.choice(users),
                is_published=fake.boolean(),
                program_type=random.choice(['INTERNAL', 'EXTERNAL']),
                duration=fake.time(),
                level=fake.word(),
                provider=fake.company(),
                exam_code=fake.bothify(text='??-####'),
                exam_link=fake.url(),
            )
            program.tags.set(random.sample(tags, 3))
            program.prerequisites.set(random.sample(list(Program.objects.all()), 2))
            program.save()

        self.stdout.write(self.style.SUCCESS('Successfully populated the database with fake courses and programs'))