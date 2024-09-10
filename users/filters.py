import django_filters
from courses.models import Program, Course, Tag, CourseCategory

class ProgramFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains')
    program_type = django_filters.ChoiceFilter(choices=Program.PROGRAM_TYPES)
    level = django_filters.CharFilter(lookup_expr='icontains')
    tags = django_filters.ModelMultipleChoiceFilter(queryset=Tag.objects.all())

    class Meta:
        model = Program
        fields = ['title', 'program_type', 'level', 'tags']

class CourseFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains')
    category = django_filters.ModelChoiceFilter(queryset=CourseCategory.objects.all())
    difficulty_level = django_filters.ChoiceFilter(choices=Course.DIFFICULTY_LEVELS)
    language = django_filters.CharFilter(lookup_expr='icontains')
    tags = django_filters.ModelMultipleChoiceFilter(queryset=Tag.objects.all())

    class Meta:
        model = Course
        fields = ['title', 'category', 'difficulty_level', 'language', 'tags']