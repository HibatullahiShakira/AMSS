from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from .serializers_agent import AgentQuerySerializer
from .agent import get_business_agent
import traceback

class AgentViewSet(viewsets.ViewSet):
    # permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def chat(self, request):
        user = getattr(request, 'user', None)
        if not user or not hasattr(user, 'business'):
            return Response({"error": "No business context found."}, status=status.HTTP_400_BAD_REQUEST)
            
        business = user.business

        serializer = AgentQuerySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        query = serializer.validated_data['query']

        try:
            agent = get_business_agent(business)
            # Run the modern LangGraph agent
            result = agent.invoke({"messages": [("user", query)]})
            
            # The result has a 'messages' list, the last message is the AI's final answer
            response_text = result["messages"][-1].content if "messages" in result else str(result)
            
            return Response({
                "query": query,
                "response": response_text
            })
        except Exception as e:
            # Handle cases where Ollama is not running or other errors
            error_msg = str(e)
            if "Connection error" in error_msg or "Failed to connect" in error_msg:
                error_msg = "Could not connect to local Ollama instance. Please ensure Ollama is running and the 'llama3.2' model is pulled."
            
            return Response({
                "error": error_msg,
                "traceback": traceback.format_exc()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
