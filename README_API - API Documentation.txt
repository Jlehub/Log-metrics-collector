# Log & Metrics Collector REST API Documentation

## Overview

The Log & Metrics Collector provides a RESTful API for accessing system metrics and log data. This API enables integration with monitoring dashboards, alerting systems, and other DevOps tools.

**Base URL**: `http://localhost:5000` (configurable)
**API Version**: 1.0.0
**Response Format**: JSON

## Quick Start

```bash
# Start the application
python main.py

# Test the API
curl http://localhost:5000/health
```

## Authentication

Currently, the API does not require authentication. For production deployments, consider implementing API key authentication or OAuth.

## Rate Limiting

Default limit: 100 requests per minute per IP (configurable in config.json)

## API Endpoints

### 1. Root Endpoint

**GET /**

Returns API information and available endpoints.

**Response:**
```json
{
  "name": "Log & Metrics Collector API",
  "version": "1.0.0",
  "description": "REST API for system metrics and log monitoring",
  "endpoints": {
    "GET /": "API information",
    "GET /health": "Health check",
    "GET /metrics": "System metrics",
    "GET /logs": "Log entries",
    "GET /logs/stats": "Log statistics",
    "GET /status": "Application status",
    "GET /config": "Current configuration"
  }
}
```

### 2. Health Check

**GET /health**

Returns the health status of the application and its components.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-08-11T15:30:00.123456",
  "version": "1.0.0",
  "components": {
    "metrics_collector": true,
    "log_monitor": true
  }
}
```

**Status Codes:**
- `200 OK`: Application is healthy
- `503 Service Unavailable`: One or more components are unhealthy

### 3. System Metrics

**GET /metrics**

Returns system metrics data.

**Query Parameters:**
- `limit` (integer): Maximum number of metric samples to return
- `current` (boolean): If true, returns only the current metrics

**Examples:**
```bash
# Get current metrics only
curl "http://localhost:5000/metrics?current=true"

# Get last 10 metric samples
curl "http://localhost:5000/metrics?limit=10"

# Get all available metrics
curl http://localhost:5000/metrics
```

**Response:**
```json
{
  "metrics": [
    {
      "timestamp": "2025-08-11T15:30:00.123456",
      "cpu": {
        "percent": 15.2,
        "count": 8
      },
      "memory": {
        "percent": 45.3,
        "used_gb": 7.2,
        "total_gb": 16.0
      },
      "disk": {
        "percent": 67.8,
        "used_gb": 678.0,
        "total_gb": 1000.0
      },
      "processes": 156,
      "network": {
        "bytes_sent": 1048576,
        "bytes_recv": 2097152,
        "packets_sent": 1000,
        "packets_recv": 1500
      }
    }
  ],
  "count": 1,
  "type": "current"
}
```

**Metric Fields:**
- `timestamp`: ISO format timestamp
- `cpu.percent`: CPU usage percentage
- `cpu.count`: Number of CPU cores
- `memory.percent`: Memory usage percentage
- `memory.used_gb`: Used memory in GB
- `memory.total_gb`: Total memory in GB
- `disk.percent`: Disk usage percentage
- `disk.used_gb`: Used disk space in GB
- `disk.total_gb`: Total disk space in GB
- `processes`: Number of running processes
- `network.bytes_sent/recv`: Network traffic in bytes
- `network.packets_sent/recv`: Network packets count

### 4. Log Entries

**GET /logs**

Returns log entries with optional filtering.

**Query Parameters:**
- `limit` (integer): Maximum number of log entries to return (default: 50)
- `level` (string): Filter by log level (ERROR, WARNING, INFO, DEBUG, UNKNOWN)

**Examples:**
```bash
# Get recent logs (default 50)
curl http://localhost:5000/logs

# Get last 10 logs
curl "http://localhost:5000/logs?limit=10"

# Get only ERROR level logs
curl "http://localhost:5000/logs?level=ERROR"

# Get last 20 WARNING logs
curl "http://localhost:5000/logs?level=WARNING&limit=20"
```

**Response:**
```json
{
  "logs": [
    {
      "timestamp": "2025-08-11T15:30:00.123456",
      "file": "test.log",
      "full_path": "/path/to/logs/test.log",
      "message": "2025-08-11 15:30:00 [INFO] User authentication successful",
      "level": "INFO"
    }
  ],
  "count": 1,
  "filter": {
    "level": null,
    "limit": 50
  }
}
```

**Log Entry Fields:**
- `timestamp`: When the log was captured (ISO format)
- `file`: Log filename
- `full_path`: Complete file path
- `message`: Original log message
- `level`: Extracted log level (ERROR, WARNING, INFO, DEBUG, UNKNOWN)

**Supported Log Levels:**
- `ERROR`: Error, critical, fatal messages
- `WARNING`: Warning messages
- `INFO`: Informational messages
- `DEBUG`: Debug and trace messages
- `UNKNOWN`: Messages without recognizable log levels

### 5. Log Statistics

**GET /logs/stats**

Returns statistics about collected log entries.

**Response:**
```json
{
  "statistics": {
    "total_entries": 150,
    "error_count": 12,
    "warning_count": 25,
    "info_count": 98,
    "debug_count": 10,
    "unknown_count": 5
  },
  "timestamp": "2025-08-11T15:30:00.123456"
}
```

### 6. Application Status

**GET /status**

Returns detailed application status and configuration information.

**Response:**
```json
{
  "status": "running",
  "timestamp": "2025-08-11T15:30:00.123456",
  "components": {
    "metrics_collector": {
      "active": true,
      "samples_collected": 120,
      "max_samples": 1000
    },
    "log_monitor": {
      "active": true,
      "entries_collected": 150,
      "max_entries": 500,
      "monitored_directories": ["logs", "/var/log"]
    }
  },
  "configuration": {
    "metrics_interval": 10,
    "api_host": "0.0.0.0",
    "api_port": 5000
  }
}
```

### 7. Configuration

**GET /config**

Returns the current application configuration.

**Response:**
```json
{
  "configuration": {
    "api": {
      "host": "0.0.0.0",
      "port": 5000,
      "debug": false
    },
    "metrics": {
      "collection_interval": 10,
      "max_samples": 1000
    },
    "logging": {
      "directories": ["logs"],
      "max_entries": 500
    }
  },
  "timestamp": "2025-08-11T15:30:00.123456"
}
```

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200 OK`: Successful request
- `400 Bad Request`: Invalid parameters
- `404 Not Found`: Endpoint not found
- `500 Internal Server Error`: Application error
- `503 Service Unavailable`: Service unhealthy

**Error Response Format:**
```json
{
  "error": "Error message description",
  "timestamp": "2025-08-11T15:30:00.123456"
}
```

## Usage Examples

### Monitoring Dashboard Integration

```javascript
// JavaScript example for dashboard
async function getSystemMetrics() {
  try {
    const response = await fetch('http://localhost:5000/metrics?current=true');
    const data = await response.json();
    return data.metrics[0];
  } catch (error) {
    console.error('Error fetching metrics:', error);
  }
}

// Usage
const metrics = await getSystemMetrics();
console.log(`CPU: ${metrics.cpu.percent}%`);
```

### Log Monitoring Script

```bash
#!/bin/bash
# Check for recent errors
ERROR_COUNT=$(curl -s "http://localhost:5000/logs?level=ERROR&limit=10" | jq '.count')

if [ "$ERROR_COUNT" -gt 5 ]; then
  echo "ALERT: $ERROR_COUNT errors found in recent logs"
  # Send alert notification
fi
```

### Python Integration

```python
import requests

class MetricsCollectorClient:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
    
    def get_current_metrics(self):
        response = requests.get(f"{self.base_url}/metrics?current=true")
        return response.json()
    
    def get_error_logs(self, limit=20):
        response = requests.get(f"{self.base_url}/logs?level=ERROR&limit={limit}")
        return response.json()
    
    def check_health(self):
        response = requests.get(f"{self.base_url}/health")
        return response.status_code == 200

# Usage
client = MetricsCollectorClient()
metrics = client.get_current_metrics()
print(f"CPU Usage: {metrics['metrics'][0]['cpu']['percent']}%")
```

## Configuration

The API behavior can be customized through `config.json`:

```json
{
  "api": {
    "host": "0.0.0.0",
    "port": 5000,
    "debug": false
  },
  "metrics": {
    "collection_interval": 10,
    "max_samples": 1000
  },
  "logging": {
    "directories": ["logs", "/var/log"],
    "max_entries": 500
  }
}
```

## CORS Support

The API includes CORS (Cross-Origin Resource Sharing) support, allowing access from web browsers and different domains. This enables:

- Web dashboard integration
- Browser-based monitoring tools
- Cross-domain API calls

## Performance Considerations

- **Metrics Collection**: CPU sampling takes ~1 second, affecting response time for current metrics
- **Memory Usage**: Bounded by `max_samples` and `max_entries` configuration
- **Concurrent Requests**: Thread-safe design supports multiple simultaneous requests
- **Log File Size**: Large log files may impact startup time during initial loading

## Deployment Notes

### Development
```bash
python main.py --debug --port 8080
```

### Production
```bash
python main.py --config production_config.json --log-level WARNING
```

### Docker
```bash
docker build -t log-metrics-collector .
docker run -p 5000:5000 -v $(pwd)/logs:/app/logs log-metrics-collector
```

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Check if application is running
   - Verify correct port number
   - Check firewall settings

2. **Empty Metrics**
   - Wait for initial collection cycle (based on `collection_interval`)
   - Check `/status` endpoint for component health

3. **No Logs Appearing**
   - Verify log directories exist and are writable
   - Check log file permissions
   - Ensure log files have `.log` extension

4. **High Memory Usage**
   - Adjust `max_samples` and `max_entries` in configuration
   - Monitor collection intervals

### Debug Mode

Enable debug mode for detailed logging:
```bash
python main.py --log-level DEBUG
```

## Support

For issues and questions:
- Check application logs for error messages
- Verify configuration settings
- Test individual endpoints for specific issues
- Review system resource availability

## Changelog

### Version 1.0.0
- Initial REST API implementation
- System metrics collection
- Log file monitoring
- Health check endpoints
- CORS support
- Configuration management
