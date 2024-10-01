from django.conf import settings
from django.db import models
import uuid
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()

class Review(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type', 'object_id')
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'content_type', 'object_id']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f"Review by {self.user.username} for {self.content_object}"

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
    program_type = models.CharField(max_length=10, choices=PROGRAM_TYPES, default='INTERNAL')
    duration = models.CharField(max_length=100, null=True, blank=True)
    level = models.CharField(max_length=50, null=True, blank=True)
    provider = models.CharField(max_length=255, null=True, blank=True)
    exam_code = models.CharField(max_length=50, null=True, blank=True)
    exam_link = models.URLField(null=True, blank=True)
    tags = models.ManyToManyField('Tag', blank=True)
    prerequisites = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='required_for')
    reviews = GenericRelation(Review, related_query_name='program')


    def __str__(self):
        return self.title

class Course(models.Model):
    DIFFICULTY_LEVELS = (
        ('BEGINNER', 'Beginner'),
        ('INTERMEDIATE', 'Intermediate'),
        ('ADVANCED', 'Advanced'),
    )
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
    duration = models.CharField(max_length=100, blank=True)
    tags = models.ManyToManyField('Tag', blank=True)
    prerequisites = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='required_for')
    language = models.CharField(max_length=50, null=True, blank=True)
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_LEVELS, null=True, blank=True)
    reviews = GenericRelation(Review, related_query_name='course')

    def __str__(self):
        return self.title

class ProgramCourse(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='program_courses')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    is_mandatory = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('program', 'course')
        ordering = ['order']

    def __str__(self):
        return f"{self.program.title} - {self.course.title}"

class LearningResource(models.Model):
    RESOURCE_TYPES = (
        ('SCORM', 'SCORM Package'),
        ('VIDEO', 'Video'),
        ('DOCUMENT', 'Document'),
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
    order = models.PositiveIntegerField(default=0)
    is_mandatory = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reviews = GenericRelation(Review, related_query_name='learning_resource')

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.title} ({self.get_resource_type_display()})"

class Delivery(models.Model):
    DELIVERY_TYPES = (
        ('PROGRAM', 'Program'),
        ('COURSE', 'Course'),
    )
    DELIVERY_MODES = (
        ('SELF_PACED', 'Self-Paced'),
        ('INSTRUCTOR_LED', 'Instructor-Led'),
        ('BLENDED', 'Blended'),
    )
    COMPLETION_CRITERIA = (
        ('ALL_COMPONENTS', 'Complete All Components'),
        ('MINIMUM_SCORE', 'Achieve Minimum Score'),
        ('ATTENDANCE', 'Meet Attendance Requirement'),
    )

    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # Delivery Configuration
    delivery_type = models.CharField(max_length=10, choices=DELIVERY_TYPES)
    program = models.ForeignKey('Program', on_delete=models.CASCADE, null=True, blank=True, related_name='deliveries')
    course = models.ForeignKey('Course', on_delete=models.CASCADE, null=True, blank=True, related_name='deliveries')
    delivery_mode = models.CharField(max_length=20, choices=DELIVERY_MODES)

    # Scheduling
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    enrollment_start = models.DateTimeField()
    enrollment_end = models.DateTimeField()
    deactivation_date = models.DateTimeField(null=True, blank=True)

    # Instructor Assignment
    instructors = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='DeliveryInstructor',
        through_fields=('delivery', 'instructor'),
        related_name='instructed_deliveries'
    )

    # Capacity and Status
    max_participants = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_mandatory = models.BooleanField(default=False)

    # Completion and Certification
    completion_criteria = models.CharField(max_length=20, choices=COMPLETION_CRITERIA)
    minimum_score = models.PositiveIntegerField(null=True, blank=True)
    attendance_threshold = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    issue_certificate = models.BooleanField(default=True)

    # Enrollment Options
    allow_self_unenroll = models.BooleanField(default=False)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_deliveries')

    def clean(self):
        if self.delivery_type == 'PROGRAM' and not self.program:
            raise ValidationError(_("Program delivery must have a program associated."))
        if self.delivery_type == 'COURSE' and not self.course:
            raise ValidationError(_("Course delivery must have a course associated."))
        if self.delivery_type == 'PROGRAM' and self.course:
            raise ValidationError(_("Program delivery cannot have a course associated."))
        if self.delivery_type == 'COURSE' and self.program:
            raise ValidationError(_("Course delivery cannot have a program associated."))
        if self.completion_criteria == 'MINIMUM_SCORE' and self.minimum_score is None:
            raise ValidationError(_("Minimum score must be set when using 'Achieve Minimum Score' completion criteria."))
        if self.completion_criteria == 'ATTENDANCE' and self.attendance_threshold is None:
            raise ValidationError(_("Attendance threshold must be set when using 'Meet Attendance Requirement' completion criteria."))

    def __str__(self):
        return f"{self.get_delivery_type_display()} Delivery: {self.title}"
    
    def has_started(self):
        return self.start_date <= timezone.now() if self.start_date else False

