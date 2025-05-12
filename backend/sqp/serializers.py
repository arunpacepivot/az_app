from rest_framework import serializers
from .models import SQPFile

class SQPFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SQPFile
        fields = '__all__' 