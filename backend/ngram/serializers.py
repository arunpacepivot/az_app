from rest_framework import serializers
from .models import NgramFile

class NgramFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = NgramFile
        fields = '__all__' 