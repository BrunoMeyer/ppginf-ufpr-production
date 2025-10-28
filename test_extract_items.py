#!/usr/bin/env python3
"""
Unit tests for the DSpace item extractor.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from extract_items import DSpaceExtractor


class TestDSpaceExtractor(unittest.TestCase):
    """Test cases for DSpaceExtractor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.api_url = "https://test.dspace.edu/server/api"
        self.community_id = "test-community-123"
        self.extractor = DSpaceExtractor(self.api_url, self.community_id)
    
    def test_initialization(self):
        """Test extractor initialization."""
        self.assertEqual(self.extractor.api_url, self.api_url)
        self.assertEqual(self.extractor.community_id, self.community_id)
        self.assertIsNotNone(self.extractor.session)
    
    def test_api_url_trailing_slash_removed(self):
        """Test that trailing slash is removed from API URL."""
        extractor = DSpaceExtractor("https://test.dspace.edu/server/api/", self.community_id)
        self.assertEqual(extractor.api_url, "https://test.dspace.edu/server/api")
    
    @patch('extract_items.requests.Session')
    def test_get_collections_success(self, mock_session):
        """Test successful collection retrieval."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            '_embedded': {
                'collections': [
                    {'id': 'col-1', 'name': 'Collection 1'},
                    {'id': 'col-2', 'name': 'Collection 2'}
                ]
            },
            'page': {'totalPages': 1}
        }
        mock_response.raise_for_status = Mock()
        
        self.extractor.session.get = Mock(return_value=mock_response)
        
        collections = self.extractor.get_collections()
        
        self.assertEqual(len(collections), 2)
        self.assertEqual(collections[0]['name'], 'Collection 1')
        self.assertEqual(collections[1]['name'], 'Collection 2')
    
    @patch('extract_items.requests.Session')
    def test_get_collections_pagination(self, mock_session):
        """Test collection retrieval with pagination."""
        # Mock responses for two pages
        mock_response_page1 = Mock()
        mock_response_page1.json.return_value = {
            '_embedded': {
                'collections': [
                    {'id': 'col-1', 'name': 'Collection 1'}
                ]
            },
            'page': {'totalPages': 2}
        }
        mock_response_page1.raise_for_status = Mock()
        
        mock_response_page2 = Mock()
        mock_response_page2.json.return_value = {
            '_embedded': {
                'collections': [
                    {'id': 'col-2', 'name': 'Collection 2'}
                ]
            },
            'page': {'totalPages': 2}
        }
        mock_response_page2.raise_for_status = Mock()
        
        self.extractor.session.get = Mock(side_effect=[mock_response_page1, mock_response_page2])
        
        collections = self.extractor.get_collections()
        
        self.assertEqual(len(collections), 2)
        self.assertEqual(self.extractor.session.get.call_count, 2)
    
    @patch('extract_items.requests.Session')
    def test_get_items_from_collection_success(self, mock_session):
        """Test successful item retrieval from collection."""
        mock_response = Mock()
        mock_response.json.return_value = {
            '_embedded': {
                'items': [
                    {'id': 'item-1', 'name': 'Item 1'},
                    {'id': 'item-2', 'name': 'Item 2'}
                ]
            },
            'page': {'totalPages': 1}
        }
        mock_response.raise_for_status = Mock()
        
        self.extractor.session.get = Mock(return_value=mock_response)
        
        items = self.extractor.get_items_from_collection('col-1')
        
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]['name'], 'Item 1')
    
    def test_extract_item_data(self):
        """Test item data extraction."""
        item = {
            'id': 'item-123',
            'uuid': 'uuid-123',
            'name': 'Test Item',
            'handle': '123456789/123',
            'metadata': {
                'dc.title': [{'value': 'Test Title'}],
                'dc.creator': [{'value': 'Author 1'}, {'value': 'Author 2'}]
            }
        }
        
        extracted = self.extractor.extract_item_data(item)
        
        self.assertEqual(extracted['id'], 'item-123')
        self.assertEqual(extracted['name'], 'Test Item')
        self.assertEqual(extracted['metadata']['dc.title'], ['Test Title'])
        self.assertEqual(extracted['metadata']['dc.creator'], ['Author 1', 'Author 2'])
    
    def test_extract_item_data_missing_fields(self):
        """Test item data extraction with missing fields."""
        item = {}
        
        extracted = self.extractor.extract_item_data(item)
        
        self.assertEqual(extracted['id'], '')
        self.assertEqual(extracted['name'], '')
        self.assertEqual(extracted['metadata'], {})
    
    @patch('extract_items.requests.Session')
    def test_extract_all_items(self, mock_session):
        """Test full extraction process."""
        # Mock collections response
        collections_response = Mock()
        collections_response.json.return_value = {
            '_embedded': {
                'collections': [
                    {
                        'id': 'col-1',
                        'uuid': 'col-uuid-1',
                        'name': 'Collection 1',
                        'handle': '123456789/1'
                    }
                ]
            },
            'page': {'totalPages': 1}
        }
        collections_response.raise_for_status = Mock()
        
        # Mock items response
        items_response = Mock()
        items_response.json.return_value = {
            '_embedded': {
                'items': [
                    {
                        'id': 'item-1',
                        'uuid': 'item-uuid-1',
                        'name': 'Item 1',
                        'handle': '123456789/2',
                        'metadata': {}
                    }
                ]
            },
            'page': {'totalPages': 1}
        }
        items_response.raise_for_status = Mock()
        
        self.extractor.session.get = Mock(side_effect=[collections_response, items_response])
        
        result = self.extractor.extract_all_items()
        
        self.assertIn('Collection 1', result)
        self.assertEqual(len(result['Collection 1']['items']), 1)
        self.assertEqual(result['Collection 1']['items'][0]['name'], 'Item 1')


if __name__ == '__main__':
    unittest.main()
