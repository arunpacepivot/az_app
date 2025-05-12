from rest_framework import serializers
from .models import CerebroFile

class CerebroFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CerebroFile
        fields = '__all__' 