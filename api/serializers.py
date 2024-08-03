# serializers.py

from rest_framework import serializers
from courses.models import CourseDelivery, ScormRegistration

class CourseDeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseDelivery
        fields = ['id', 'title', 'course', 'delivery_type', 'start_date', 'end_date', 'status']

class ScormRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScormRegistration
        fields = ['id', 'scorm_registration_id', 'enrollment', 'created_at', 'updated_at']