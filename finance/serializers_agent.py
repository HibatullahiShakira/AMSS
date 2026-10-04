from rest_framework import serializers

class AgentQuerySerializer(serializers.Serializer):
    query = serializers.CharField(max_length=1000)
