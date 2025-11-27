from km_agent import KMAgent
from pdf_vectorizer import PDFVectorizer

# Global instances
km_agent = None
vectorizer = None
km_agent_cache = {}  # Cache KMAgent instances per owner

def get_or_create_km_agent(owner: str):
    """
    Get or create KMAgent instance for specific owner
    
    Caches instances to avoid recreating on every request
    """
    global km_agent_cache
    
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
