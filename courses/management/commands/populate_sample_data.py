import random
import uuid
from django.core.management.base import BaseCommand
from faker import Faker
from courses.models import Course, Program, CourseCategory, Tag, Review
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate the database with fake courses and programs'

    def generate_unique_words(self, fake, count):
        """Generate a list of unique words"""
        words = set()
        while len(words) < count:
            words.add(fake.unique.word())
        return list(words)

    def handle(self, *args, **kwargs):
        fake = Faker()

        # Create fake users
        users = [User.objects.create(username=fake.unique.user_name(), email=fake.unique.email()) for _ in range(5)]

        # Create fake course categories with unique names
        category_names = self.generate_unique_words(fake, 5)
        categories = [CourseCategory.objects.create(name=name) for name in category_names]

        # Create fake tags with unique names
        tag_names = self.generate_unique_words(fake, 10)
        tags = [Tag.objects.create(name=name) for name in tag_names]

        # Create fake courses
        created_courses = []
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
            course.tags.set(random.sample(tags, random.randint(1, 3)))
            created_courses.append(course)

            # Add prerequisites only if there are enough courses to sample from
            existing_courses = created_courses[:-1]  # Exclude the current course
            if len(existing_courses) >= 2:
                course.prerequisites.set(random.sample(existing_courses, random.randint(1, min(2, len(existing_courses)))))
            course.save()

        # Create fake programs
        created_programs = []
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
            program.tags.set(random.sample(tags, random.randint(1, 3)))
            created_programs.append(program)

            # Add prerequisites only if there are enough programs to sample from
            existing_programs = created_programs[:-1]  # Exclude the current program
            if len(existing_programs) >= 2:
                program.prerequisites.set(random.sample(existing_programs, random.randint(1, min(2, len(existing_programs)))))
            program.save()

        self.stdout.write(self.style.SUCCESS('Successfully populated the database with fake courses and programs'))