class DeliveryComponent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    delivery = models.ForeignKey('Delivery', on_delete=models.CASCADE, related_name='components')
    program_course = models.ForeignKey('ProgramCourse', on_delete=models.CASCADE, null=True, blank=True)
    learning_resource = models.ForeignKey('LearningResource', on_delete=models.CASCADE, null=True, blank=True)
    is_mandatory = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    parent_component = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='child_components')

    class Meta:
        ordering = ['order']
        unique_together = [
            ('delivery', 'program_course'),
            ('delivery', 'learning_resource'),
        ]

    def __str__(self):
        if self.program_course:
            return f"{self.delivery.title} - {self.program_course.course.title}"
        elif self.learning_resource:
            return f"{self.delivery.title} - {self.learning_resource.title}"
        return f"Component of {self.delivery.title}"

    @property
    def is_course_component(self):
        return self.program_course is not None and self.learning_resource is None

    @property
    def is_resource_component(self):
        return self.learning_resource is not None

    def get_child_components(self):
        return self.child_components.all() if self.is_course_component else None

class DeliverySchedule(models.Model):
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    delivery = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name='schedules')
    session_title = models.CharField(max_length=255)

    # Scheduling
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    # Location
    location = models.CharField(max_length=255, blank=True)
    is_virtual = models.BooleanField(default=False)
    virtual_meeting_link = models.URLField(blank=True)

    class Meta:
        ordering = ['start_time']

    def __str__(self):
        return f"{self.delivery.title} - {self.session_title}"
    
class DeliveryInstructor(models.Model):
    INSTRUCTOR_ROLES = (
        ('PRIMARY', 'Primary Instructor'),
        ('ASSISTANT', 'Assistant Instructor'),
        ('GUEST', 'Guest Lecturer'),
        ('MENTOR', 'Mentor'),
    )

    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    delivery = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name='delivery_instructors')
    instructor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='delivery_instructor_roles')

    # Role Information
    role = models.CharField(max_length=20, choices=INSTRUCTOR_ROLES)
    is_active = models.BooleanField(default=True)

    # Assignment Details
    assigned_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='instructor_assignments'
    )

    class Meta:
        unique_together = ['delivery', 'instructor']

    def __str__(self):
        return f"{self.instructor.get_full_name()} - {self.get_role_display()} for {self.delivery.title}"
    

    def clean(self):
        # Ensure the assigned instructor has the appropriate permissions
        if not self.instructor.has_perm('courses.can_be_instructor'):
            raise ValidationError(_("The selected user does not have permission to be an instructor."))

class DeliveryFeedback(models.Model):
    FEEDBACK_TYPES = (
        ('SURVEY', 'Survey'),
        ('RATING', 'Rating'),
        ('OPEN_ENDED', 'Open-ended Feedback'),
    )

    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    delivery = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name='feedback')
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPES)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # Feedback Configuration
    is_anonymous = models.BooleanField(default=False)
    is_required = models.BooleanField(default=False)
    due_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.delivery.title} - {self.title}"

class DeliveryEmailTemplate(models.Model):
    EMAIL_TYPES = (
        ('ENROLLMENT_CONFIRMATION', 'Enrollment Confirmation'),
        ('REMINDER', 'Reminder'),
        ('COMPLETION', 'Completion'),
        ('CERTIFICATE', 'Certificate Issuance'),
    )

    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    delivery = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name='email_templates')
    email_type = models.CharField(max_length=30, choices=EMAIL_TYPES)

    # Email Content
    subject = models.CharField(max_length=255)
    body = models.TextField()

    # Status
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.delivery.title} - {self.get_email_type_display()}"

class DeliveryAttendance(models.Model):
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    delivery = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name='attendance')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='delivery_attendance')
    schedule = models.ForeignKey(DeliverySchedule, on_delete=models.CASCADE, related_name='attendance')

    # Attendance Data
    is_present = models.BooleanField(default=False)
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['delivery', 'user', 'schedule']

    def __str__(self):
        return f"{self.user} - {self.schedule}"

