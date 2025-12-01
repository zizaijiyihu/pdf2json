from km_agent import KMAgent
from pdf_vectorizer import PDFVectorizer

# Global instances
km_agent = None
vectorizer = None
km_agent_cache = {}  # Cache KMAgent instances per owner

def get_or_create_km_agent(owner: str, conversation_id: str = None, enable_history: bool = False):
    """
    Get or create KMAgent instance for specific owner
    
    Args:
        owner: User identifier
        conversation_id: Conversation ID for history persistence (optional)
        enable_history: Whether to enable conversation history persistence
    
    Note:
        When enable_history is True, a new KMAgent instance is created each time
        to ensure conversation isolation. Otherwise, instances are cached.
    """
    global km_agent_cache
    
    # If history is enabled, create a new instance with conversation context
    if enable_history:
        return KMAgent(
            verbose=True,
            owner=owner,
            conversation_id=conversation_id,
            enable_history=True
        )
    
    # Otherwise, use cached instance
    if owner not in km_agent_cache:
        km_agent_cache[owner] = KMAgent(verbose=True, owner=owner)
    
    return km_agent_cache[owner]

def init_services():
    """Initialize KM Agent and PDF Vectorizer"""
    global km_agent, vectorizer

    # Initialize KM Agent (uses ks_infrastructure, no parameters needed)
    km_agent = KMAgent(verbose=True)

    # Initialize PDF Vectorizer (uses ks_infrastructure, defaults from pdf_vectorizer)
    vectorizer = PDFVectorizer()

    print("✓ Services initialized successfully")

def get_vectorizer():
    """Get the global vectorizer instance"""
    global vectorizer
    if vectorizer is None:
        vectorizer = PDFVectorizer()
    return vectorizer
