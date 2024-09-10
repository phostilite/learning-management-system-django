# File: courses/management/commands/populate_sample_data.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from courses.models import Program, Course, LearningResource, ProgramCourse, Tag, CourseCategory
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Populates the database with sample data for testing'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating sample data...')

        # Create sample users
        users = []
        for i in range(5):
            user, created = User.objects.get_or_create(
                username=f"user{i}@example.com",
                email=f"user{i}@example.com",
                defaults={'password': 'password'}
            )
            if created:
                user.set_password('password')
                user.save()
            users.append(user)

        # Create sample tags
        tags = [Tag.objects.get_or_create(name=tag)[0] for tag in ["Programming", "Data Science", "Web Development", "AI", "Machine Learning"]]

        # Create sample course categories
        categories = [CourseCategory.objects.get_or_create(name=cat)[0] for cat in ["Computer Science", "Mathematics", "Business"]]

        # Create sample programs
        programs = []
        for i in range(3):
            program, created = Program.objects.get_or_create(
                title=f"Sample Program {i+1}",
                defaults={
                    'description': f"This is a sample program description for Program {i+1}.",
                    'short_description': f"Short description for Program {i+1}",
                    'created_by': random.choice(users),
                    'is_published': True,
                    'program_type': "INTERNAL",
                    'duration': f"{random.randint(1, 12)} months",
                }
            )
            program.tags.set(random.sample(tags, k=2))
            programs.append(program)

        # Create sample courses
        courses = []
        for i in range(10):
            course, created = Course.objects.get_or_create(
                title=f"Sample Course {i+1}",
                defaults={
                    'description': f"This is a sample course description for Course {i+1}.",
                    'short_description': f"Short description for Course {i+1}",
                    'category': random.choice(categories),
                    'created_by': random.choice(users),
                    'is_published': True,
                    'duration': f"{random.randint(1, 8)} weeks",
                    'language': "English",
                    'difficulty_level': random.choice(["BEGINNER", "INTERMEDIATE", "ADVANCED"]),
                }
            )
            course.tags.set(random.sample(tags, k=2))
            courses.append(course)

        # Create sample learning resources
        for course in courses:
            for i in range(3):
                LearningResource.objects.get_or_create(
                    course=course,
                    title=f"Resource {i+1} for {course.title}",
                    defaults={
                        'description': f"Description of Resource {i+1} for {course.title}",
                        'resource_type': random.choice(["SCORM", "VIDEO", "DOCUMENT", "LINK", "QUIZ"]),
                        'order': i,
                        'is_mandatory': random.choice([True, False]),
                    }
                )

        # Create sample program courses
        for program in programs:
            for i, course in enumerate(random.sample(courses, k=random.randint(3, 5))):
                ProgramCourse.objects.get_or_create(
                    program=program,
                    course=course,
                    defaults={
                        'order': i,
                        'is_mandatory': random.choice([True, False]),
                    }
                )

        self.stdout.write(self.style.SUCCESS('Sample data has been successfully created!'))