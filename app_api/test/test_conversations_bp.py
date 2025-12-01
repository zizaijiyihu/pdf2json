import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app_api.api import create_app

class TestConversationsBlueprint(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.app.testing = True

    @patch('app_api.routes.conversations.get_current_user')
    @patch('app_api.routes.conversations.list_conversations')
    @patch('app_api.routes.conversations.count_conversations')
    def test_get_conversations_route(self, mock_count, mock_list, mock_user):
        """Test that the GET /api/conversations route is registered and working"""
        print("\nTesting GET /api/conversations...")
        
        # Setup mocks
        mock_user.return_value = 'test_user'
        mock_list.return_value = [{'id': 1, 'title': 'Test Conversation', 'owner': 'test_user'}]
        mock_count.return_value = 1

        # Make request
        response = self.client.get('/api/conversations')

        # Assertions
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.get_json()}")
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']['conversations']), 1)
        self.assertEqual(data['data']['conversations'][0]['title'], 'Test Conversation')
        
    @patch('app_api.routes.conversations.get_current_user')
    @patch('app_api.routes.conversations.create_conversation')
    def test_create_conversation_route(self, mock_create, mock_user):
        """Test that the POST /api/conversations route is registered and working"""
        print("\nTesting POST /api/conversations...")
        
        # Setup mocks
        mock_user.return_value = 'test_user'
        mock_create.return_value = 'new-uuid-123'

        # Make request
        response = self.client.post('/api/conversations', json={'title': 'New Chat'})

        # Assertions
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.get_json()}")
        
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['conversation_id'], 'new-uuid-123')

if __name__ == '__main__':
    unittest.main()
