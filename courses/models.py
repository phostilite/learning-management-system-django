# courses/models.py

from django.conf import settings
from django.db import models
import uuid
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
import dateutil.relativedelta

User = get_user_model()

class Program(models.Model):
    PROGRAM_TYPES = (
        ('INTERNAL', 'Internal'),
        ('EXTERNAL', 'External'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    short_description = models.CharField(max_length=500, blank=True)
    cover_image = models.ImageField(upload_to='program_covers/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_programs')
    is_published = models.BooleanField(default=False)
    program_type = models.CharField(max_length=10, choices=PROGRAM_TYPES, default='INTERNAL', null=True, blank=True)
    duration = models.CharField(max_length=100, null=True, blank=True)
    level = models.CharField(max_length=50, null=True, blank=True)
    
    provider = models.CharField(max_length=255, null=True, blank=True)
    exam_code = models.CharField(max_length=50, null=True, blank=True)
    exam_link = models.URLField(null=True, blank=True)

    tags = models.ManyToManyField('Tag', blank=True)
    prerequisites = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='required_for')

    def __str__(self):
        return self.title

class Course(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    short_description = models.CharField(max_length=500, blank=True)
    category = models.ForeignKey('CourseCategory', on_delete=models.SET_NULL, null=True)
    cover_image = models.ImageField(upload_to='course_covers/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_courses')
    is_published = models.BooleanField(default=False)
    scorm_url = models.URLField(null=True, blank=True)
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='courses', null=True, blank=True)
    duration = models.CharField(max_length=100, blank=True)

    tags = models.ManyToManyField('Tag', blank=True)
    prerequisites = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='required_for')
    language = models.CharField(max_length=50, null=True, blank=True)
    difficulty_level = models.CharField(max_length=20, choices=[
        ('BEGINNER', 'Beginner'),
        ('INTERMEDIATE', 'Intermediate'),
        ('ADVANCED', 'Advanced')
    ], null=True, blank=True)

    def __str__(self):
        return self.title
    
class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
class ProgramCourse(models.Model):
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('program', 'course')
        ordering = ['order']

    def __str__(self):
        return f"{self.program.title} - {self.course.title}"
    
class ProgramEnrollment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    enrollment_date = models.DateTimeField(auto_now_add=True)
    completion_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('ENROLLED', 'Enrolled'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('WITHDRAWN', 'Withdrawn'),
    ], default='ENROLLED')

    class Meta:
        unique_together = ('user', 'program')

    def __str__(self):
        return f"{self.user.username} - {self.program.title}"

class CourseCategory(models.Model):
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
    )

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)  # Adding a description field
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Course Categories"

class LearningResource(models.Model):
    RESOURCE_TYPES = (
        ('SCORM', 'SCORM Package'),
        ('VIDEO', 'Video'),
        ('DOCUMENT', 'Document'),
        ('PRESENTATION', 'Presentation'),
        ('LINK', 'External Link'),
        ('QUIZ', 'Quiz'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='resources')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES)
    content = models.FileField(upload_to='course_resources/', null=True, blank=True)
    external_url = models.URLField(null=True, blank=True)
    launch_url = models.URLField(null=True, blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.title} ({self.get_resource_type_display()})"
    
    def get_learning_progress(self, user):
        try:
            enrollment = Enrollment.objects.get(user=user, course_delivery__course=self.course)
            progress = LearningProgress.objects.get(enrollment=enrollment, resource=self)
            return progress
        except (Enrollment.DoesNotExist, LearningProgress.DoesNotExist):
            return None
        
class ExternalProgramProgress(models.Model):
    enrollment = models.OneToOneField('ProgramEnrollment', on_delete=models.CASCADE)
    exam_status = models.CharField(max_length=20, choices=[
        ('NOT_STARTED', 'Not Started'),
        ('IN_PROGRESS', 'In Progress'),
        ('PASSED', 'Passed'),
        ('FAILED', 'Failed')
    ], default='NOT_STARTED')
    exam_date = models.DateField(null=True, blank=True)
    certificate_file = models.FileField(upload_to='external_certificates/', null=True, blank=True)

    def __str__(self):
        return f"External Progress for {self.enrollment}"

