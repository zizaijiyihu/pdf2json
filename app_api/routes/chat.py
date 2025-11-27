from flask import Blueprint, request, Response, stream_with_context, jsonify
import json
from app_api.services.agent_service import get_or_create_km_agent
from ks_infrastructure import get_current_user

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/api/chat', methods=['POST'])
def chat():
    """
    Chat with KM Agent using streaming (SSE)

    Request body:
    {
        "message": "user question",
        "history": [...]  // optional, conversation history
    }

    Note: User identification is handled server-side via get_current_user()

    Response: Server-Sent Events (SSE) stream
    Event types:
    - content: Streaming response content
    - tool_call: Tool execution notification
    - done: Final result with history
    """
    try:
        data = request.get_json()
        print(f"\n[DEBUG] Received chat request: {data}", flush=True)

        if not data or 'message' not in data:
            return jsonify({
                "success": False,
                "error": "Missing 'message' in request body"
            }), 400

        user_message = data['message']
        history = data.get('history', None)
        owner = get_current_user() # Always use trusted user from server
        print(f"[DEBUG] Using owner: {owner}", flush=True)

        # Get or create KMAgent instance for the specific owner
        km_agent_instance = get_or_create_km_agent(owner)
        
        # Reload instructions to ensure we have the latest ones
        km_agent_instance.reload_instructions()

        def generate_stream():
            """Generate SSE stream from agent"""
            try:
                for chunk in km_agent_instance.chat_stream(user_message, history):
                    yield f"data: {json.dumps(chunk)}\n\n"
            except Exception as e:
                error_chunk = {
                    "type": "error",
                    "data": {"error": str(e)}
                }
                yield f"data: {json.dumps(error_chunk)}\n\n"

        return Response(
            stream_with_context(generate_stream()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