class Enrollment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    delivery = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name='enrollments', null=True, blank=True)
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='direct_enrollments', null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='direct_enrollments', null=True, blank=True)
    enrollment_date = models.DateTimeField(auto_now_add=True)
    completion_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('ENROLLED', 'Enrolled'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('WITHDRAWN', 'Withdrawn'),
    ], default='ENROLLED')

    class Meta:
        unique_together = [
            ('user', 'delivery'),
            ('user', 'program'),
            ('user', 'course'),
        ]

    def __str__(self):
        if self.delivery:
            return f"{self.user.username} - {self.delivery.title}"
        elif self.program:
            return f"{self.user.username} - {self.program.title} (Direct)"
        else:
            return f"{self.user.username} - {self.course.title} (Direct)"

class ComponentCompletion(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='component_completions')
    delivery_component = models.ForeignKey(DeliveryComponent, on_delete=models.CASCADE, null=True, blank=True)
    program_course = models.ForeignKey(ProgramCourse, on_delete=models.CASCADE, null=True, blank=True)
    learning_resource = models.ForeignKey(LearningResource, on_delete=models.CASCADE, null=True, blank=True)
    completion_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [
            ('enrollment', 'delivery_component'),
            ('enrollment', 'program_course'),
            ('enrollment', 'learning_resource'),
        ]

    def __str__(self):
        if self.delivery_component:
            return f"{self.enrollment.user.username} completed {self.delivery_component}"
        elif self.program_course:
            return f"{self.enrollment.user.username} completed {self.program_course}"
        else:
            return f"{self.enrollment.user.username} completed {self.learning_resource}"

    def clean(self):
        if not any([self.delivery_component, self.program_course, self.learning_resource]):
            raise ValidationError("ComponentCompletion must be associated with either a delivery component, program course, or learning resource.")

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class CourseCategory(models.Model):
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Course Categories"

class Progress(models.Model):
    PROGRESS_TYPES = (
        ('LEARNING_RESOURCE', 'Learning Resource'),
        ('COURSE', 'Course'),
        ('PROGRAM', 'Program'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='progress_records')
    progress_type = models.CharField(max_length=20, choices=PROGRESS_TYPES)
    learning_resource = models.ForeignKey(LearningResource, on_delete=models.CASCADE, null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True)
    program = models.ForeignKey(Program, on_delete=models.CASCADE, null=True, blank=True)
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    completed_items = models.PositiveIntegerField(default=0)
    total_items = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [
            ('enrollment', 'learning_resource'),
            ('enrollment', 'course'),
            ('enrollment', 'program'),
        ]

    def __str__(self):
        if self.progress_type == 'LEARNING_RESOURCE':
            return f"Progress for {self.enrollment.user.username} in {self.learning_resource.title}"
        elif self.progress_type == 'COURSE':
            return f"Progress for {self.enrollment.user.username} in {self.course.title}"
        else:
            return f"Progress for {self.enrollment.user.username} in {self.program.title}"

    def update_progress(self, completed_items, total_items):
        self.completed_items = completed_items
        self.total_items = total_items
        self.progress_percentage = (completed_items / total_items) * 100 if total_items > 0 else 0
        self.save()

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



class Recommendation(models.Model):
    RECOMMENDATION_TYPES = (
        ('COURSE', 'Course'),
        ('PROGRAM', 'Program'),
        ('LEARNING_RESOURCE', 'Learning Resource'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendations')
    recommendation_type = models.CharField(max_length=20, choices=RECOMMENDATION_TYPES)
    
    # For Course recommendations
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True, related_name='course_recommendations')
    
    # For Program recommendations
    program = models.ForeignKey(Program, on_delete=models.CASCADE, null=True, blank=True, related_name='program_recommendations')
    
    # For Learning Resource recommendations
    learning_resource = models.ForeignKey(LearningResource, on_delete=models.CASCADE, null=True, blank=True, related_name='resource_recommendations')
    
    score = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    reason = models.TextField(blank=True, help_text="Explanation for this recommendation")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'recommendation_type', 'course', 'program', 'learning_resource']
        indexes = [
            models.Index(fields=['user', 'recommendation_type', 'score']),
        ]

    def clean(self):
        if self.recommendation_type == 'COURSE' and not self.course:
            raise ValidationError("Course must be specified for course recommendations.")
        elif self.recommendation_type == 'PROGRAM' and not self.program:
            raise ValidationError("Program must be specified for program recommendations.")
        elif self.recommendation_type == 'LEARNING_RESOURCE' and not self.learning_resource:
            raise ValidationError("Learning Resource must be specified for learning resource recommendations.")

    def __str__(self):
        if self.recommendation_type == 'COURSE':
            return f"Course recommendation: {self.course.title} for {self.user.username}"
        elif self.recommendation_type == 'PROGRAM':
            return f"Program recommendation: {self.program.title} for {self.user.username}"
        else:
            return f"Learning Resource recommendation: {self.learning_resource.title} for {self.user.username}"
        