class ScormResource(models.Model):
    learning_resource = models.OneToOneField(LearningResource, on_delete=models.CASCADE, related_name='scorm_details')
    scorm_course_id = models.CharField(max_length=50, unique=True)
    scorm_package_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    version = models.CharField(max_length=50)
    web_path = models.CharField(max_length=255)

    def __str__(self):
        return f"SCORM: {self.learning_resource.title}"
    
class ScormRegistration(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrollment = models.OneToOneField('Enrollment', on_delete=models.CASCADE, related_name='scorm_registration')
    scorm_registration_id = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"SCORM Registration for {self.enrollment}"

class CourseDelivery(models.Model):
    DELIVERY_TYPES = (
        ('SELF_PACED', 'Self Paced'),
        ('INSTRUCTOR_LED', 'Instructor Led'),
    )
    ENROLLMENT_TYPES = (
        ('OPEN', 'Open Enrollment'),
        ('INVITE', 'By Invitation'),
    )
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('ARCHIVED', 'Archived'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='deliveries')
    title = models.CharField(max_length=255)
    delivery_code = models.CharField(max_length=50, unique=True)
    delivery_type = models.CharField(max_length=20, choices=DELIVERY_TYPES)
    enrollment_type = models.CharField(max_length=20, choices=ENROLLMENT_TYPES)
    facilitators = models.ManyToManyField(User, related_name='facilitated_deliveries')
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    max_participants = models.PositiveIntegerField(null=True, blank=True)
    is_mandatory = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_deliveries')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')

    def __str__(self):
        return f"{self.title} ({self.delivery_code})"

    def duration(self):
        if not self.start_date or not self.end_date:
            return "Not available"

        delta = self.end_date - self.start_date
        if delta < timedelta(days=1):
            hours = delta.total_seconds() // 3600
            return f"{hours} Hours" if hours != 1 else "1 Hour"

        if delta < timedelta(weeks=1):
            days = delta.days
            return f"{days} Days" if days != 1 else "1 Day"

        diff = dateutil.relativedelta.relativedelta(self.end_date, self.start_date)
        years, months, weeks, days = diff.years, diff.months, diff.weeks, diff.days

        readable = []
        if years:
            readable.append(f"{years} Years" if years != 1 else "1 Year")
        if months:
            readable.append(f"{months} Months" if months != 1 else "1 Month")
        if weeks:
            readable.append(f"{weeks} Weeks" if weeks != 1 else "1 Week")
        if days:
            readable.append(f"{days} Days" if days != 1 else "1 Day")

        return ", ".join(readable)

class Enrollment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course_delivery = models.ForeignKey(CourseDelivery, on_delete=models.CASCADE)
    enrollment_date = models.DateTimeField(auto_now_add=True)
    completion_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('ENROLLED', 'Enrolled'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('WITHDRAWN', 'Withdrawn'),
    ], default='ENROLLED')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        unique_together = ('user', 'course_delivery')

    def __str__(self):
        return f"{self.user.username} - {self.course_delivery.title}"

class LearningProgress(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE)
    resource = models.ForeignKey(LearningResource, on_delete=models.CASCADE)
    start_date = models.DateTimeField(null=True, blank=True)
    completion_date = models.DateTimeField(null=True, blank=True)
    progress = models.FloatField(default=0)  # 0 to 100
    is_completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('enrollment', 'resource')

    def __str__(self):
        return f"{self.enrollment.user.username} - {self.resource.title}"

class Feedback(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField()
    comments = models.TextField()
    submission_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('enrollment',)

    def __str__(self):
        return f"Feedback for {self.enrollment.course_delivery.title} by {self.enrollment.user.username}"

class Attendance(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE)
    date = models.DateField()
    is_present = models.BooleanField(default=False)

    class Meta:
        unique_together = ('enrollment', 'date')

    def __str__(self):
        return f"{self.enrollment.user.username} - {self.enrollment.course_delivery.title} - {self.date}"