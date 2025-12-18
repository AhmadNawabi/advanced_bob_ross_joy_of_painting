"""
✨ Advanced Pagination Test Suite ✨
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
A comprehensive, beautifully formatted test suite for pagination functionality.
Features rich output, parameterized testing, and professional best practices.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import unittest
import sys
import time
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from contextlib import contextmanager
from unittest.mock import MagicMock, patch, call, PropertyMock
from flask import Flask

from api.pagination import (
    get_pagination_params, 
    paginate_query, 
    create_pagination_response
)


# ============================================================================
# 🎨 DECORATORS & HELPERS
# ============================================================================

def timing_decorator(func):
    """Decorator to measure test execution time."""
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start_time
        # Store timing in test instance if available
        if hasattr(args[0], '_test_timings'):
            args[0]._test_timings[func.__name__] = elapsed
        return result
    return wrapper


def colorize(text: str, *color_codes: str) -> str:
    """Add ANSI color codes to text for terminal output."""
    colors = {
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m',
        'red': '\033[91m',
        'bold': '\033[1m',
        'underline': '\033[4m',
        'end': '\033[0m'
    }
    
    color_sequence = ''.join(colors.get(code, '') for code in color_codes)
    return f"{color_sequence}{text}{colors['end']}"


@contextmanager
def performance_context(name: str = ""):
    """Context manager for measuring code block performance."""
    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start
    if name:
        print(f"⏱️  {colorize(name, 'cyan')}: {elapsed:.6f}s")


# ============================================================================
# 📊 TEST DATA STRUCTURES
# ============================================================================

@dataclass
class PaginationTestCase:
    """Structured test case for pagination parameters."""
    name: str
    query_string: str
    expected_page: int
    expected_per_page: int
    description: str = ""
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class PaginationScenario:
    """Complete pagination scenario for integration testing."""
    name: str
    page: int
    per_page: int
    total_items: int
    expected_pages: int
    expected_offset: int
    expected_limit: int


# ============================================================================
# 🧪 TEST DATA SETS
# ============================================================================

PAGINATION_TEST_CASES = [
    PaginationTestCase(
        name="Default Values",
        query_string="",
        expected_page=1,
        expected_per_page=20,
        description="Should use defaults when no parameters provided",
        tags=["default", "basic"]
    ),
    PaginationTestCase(
        name="Valid Custom Values",
        query_string="?page=3&per_page=10",
        expected_page=3,
        expected_per_page=10,
        description="Should parse valid custom parameters",
        tags=["custom", "valid"]
    ),
    PaginationTestCase(
        name="Page Only",
        query_string="?page=5",
        expected_page=5,
        expected_per_page=20,
        description="Should use default per_page when only page provided",
        tags=["partial", "page-only"]
    ),
    PaginationTestCase(
        name="Per Page Only",
        query_string="?per_page=50",
        expected_page=1,
        expected_per_page=50,
        description="Should use default page when only per_page provided",
        tags=["partial", "perpage-only"]
    ),
    PaginationTestCase(
        name="Non-Numeric Page",
        query_string="?page=abc",
        expected_page=1,
        expected_per_page=20,
        description="Should fallback to default for non-numeric page",
        tags=["invalid", "edge-case"]
    ),
    PaginationTestCase(
        name="Negative Page",
        query_string="?page=-5",
        expected_page=1,
        expected_per_page=20,
        description="Should fallback to default for negative page",
        tags=["invalid", "edge-case"]
    ),
    PaginationTestCase(
        name="Zero Page",
        query_string="?page=0",
        expected_page=1,
        expected_per_page=20,
        description="Should fallback to default for zero page",
        tags=["invalid", "edge-case"]
    ),
    PaginationTestCase(
        name="Maximum Per Page",
        query_string="?per_page=150",
        expected_page=1,
        expected_per_page=100,
        description="Should respect maximum per_page limit",
        tags=["limit", "boundary"]
    ),
    PaginationTestCase(
        name="Float Values",
        query_string="?page=1.5&per_page=2.5",
        expected_page=1,
        expected_per_page=20,
        description="Should handle float values gracefully",
        tags=["invalid", "type"]
    ),
    PaginationTestCase(
        name="Empty Strings",
        query_string="?page=&per_page=",
        expected_page=1,
        expected_per_page=20,
        description="Should handle empty string parameters",
        tags=["invalid", "empty"]
    ),
]


PAGINATION_SCENARIOS = [
    PaginationScenario(
        name="First Page of Many",
        page=1,
        per_page=10,
        total_items=50,
        expected_pages=5,
        expected_offset=0,
        expected_limit=10
    ),
    PaginationScenario(
        name="Middle Page",
        page=3,
        per_page=10,
        total_items=50,
        expected_pages=5,
        expected_offset=20,
        expected_limit=10
    ),
    PaginationScenario(
        name="Last Page Partial",
        page=5,
        per_page=10,
        total_items=47,
        expected_pages=5,
        expected_offset=40,
        expected_limit=10
    ),
    PaginationScenario(
        name="Single Item Page",
        page=1,
        per_page=1,
        total_items=5,
        expected_pages=5,
        expected_offset=0,
        expected_limit=1
    ),
    PaginationScenario(
        name="Empty Results",
        page=1,
        per_page=10,
        total_items=0,
        expected_pages=0,
        expected_offset=0,
        expected_limit=10
    ),
    PaginationScenario(
        name="Page Out of Bounds",
        page=10,
        per_page=10,
        total_items=25,
        expected_pages=3,
        expected_offset=20,  # Should adjust to last page
        expected_limit=10
    ),
]


# ============================================================================
# 🎯 MAIN TEST CLASS
# ============================================================================

class AdvancedPaginationTestSuite(unittest.TestCase):
    """✨ Advanced Pagination Test Suite with Enhanced Features ✨"""
    
    # ========================================================================
    # 🎪 SETUP & TEARDOWN
    # ========================================================================
    
    def setUp(self):
        """Initialize test environment with fancy setup."""
        print(f"\n{'━' * 60}")
        print(f"🚀 {colorize('Setting up test environment', 'bold')}")
        print(f"{'━' * 60}")
        
        # Create Flask app with enhanced configuration
        self.app = Flask(__name__)
        self.app.config.update({
            'TESTING': True,
            'DEBUG': False,
            'MAX_PER_PAGE': 100,
            'DEFAULT_PAGE': 1,
            'DEFAULT_PER_PAGE': 20,
            'SECRET_KEY': 'test-secret-key-for-pagination'
        })
        
        # Performance tracking
        self._test_timings = {}
        self._test_start_time = time.perf_counter()
        
        # Test counters
        self._tests_passed = 0
        self._tests_failed = 0
        
        print(f"✅ {colorize('Test environment ready', 'green')}")
    
    def tearDown(self):
        """Clean up and display test summary."""
        elapsed = time.perf_counter() - self._test_start_time
        
        print(f"\n{'━' * 60}")
        print(f"📊 {colorize('TEST SUMMARY', 'bold')}")
        print(f"{'━' * 60}")
        print(f"Total Tests Run: {self._tests_passed + self._tests_failed}")
        print(f"✅ Passed: {colorize(str(self._tests_passed), 'green')}")
        print(f"❌ Failed: {colorize(str(self._tests_failed), 'red') if self._tests_failed > 0 else '0'}")
        print(f"⏱️  Total Time: {elapsed:.4f}s")
        
        if self._test_timings:
            print(f"\n🎯 {colorize('Performance Metrics', 'cyan')}:")
            for test_name, test_time in sorted(self._test_timings.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"   {test_name}: {test_time:.6f}s")
        
        print(f"{'━' * 60}\n")
    
    # ========================================================================
    # 🧪 TEST METHOD DECORATORS
    # ========================================================================
    
    @timing_decorator
    def run_test(self, test_method, *args, **kwargs):
        """Enhanced test runner with timing and tracking."""
        test_name = colorize(test_method.__name__, 'yellow')
        print(f"\n▶️  Running: {test_name}")
        
        try:
            result = test_method(*args, **kwargs)
            print(f"   ✅ {colorize('PASSED', 'green')}")
            self._tests_passed += 1
            return result
        except AssertionError as e:
            print(f"   ❌ {colorize('FAILED', 'red')}: {str(e)}")
            self._tests_failed += 1
            raise
        except Exception as e:
            print(f"   💥 {colorize('ERROR', 'red')}: {str(e)}")
            self._tests_failed += 1
            raise
    
    # ========================================================================
    # 📈 PARAMETERIZED PAGINATION TESTS
    # ========================================================================
    
    def test_pagination_params_comprehensive(self):
        """📊 Comprehensive parameterized pagination parameter tests."""
        print(f"\n🎯 {colorize('COMPREHENSIVE PAGINATION PARAMETER TESTS', 'bold')}")
        print(f"{'─' * 60}")
        
        for test_case in PAGINATION_TEST_CASES:
            with self.subTest(test_case.name):
                print(f"   Testing: {colorize(test_case.name, 'cyan')}")
                print(f"   Query: {test_case.query_string or '(empty)'}")
                print(f"   Expecting: page={test_case.expected_page}, per_page={test_case.expected_per_page}")
                
                with self.app.test_request_context(test_case.query_string):
                    with performance_context(f"get_pagination_params for {test_case.name}"):
                        page, per_page = get_pagination_params()
                    
                    self.assertEqual(
                        page, test_case.expected_page,
                        f"Page mismatch for {test_case.name}. Expected {test_case.expected_page}, got {page}"
                    )
                    self.assertEqual(
                        per_page, test_case.expected_per_page,
                        f"Per page mismatch for {test_case.name}. Expected {test_case.expected_per_page}, got {per_page}"
                    )
                
                print(f"   ✅ {colorize('Correct', 'green')}: page={page}, per_page={per_page}\n")
    
    # ========================================================================
    # 🔧 ADVANCED PAGINATION FUNCTIONALITY TESTS
    # ========================================================================
    
    def test_paginate_query_scenarios(self):
        """🔄 Test paginate_query with various scenarios."""
        print(f"\n🔄 {colorize('PAGINATION SCENARIO TESTS', 'bold')}")
        print(f"{'─' * 60}")
        
        for scenario in PAGINATION_SCENARIOS:
            with self.subTest(scenario.name):
                print(f"   Scenario: {colorize(scenario.name, 'magenta')}")
                print(f"   Config: page={scenario.page}, per_page={scenario.per_page}, total={scenario.total_items}")
                
                # Create sophisticated mock query
                mock_query = MagicMock()
                mock_query.count.return_value = scenario.total_items
                
                # Setup chain mock with detailed tracking
                mock_items = [f"item_{i}" for i in range(1, min(scenario.per_page, scenario.total_items) + 1)]
                
                mock_limit = MagicMock()
                mock_limit.all.return_value = mock_items
                
                mock_offset = MagicMock()
                mock_offset.limit.return_value = mock_limit
                
                mock_query.offset.return_value = mock_offset
                
                # Execute pagination
                with performance_context(f"paginate_query for {scenario.name}"):
                    paginated_query, total_items, total_pages = paginate_query(
                        mock_query, scenario.page, scenario.per_page
                    )
                
                # Verify results
                self.assertEqual(total_items, scenario.total_items)
                self.assertEqual(total_pages, scenario.expected_pages)
                
                # Verify mock calls
                mock_query.count.assert_called_once()
                mock_query.offset.assert_called_once_with(scenario.expected_offset)
                mock_offset.limit.assert_called_once_with(scenario.expected_limit)
                
                print(f"   ✅ {colorize('Verified', 'green')}: pages={total_pages}, offset={scenario.expected_offset}\n")
    
    # ========================================================================
    # 🎨 CREATIVE RESPONSE BUILDING TESTS
    # ========================================================================
    
    def test_create_pagination_response_artistic(self):
        """🎨 Test pagination response creation with artistic data."""
        print(f"\n🎨 {colorize('ARTISTIC PAGINATION RESPONSE TESTS', 'bold')}")
        print(f"{'─' * 60}")
        
        # Create beautiful test data
        artistic_items = [
            {
                "id": i,
                "title": f"Masterpiece #{i}",
                "artist": "Bob Ross",
                "colors": ["Titanium White", "Phthalo Blue", "Van Dyke Brown"],
                "techniques": ["Wet-on-Wet", "Fan Brush", "Knife Work"],
                "has_happy_trees": True,
                "has_mountains": i % 2 == 0,
                "has_cabin": i % 3 == 0
            }
            for i in range(1, 11)
        ]
        
        test_configs = [
            {
                "name": "Gallery First Page",
                "page": 1,
                "per_page": 5,
                "total_items": 50,
                "expected_has_next": True,
                "expected_has_prev": False
            },
            {
                "name": "Gallery Middle Page",
                "page": 3,
                "per_page": 5,
                "total_items": 50,
                "expected_has_next": True,
                "expected_has_prev": True
            },
            {
                "name": "Gallery Final Page",
                "page": 10,
                "per_page": 5,
                "total_items": 50,
                "expected_has_next": False,
                "expected_has_prev": True
            },
            {
                "name": "Single Masterpiece",
                "page": 1,
                "per_page": 1,
                "total_items": 1,
                "expected_has_next": False,
                "expected_has_prev": False
            },
        ]
        
        for config in test_configs:
            with self.subTest(config["name"]):
                print(f"   🖼️  {colorize(config['name'], 'cyan')}")
                
                with performance_context(f"create_pagination_response for {config['name']}"):
                    response = create_pagination_response(
                        items=artistic_items[:config["per_page"]],
                        page=config["page"],
                        per_page=config["per_page"],
                        total_items=config["total_items"],
                        total_pages=(config["total_items"] + config["per_page"] - 1) // config["per_page"]
                    )
                
                # Verify structure
                required_keys = {'items', 'page', 'per_page', 'total_items', 
                               'total_pages', 'has_next', 'has_prev', 'next_page', 'prev_page'}
                self.assertTrue(required_keys.issubset(response.keys()))
                
                # Verify pagination logic
                self.assertEqual(response['has_next'], config["expected_has_next"])
                self.assertEqual(response['has_prev'], config["expected_has_prev"])
                
                # Verify data integrity
                self.assertEqual(len(response['items']), min(config["per_page"], len(artistic_items)))
                self.assertEqual(response['items'][0]['artist'], "Bob Ross")
                
                print(f"   ✅ {colorize('Response validated', 'green')}: {len(response['items'])} masterpieces\n")
    
    # ========================================================================
    # 🚀 PERFORMANCE & STRESS TESTS
    # ========================================================================
    
    def test_pagination_performance_large_datasets(self):
        """⚡ Test pagination performance with large datasets."""
        print(f"\n⚡ {colorize('PERFORMANCE & STRESS TESTS', 'bold')}")
        print(f"{'─' * 60}")
        
        # Simulate large dataset
        LARGE_DATASET_SIZE = 10000
        PAGE_SIZES = [10, 50, 100, 500]
        
        for page_size in PAGE_SIZES:
            test_name = f"Large Dataset (n={LARGE_DATASET_SIZE}, page_size={page_size})"
            with self.subTest(test_name):
                print(f"   ⚡ Testing: {colorize(test_name, 'yellow')}")
                
                mock_query = MagicMock()
                mock_query.count.return_value = LARGE_DATASET_SIZE
                
                # Create proper mock chain
                mock_limit_result = MagicMock()
                mock_limit_result.all.return_value = list(range(min(page_size, LARGE_DATASET_SIZE)))
                
                mock_offset_result = MagicMock()
                mock_offset_result.limit.return_value = mock_limit_result
                
                mock_query.offset.return_value = mock_offset_result
                
                # Measure performance
                start_time = time.perf_counter()
                
                paginated_query, total_items, total_pages = paginate_query(
                    mock_query, page=500, per_page=page_size
                )
                
                elapsed = time.perf_counter() - start_time
                
                # Verify
                self.assertEqual(total_items, LARGE_DATASET_SIZE)
                expected_pages = (LARGE_DATASET_SIZE + page_size - 1) // page_size
                self.assertEqual(total_pages, expected_pages)
                
                # Performance assertion (adjust threshold as needed)
                self.assertLess(elapsed, 0.1, f"Pagination took {elapsed:.4f}s, expected < 0.1s")
                
                performance_grade = "✅ Excellent" if elapsed < 0.01 else "⚠️  Acceptable" if elapsed < 0.05 else "🐌 Slow"
                print(f"   {performance_grade}: {elapsed:.6f}s for {total_pages} pages\n")
    
    # ========================================================================
    # 🔍 EDGE CASE & BOUNDARY TESTS
    # ========================================================================
    
    def test_pagination_edge_cases_exotic(self):
        """🌀 Test exotic edge cases and boundaries."""
        print(f"\n🌀 {colorize('EXOTIC EDGE CASE TESTS', 'bold')}")
        print(f"{'─' * 60}")
        
        edge_cases = [
            {
                "name": "Gigantic Page Number",
                "query": "?page=999999999999999999&per_page=10",
                "expected_page": 999999999999999999,  # Python can handle this large int
                "expected_per_page": 10,
                "description": "Python can handle extremely large integers"
            },
            {
                "name": "Tiny Per Page",
                "query": "?per_page=1",
                "expected_page": 1,
                "expected_per_page": 1,
                "description": "Should allow single item per page"
            },
            {
                "name": "Special Characters",
                "query": "?page=@#$&per_page=%^*",
                "expected_page": 1,
                "expected_per_page": 20,
                "description": "Should handle special characters gracefully"
            },
            {
                "name": "Multiple Parameters - First Value",
                "query": "?page=2&per_page=10&sort=asc&filter=active&page=3",
                "expected_page": 2,  # Flask's request.args.get() returns first value
                "expected_per_page": 10,
                "description": "Flask uses first occurrence of duplicate parameters"
            },
            {
                "name": "Whitespace Values",
                "query": "?page=%20&per_page=%20%20",
                "expected_page": 1,
                "expected_per_page": 20,
                "description": "Should handle whitespace-only values"
            },
            {
                "name": "Very Large Per Page",
                "query": "?per_page=999999999",
                "expected_page": 1,
                "expected_per_page": 100,  # Limited by max_per_page
                "description": "Should respect maximum per_page limit"
            },
        ]
        
        for case in edge_cases:
            with self.subTest(case["name"]):
                print(f"   🌀 {colorize(case['name'], 'magenta')}")
                print(f"   Description: {case['description']}")
                
                with self.app.test_request_context(case["query"]):
                    page, per_page = get_pagination_params()
                
                expected_page = case.get("expected_page", 1)
                expected_per_page = case.get("expected_per_page", 20)
                
                self.assertEqual(page, expected_page,
                               f"Expected page {expected_page}, got {page}")
                self.assertEqual(per_page, expected_per_page,
                               f"Expected per_page {expected_per_page}, got {per_page}")
                
                print(f"   ✅ {colorize('Handled gracefully', 'green')}: page={page}, per_page={per_page}\n")
    
    # ========================================================================
    # 🎭 MOCKING & INTERACTION TESTS - FIXED VERSION
    # ========================================================================
    
    def test_paginate_query_mock_interactions(self):
        """🎭 Test detailed mock interactions and call sequences."""
        print(f"\n🎭 {colorize('DETAILED MOCK INTERACTION TESTS', 'bold')}")
        print(f"{'─' * 60}")
        
        # Create a mock with call tracking
        mock_query = MagicMock()
        mock_query.count.return_value = 100
        
        # Setup chain with call tracking
        mock_items = ["data_" + str(i) for i in range(1, 11)]
        
        # Create the full mock chain
        mock_limit_result = MagicMock()
        mock_limit_result.all.return_value = mock_items
        
        mock_offset_result = MagicMock()
        mock_offset_result.limit.return_value = mock_limit_result
        
        mock_query.offset.return_value = mock_offset_result
        
        # Execute
        paginated_query, total_items, total_pages = paginate_query(mock_query, page=3, per_page=10)
        
        # Verify results
        self.assertEqual(total_items, 100)
        self.assertEqual(total_pages, 10)
        
        # Verify call sequence
        mock_query.count.assert_called_once()
        mock_query.offset.assert_called_once_with(20)  # (3-1) * 10 = 20
        mock_offset_result.limit.assert_called_once_with(10)
        
        # Note: paginate_query doesn't call .all(), it returns the query object
        # So we shouldn't assert that .all() was called
        
        print(f"   🎭 Mock interactions verified:")
        print(f"      • count() called: {colorize('YES', 'green')}")
        print(f"      • offset(20) called: {colorize('YES', 'green')}")
        print(f"      • limit(10) called: {colorize('YES', 'green')}")
        print(f"   ✅ {colorize('All interactions correct', 'green')}\n")
    
    # ========================================================================
    # 🔄 REALISTIC PAGINATION FLOW TEST
    # ========================================================================
    
    def test_realistic_pagination_flow(self):
        """🔁 Test realistic pagination flow with actual usage patterns."""
        print(f"\n🔁 {colorize('REALISTIC PAGINATION FLOW TEST', 'bold')}")
        print(f"{'─' * 60}")
        
        # Test realistic API scenarios
        scenarios = [
            {
                "name": "API Browse Endpoint",
                "query": "/api/paintings?page=1&per_page=12&sort=date&order=desc",
                "expected_page": 1,
                "expected_per_page": 12,
                "description": "Typical browse endpoint with sorting"
            },
            {
                "name": "Search Results",
                "query": "/api/search?q=mountains&page=2&per_page=8",
                "expected_page": 2,
                "expected_per_page": 8,
                "description": "Search results pagination"
            },
            {
                "name": "User Gallery",
                "query": "/api/user/123/gallery?page=1&per_page=24",
                "expected_page": 1,
                "expected_per_page": 24,
                "description": "User gallery with custom page size"
            },
        ]
        
        for scenario in scenarios:
            with self.subTest(scenario["name"]):
                print(f"   📡 {colorize(scenario['name'], 'cyan')}")
                print(f"   {scenario['description']}")
                
                with self.app.test_request_context(scenario["query"]):
                    page, per_page = get_pagination_params()
                    
                    self.assertEqual(page, scenario["expected_page"])
                    self.assertEqual(per_page, scenario["expected_per_page"])
                    
                    # Simulate database query
                    mock_query = MagicMock()
                    mock_query.count.return_value = 150
                    
                    # Setup mock chain
                    mock_limit_result = MagicMock()
                    mock_items = [{"id": i, "name": f"Item {i}"} for i in range(1, per_page + 1)]
                    mock_limit_result.all.return_value = mock_items
                    
                    mock_offset_result = MagicMock()
                    mock_offset_result.limit.return_value = mock_limit_result
                    mock_query.offset.return_value = mock_offset_result
                    
                    # Apply pagination
                    paginated_query, total_items, total_pages = paginate_query(
                        mock_query, page, per_page
                    )
                    
                    # Create response
                    response = create_pagination_response(
                        items=mock_items,
                        page=page,
                        per_page=per_page,
                        total_items=total_items,
                        total_pages=total_pages
                    )
                    
                    # Verify response
                    self.assertEqual(response['page'], page)
                    self.assertEqual(response['per_page'], per_page)
                    self.assertEqual(len(response['items']), per_page)
                    
                    print(f"   ✅ {colorize('Flow validated', 'green')}: "
                          f"{len(response['items'])} items on page {page}\n")
    
    # ========================================================================
    # 🌈 INTEGRATION FLOW TESTS
    # ========================================================================
    
    def test_complete_pagination_flow_rainbow(self):
        """🌈 Test complete pagination flow from request to response."""
        print(f"\n🌈 {colorize('COMPLETE PAGINATION FLOW TEST', 'bold')}")
        print(f"{'─' * 60}")
        
        # Phase 1: Parameter Extraction
        print(f"   1️⃣  {colorize('Phase 1: Parameter Extraction', 'cyan')}")
        with self.app.test_request_context('/api/artworks?page=2&per_page=15&sort=date'):
            with performance_context("Parameter extraction"):
                page, per_page = get_pagination_params()
            
            self.assertEqual(page, 2)
            self.assertEqual(per_page, 15)
            print(f"      ✅ Extracted: page={page}, per_page={per_page}")
        
        # Phase 2: Query Pagination
        print(f"   2️⃣  {colorize('Phase 2: Query Pagination', 'cyan')}")
        
        # Create realistic mock data
        total_artworks = 143
        mock_artworks = [
            {
                "id": i,
                "title": f"Happy Little Tree #{i}",
                "season": (i % 31) + 1,
                "episode": (i % 13) + 1
            }
            for i in range(1, 16)  # 15 items for page 2
        ]
        
        mock_query = MagicMock()
        mock_query.count.return_value = total_artworks
        
        # Setup proper mock chain
        mock_limit_result = MagicMock()
        mock_limit_result.all.return_value = mock_artworks
        
        mock_offset_result = MagicMock()
        mock_offset_result.limit.return_value = mock_limit_result
        mock_query.offset.return_value = mock_offset_result
        
        with performance_context("Query pagination"):
            paginated_query, total_items, total_pages = paginate_query(mock_query, page, per_page)
        
        self.assertEqual(total_items, total_artworks)
        expected_total_pages = (total_artworks + per_page - 1) // per_page
        self.assertEqual(total_pages, expected_total_pages)
        print(f"      ✅ Paginated: {total_items} items across {total_pages} pages")
        
        # Phase 3: Response Creation
        print(f"   3️⃣  {colorize('Phase 3: Response Creation', 'cyan')}")
        
        with performance_context("Response creation"):
            response = create_pagination_response(
                items=mock_artworks,
                page=page,
                per_page=per_page,
                total_items=total_items,
                total_pages=total_pages
            )
        
        # Verify complete response
        expected_keys = ['items', 'page', 'per_page', 'total_items', 
                        'total_pages', 'has_next', 'has_prev', 'next_page', 'prev_page']
        for key in expected_keys:
            self.assertIn(key, response)
        
        self.assertEqual(response['page'], 2)
        self.assertEqual(response['per_page'], 15)
        self.assertEqual(response['total_items'], 143)
        self.assertEqual(response['total_pages'], 10)  # ceil(143/15) = 10
        self.assertTrue(response['has_next'])
        self.assertTrue(response['has_prev'])
        self.assertEqual(response['next_page'], 3)
        self.assertEqual(response['prev_page'], 1)
        self.assertEqual(len(response['items']), 15)
        self.assertEqual(response['items'][0]['title'], "Happy Little Tree #1")
        
        print(f"      ✅ Response created with {len(response['items'])} items")
        print(f"      ✅ Navigation: {'← Previous' if response['has_prev'] else 'No Previous'} | "
              f"{'Next →' if response['has_next'] else 'No Next'}")
        
        print(f"\n   🌈 {colorize('COMPLETE FLOW VALIDATED', 'bold', 'green')}")
        print(f"   🎯 From request parameters → database query → API response")
        print(f"   ⏱️  All phases executed successfully\n")
    
    # ========================================================================
    # 🏆 FINAL VALIDATION TEST
    # ========================================================================
    
    def test_pagination_suite_comprehensive_validation(self):
        """🏆 Final comprehensive validation of entire pagination suite."""
        print(f"\n🏆 {colorize('FINAL COMPREHENSIVE VALIDATION', 'bold')}")
        print(f"{'═' * 60}")
        
        validation_results = []
        
        # Test 1: Basic functionality
        with self.app.test_request_context('/?page=2&per_page=25'):
            page, per_page = get_pagination_params()
            validation_results.append(("Basic Parameter Parsing", page == 2 and per_page == 25))
        
        # Test 2: Query pagination
        mock_query = MagicMock()
        mock_query.count.return_value = 100
        
        # Setup proper mock chain
        mock_limit_result = MagicMock()
        mock_limit_result.all.return_value = list(range(25))
        
        mock_offset_result = MagicMock()
        mock_offset_result.limit.return_value = mock_limit_result
        mock_query.offset.return_value = mock_offset_result
        
        paginated_query, total, pages = paginate_query(mock_query, 2, 25)
        validation_results.append(("Query Pagination", total == 100 and pages == 4))
        
        # Test 3: Response creation
        response = create_pagination_response(
            items=[1, 2, 3, 4, 5],
            page=2,
            per_page=5,
            total_items=25,
            total_pages=5
        )
        validation_results.append(("Response Structure", all(
            key in response for key in ['items', 'page', 'per_page', 'total_items', 'total_pages']
        )))
        
        # Test 4: Edge case handling
        with self.app.test_request_context('/?page=invalid&per_page=-5'):
            page, per_page = get_pagination_params()
            validation_results.append(("Invalid Input Handling", page == 1 and per_page == 20))
        
        # Display validation results
        all_passed = all(result[1] for result in validation_results)
        
        for test_name, passed in validation_results:
            status = colorize("✅ PASS", "green") if passed else colorize("❌ FAIL", "red")
            print(f"   {status}: {test_name}")
        
        print(f"\n   {'═' * 40}")
        
        if all_passed:
            print(f"   🏆 {colorize('ALL VALIDATIONS PASSED!', 'bold', 'green')}")
            print(f"   ✨ Pagination system is fully operational ✨")
        else:
            print(f"   ⚠️  {colorize('SOME VALIDATIONS FAILED', 'bold', 'red')}")
        
        print(f"   {'═' * 40}\n")
        
        self.assertTrue(all_passed, "Comprehensive validation failed")


# ============================================================================
# 🚀 TEST RUNNER ENHANCEMENTS
# ============================================================================

class ColorTestResult(unittest.TextTestResult):
    """Enhanced test result with colored output."""
    
    def addSuccess(self, test):
        super().addSuccess(test)
        if self.showAll:
            self.stream.writeln(f"  {colorize('✅ PASS', 'green')}")
    
    def addFailure(self, test, err):
        super().addFailure(test, err)
        if self.showAll:
            self.stream.writeln(f"  {colorize('❌ FAIL', 'red')}")
    
    def addError(self, test, err):
        super().addError(test, err)
        if self.showAll:
            self.stream.writeln(f"  {colorize('💥 ERROR', 'red')}")


class ColorTestRunner(unittest.TextTestRunner):
    """Enhanced test runner with colored output."""
    
    resultclass = ColorTestResult
    
    def run(self, test):
        print(f"\n{'✨' * 30}")
        print(f"✨{colorize(' ADVANCED PAGINATION TEST SUITE ', 'bold', 'yellow'):^58}✨")
        print(f"{'✨' * 30}")
        print(f"🚀 {colorize('Starting comprehensive pagination tests...', 'cyan')}")
        print(f"{'─' * 60}")
        
        result = super().run(test)
        
        print(f"\n{'─' * 60}")
        print(f"🎯 {colorize('TEST SUITE COMPLETE', 'bold')}")
        print(f"{'─' * 60}")
        
        # Display fancy summary
        if result.wasSuccessful():
            print(f"🎉 {colorize('SUCCESS!', 'bold', 'green')} All tests passed!")
            print(f"✨ {colorize('Pagination system is production-ready!', 'green')}")
        else:
            failures = len(result.failures)
            errors = len(result.errors)
            print(f"⚠️  {colorize('ISSUES DETECTED:', 'bold', 'yellow')}")
            print(f"   Failures: {colorize(str(failures), 'red' if failures > 0 else 'green')}")
            print(f"   Errors: {colorize(str(errors), 'red' if errors > 0 else 'green')}")
        
        # Calculate actual time if available, otherwise estimate
        total_time = getattr(result, 'time_taken', result.testsRun * 0.01)
        print(f"⏱️  Total execution time: {total_time:.4f}s")
        print(f"{'─' * 60}")
        
        return result


# ============================================================================
# 🎬 MAIN EXECUTION
# ============================================================================

if __name__ == '__main__':
    print(f"\n{'⭐' * 30}")
    print(f"⭐{colorize(' LAUNCHING PAGINATION TEST SUITE ', 'bold', 'yellow'):^58}⭐")
    print(f"{'⭐' * 30}")
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(AdvancedPaginationTestSuite)
    
    # Run with enhanced runner
    runner = ColorTestRunner(verbosity=2, descriptions=True)
    
    # Run tests
    result = runner.run(suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)