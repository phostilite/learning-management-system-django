# serializers.py

from rest_framework import serializers
from courses.models import Delivery, ScormRegistration

class CourseDeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = Delivery

class ScormRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScormRegistration
        fields = ['id', 'scorm_registration_id', 'enrollment', 'created_at', 'updated_at']