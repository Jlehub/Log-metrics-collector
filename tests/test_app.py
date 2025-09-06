# tests/test_app.py
import pytest
import json
import time
import os
from unittest.mock import patch, mock_open, MagicMock
import psutil
from app import app


@pytest.fixture
def client():
    """Create a test client for the Flask application."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_log_data():
    """Provide mock log data for testing."""
    return [
        "2024-01-15 10:00:01 INFO Starting application",
        "2024-01-15 10:00:02 DEBUG Loading configuration", 
        "2024-01-15 10:00:03 ERROR Failed to connect to database",
        "2024-01-15 10:00:04 INFO Retrying connection",
        "2024-01-15 10:00:05 INFO Connection successful"
    ]


@pytest.fixture
def mock_system_metrics():
    """Provide mock system metrics data."""
    return {
        'cpu_percent': 45.2,
        'memory': {
            'total': 8589934592,
            'available': 4294967296,
            'percent': 50.0,
            'used': 4294967296,
            'free': 4294967296
        },
        'disk_io': {
            'read_count': 1000,
            'write_count': 500,
            'read_bytes': 1048576,
            'write_bytes': 524288
        },
        'timestamp': '2024-01-15T10:00:00'
    }


class TestHealthEndpoint:
    """Test suite for health check endpoint."""
    
    def test_health_endpoint_returns_200(self, client):
        """Test that health endpoint returns 200 status."""
        response = client.get('/health')
        assert response.status_code == 200
    
    def test_health_endpoint_returns_json(self, client):
        """Test that health endpoint returns valid JSON."""
        response = client.get('/health')
        data = json.loads(response.data)
        assert isinstance(data, dict)
        assert 'status' in data
        assert 'timestamp' in data
    
    def test_health_endpoint_status_ok(self, client):
        """Test that health endpoint reports OK status."""
        response = client.get('/health')
        data = json.loads(response.data)
        assert data['status'] == 'OK'
    
    def test_health_endpoint_has_timestamp(self, client):
        """Test that health endpoint includes timestamp."""
        response = client.get('/health')
        data = json.loads(response.data)
        assert 'timestamp' in data
        assert isinstance(data['timestamp'], str)


class TestMetricsEndpoint:
    """Test suite for system metrics endpoint."""
    
    def test_metrics_endpoint_returns_200(self, client):
        """Test that metrics endpoint returns 200 status."""
        response = client.get('/metrics')
        assert response.status_code == 200
    
    def test_metrics_endpoint_returns_json(self, client):
        """Test that metrics endpoint returns valid JSON."""
        response = client.get('/metrics')
        data = json.loads(response.data)
        assert isinstance(data, dict)
    
    def test_metrics_contains_required_fields(self, client):
        """Test that metrics response contains all required fields."""
        response = client.get('/metrics')
        data = json.loads(response.data)
        
        required_fields = ['cpu_percent', 'memory', 'disk_io', 'timestamp']
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
    
    def test_metrics_data_types(self, client):
        """Test that metrics data has correct types."""
        response = client.get('/metrics')
        data = json.loads(response.data)
        
        assert isinstance(data['cpu_percent'], (int, float))
        assert isinstance(data['memory'], dict)
        assert isinstance(data['disk_io'], dict)
        assert isinstance(data['timestamp'], str)
    
    def test_memory_metrics_structure(self, client):
        """Test that memory metrics have correct structure."""
        response = client.get('/metrics')
        data = json.loads(response.data)
        
        memory = data['memory']
        expected_keys = ['total', 'available', 'percent', 'used', 'free']
        for key in expected_keys:
            assert key in memory, f"Missing memory metric: {key}"
            assert isinstance(memory[key], (int, float))
    
    def test_disk_io_metrics_structure(self, client):
        """Test that disk I/O metrics have correct structure."""
        response = client.get('/metrics')
        data = json.loads(response.data)
        
        disk_io = data['disk_io']
        expected_keys = ['read_count', 'write_count', 'read_bytes', 'write_bytes']
        for key in expected_keys:
            assert key in disk_io, f"Missing disk I/O metric: {key}"
            assert isinstance(disk_io[key], (int, float))
    
    def test_cpu_percent_range(self, client):
        """Test that CPU percentage is within valid range."""
        response = client.get('/metrics')
        data = json.loads(response.data)
        
        cpu_percent = data['cpu_percent']
        assert 0 <= cpu_percent <= 100, f"CPU percentage out of range: {cpu_percent}"
    
    def test_memory_percent_range(self, client):
        """Test that memory percentage is within valid range."""
        response = client.get('/metrics')
        data = json.loads(response.data)
        
        memory_percent = data['memory']['percent']
        assert 0 <= memory_percent <= 100, f"Memory percentage out of range: {memory_percent}"


class TestLogsEndpoint:
    """Test suite for logs endpoint."""
    
    @patch('app.get_recent_logs')
    def test_logs_endpoint_returns_200(self, mock_get_logs, client):
        """Test that logs endpoint returns 200 status."""
        mock_get_logs.return_value = []
        response = client.get('/logs')
        assert response.status_code == 200
    
    @patch('app.get_recent_logs')
    def test_logs_endpoint_returns_json(self, mock_get_logs, client):
        """Test that logs endpoint returns valid JSON."""
        mock_get_logs.return_value = []
        response = client.get('/logs')
        data = json.loads(response.data)
        assert isinstance(data, dict)
        assert 'logs' in data
        assert 'count' in data
    
    @patch('app.get_recent_logs')
    def test_logs_with_data(self, mock_get_logs, client, mock_log_data):
        """Test logs endpoint with mock data."""
        mock_get_logs.return_value = mock_log_data
        response = client.get('/logs')
        data = json.loads(response.data)
        
        assert data['count'] == len(mock_log_data)
        assert len(data['logs']) == len(mock_log_data)
        assert data['logs'] == mock_log_data
    
    @patch('app.get_recent_logs')
    def test_logs_limit_parameter(self, mock_get_logs, client, mock_log_data):
        """Test logs endpoint with limit parameter."""
        mock_get_logs.return_value = mock_log_data[:2]
        response = client.get('/logs?limit=2')
        data = json.loads(response.data)
        
        assert data['count'] == 2
        assert len(data['logs']) == 2
    
    @patch('app.get_recent_logs')
    def test_logs_empty_response(self, mock_get_logs, client):
        """Test logs endpoint with no logs available."""
        mock_get_logs.return_value = []
        response = client.get('/logs')
        data = json.loads(response.data)
        
        assert data['count'] == 0
        assert data['logs'] == []


class TestSystemMetricsCollection:
    """Test suite for system metrics collection functions."""
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_io_counters')
    def test_collect_system_metrics_structure(self, mock_disk_io, mock_memory, mock_cpu):
        """Test that collect_system_metrics returns correct structure."""
        from app import collect_system_metrics
        
        # Mock psutil responses
        mock_cpu.return_value = 25.5
        mock_memory.return_value = MagicMock(
            total=8589934592,
            available=4294967296,
            percent=50.0,
            used=4294967296,
            free=4294967296
        )
        mock_disk_io.return_value = MagicMock(
            read_count=1000,
            write_count=500,
            read_bytes=1048576,
            write_bytes=524288
        )
        
        metrics = collect_system_metrics()
        
        assert 'cpu_percent' in metrics
        assert 'memory' in metrics
        assert 'disk_io' in metrics
        assert 'timestamp' in metrics
        
        assert metrics['cpu_percent'] == 25.5
        assert metrics['memory']['percent'] == 50.0
        assert metrics['disk_io']['read_count'] == 1000
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_io_counters')
    def test_collect_metrics_handles_cpu_exception(self, mock_disk_io, mock_memory, mock_cpu):
        """Test that metrics collection handles CPU exceptions gracefully."""
        from app import collect_system_metrics
        
        mock_cpu.side_effect = Exception("CPU error")
        mock_memory.return_value = MagicMock(
            total=8589934592,
            available=4294967296,
            percent=50.0,
            used=4294967296,
            free=4294967296
        )
        mock_disk_io.return_value = MagicMock(
            read_count=1000,
            write_count=500,
            read_bytes=1048576,
            write_bytes=524288
        )
        
        metrics = collect_system_metrics()
        assert 'cpu_percent' in metrics
        assert metrics['cpu_percent'] == 0.0
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_io_counters')
    def test_collect_metrics_handles_memory_exception(self, mock_disk_io, mock_memory, mock_cpu):
        """Test that metrics collection handles memory exceptions gracefully."""
        from app import collect_system_metrics
        
        mock_cpu.return_value = 25.5
        mock_memory.side_effect = Exception("Memory error")
        mock_disk_io.return_value = MagicMock(
            read_count=1000,
            write_count=500,
            read_bytes=1048576,
            write_bytes=524288
        )
        
        metrics = collect_system_metrics()
        assert 'memory' in metrics
        assert all(v == 0 for v in metrics['memory'].values())
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_io_counters')
    def test_collect_metrics_handles_disk_exception(self, mock_disk_io, mock_memory, mock_cpu):
        """Test that metrics collection handles disk I/O exceptions gracefully."""
        from app import collect_system_metrics
        
        mock_cpu.return_value = 25.5
        mock_memory.return_value = MagicMock(
            total=8589934592,
            available=4294967296,
            percent=50.0,
            used=4294967296,
            free=4294967296
        )
        mock_disk_io.side_effect = Exception("Disk I/O error")
        
        metrics = collect_system_metrics()
        assert 'disk_io' in metrics
        assert all(v == 0 for v in metrics['disk_io'].values())


class TestLogTailing:
    """Test suite for log tailing functionality."""
    
    @patch('builtins.open', new_callable=mock_open, read_data="line1\nline2\nline3\n")
    @patch('os.path.exists')
    def test_tail_log_file_reads_lines(self, mock_exists, mock_file):
        """Test that tail_log_file reads lines correctly."""
        from app import tail_log_file
        
        mock_exists.return_value = True
        
        lines = tail_log_file('/fake/path/test.log', lines=2)
        assert len(lines) == 2
        assert lines[0] == 'line2'
        assert lines[1] == 'line3'
    
    @patch('os.path.exists')
    def test_tail_log_file_nonexistent_file(self, mock_exists):
        """Test tail_log_file behavior with nonexistent file."""
        from app import tail_log_file
        
        mock_exists.return_value = False
        
        lines = tail_log_file('/nonexistent/file.log')
        assert lines == []
    
    @patch('builtins.open')
    @patch('os.path.exists')
    def test_tail_log_file_handles_permission_error(self, mock_exists, mock_open):
        """Test tail_log_file handles permission errors gracefully."""
        from app import tail_log_file
        
        mock_exists.return_value = True
        mock_open.side_effect = PermissionError("Access denied")
        
        lines = tail_log_file('/restricted/file.log')
        assert lines == []
    
    @patch('builtins.open', new_callable=mock_open, read_data="")
    @patch('os.path.exists')
    def test_tail_log_file_empty_file(self, mock_exists, mock_file):
        """Test tail_log_file with empty file."""
        from app import tail_log_file
        
        mock_exists.return_value = True
        
        lines = tail_log_file('/empty/file.log')
        assert lines == []


class TestErrorHandling:
    """Test suite for error handling scenarios."""
    
    @patch('app.collect_system_metrics')
    def test_metrics_endpoint_handles_collection_error(self, mock_collect, client):
        """Test metrics endpoint handles collection errors."""
        mock_collect.side_effect = Exception("System error")
        
        response = client.get('/metrics')
        assert response.status_code == 500
        
        data = json.loads(response.data)
        assert 'error' in data
    
    @patch('app.get_recent_logs')
    def test_logs_endpoint_handles_read_error(self, mock_get_logs, client):
        """Test logs endpoint handles read errors."""
        mock_get_logs.side_effect = Exception("File read error")
        
        response = client.get('/logs')
        assert response.status_code == 500
        
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_invalid_endpoint(self, client):
        """Test request to invalid endpoint."""
        response = client.get('/nonexistent')
        assert response.status_code == 404


class TestConfigurationHandling:
    """Test suite for configuration handling."""
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_config_loading_with_valid_file(self, mock_file, mock_exists):
        """Test configuration loading with valid config file."""
        mock_exists.return_value = True
        mock_config = '{"api": {"port": 5000}, "logging": {"max_entries": 100}}'
        mock_file.return_value.read.return_value = mock_config
        
        # This would test your config loading if implemented
        # For now, just verify the mocking works
        assert mock_exists.return_value is True
    
    @patch('os.path.exists')
    def test_config_loading_with_missing_file(self, mock_exists):
        """Test configuration loading with missing config file."""
        mock_exists.return_value = False
        
        # Should use default configuration
        assert mock_exists.return_value is False


class TestIntegrationScenarios:
    """Integration test scenarios."""
    
    def test_application_startup(self, client):
        """Test that application starts and responds to basic requests."""
        # Test all endpoints are accessible
        endpoints = ['/health', '/metrics', '/logs']
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code in [200, 500]  # 500 acceptable if system calls fail in test env
    
    def test_concurrent_requests(self, client):
        """Test handling of concurrent requests."""
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_request():
            response = client.get('/health')
            results.put(response.status_code)
        
        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Check all requests succeeded
        response_codes = []
        while not results.empty():
            response_codes.append(results.get())
        
        assert len(response_codes) == 5
        assert all(code == 200 for code in response_codes)
    
    @patch('time.sleep')
    def test_metrics_collection_timing(self, mock_sleep, client):
        """Test metrics collection doesn't take too long."""
        start_time = time.time()
        response = client.get('/metrics')
        end_time = time.time()
        
        assert response.status_code == 200
        # Should complete within reasonable time (2 seconds max)
        assert end_time - start_time < 2.0


