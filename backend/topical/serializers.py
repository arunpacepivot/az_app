from rest_framework import serializers
from .models import TopicalFile

class TopicalFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TopicalFile
        fields = '__all__' 