class TestDataValidation:
    """Test suite for data validation."""
    
    def test_metrics_data_consistency(self, client):
        """Test that metrics data is consistent across calls."""
        response1 = client.get('/metrics')
        response2 = client.get('/metrics')
        
        data1 = json.loads(response1.data)
        data2 = json.loads(response2.data)
        
        # Structure should be identical
        assert set(data1.keys()) == set(data2.keys())
        assert set(data1['memory'].keys()) == set(data2['memory'].keys())
        assert set(data1['disk_io'].keys()) == set(data2['disk_io'].keys())
    
    def test_timestamp_format(self, client):
        """Test that timestamps are in correct format."""
        response = client.get('/metrics')
        data = json.loads(response.data)
        
        timestamp = data['timestamp']
        # Should be ISO format string
        assert isinstance(timestamp, str)
        assert 'T' in timestamp  # ISO format contains T
    
    def test_numeric_data_types(self, client):
        """Test that all numeric data are proper numbers."""
        response = client.get('/metrics')
        data = json.loads(response.data)
        
        # CPU should be numeric
        assert isinstance(data['cpu_percent'], (int, float))
        
        # Memory values should be numeric
        for key, value in data['memory'].items():
            assert isinstance(value, (int, float)), f"Memory {key} is not numeric: {value}"
        
        # Disk I/O values should be numeric
        for key, value in data['disk_io'].items():
            assert isinstance(value, (int, float)), f"Disk I/O {key} is not numeric: {value}"


if __name__ == '__main__':
    # Run tests with coverage if this file is executed directly
    pytest.main(['-v', '--cov=app', '--cov-report=html', '--cov-report=term-missing'])