#!/usr/bin/env python3
"""
Log & Metrics Collector - Enhanced Version with Flask REST API
A lightweight system monitoring tool that collects metrics and monitors log files.
"""

import psutil
import time
import json
from datetime import datetime
import threading
from collections import deque
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import re
import argparse
import logging

# Flask imports
from flask import Flask, jsonify, request
from flask_cors import CORS


class LogFileHandler(FileSystemEventHandler):
    """Handles log file changes and processes new log entries"""
    
    def __init__(self, log_collector):
        self.log_collector = log_collector
        self.file_positions = {}  # Track file read positions
    
    def on_modified(self, event):
        """Called when a file is modified"""
        if not event.is_directory and event.src_path.endswith('.log'):
            self.process_log_file(event.src_path)
    
    def process_log_file(self, file_path):
        """Process new lines in log file"""
        try:
            # Get current file size
            current_size = os.path.getsize(file_path)
            
            # Get last known position
            last_position = self.file_positions.get(file_path, 0)
            
            if current_size > last_position:
                # Read new content
                with open(file_path, 'r', encoding='utf-8') as f:
                    f.seek(last_position)
                    new_lines = f.readlines()
                    
                    # Process each new line
                    for line in new_lines:
                        line = line.strip()
                        if line:  # Skip empty lines
                            self.log_collector.add_log_entry(file_path, line)
                
                # Update position
                self.file_positions[file_path] = current_size
                
        except Exception as e:
            logging.error(f"Error processing log file {file_path}: {e}")


class LogCollector:
    """Collects and manages log entries"""
    
    def __init__(self, max_entries=200):
        self.max_entries = max_entries
        self.log_entries = deque(maxlen=max_entries)
        self.log_stats = {
            'total_entries': 0,
            'error_count': 0,
            'warning_count': 0,
            'info_count': 0,
            'debug_count': 0,
            'unknown_count': 0
        }
        self.lock = threading.Lock()  # Thread safety for API access
    
    def add_log_entry(self, file_path, line):
        """Add a new log entry"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'file': os.path.basename(file_path),
            'full_path': file_path,
            'message': line,
            'level': self.extract_log_level(line)
        }
        
        with self.lock:
            self.log_entries.append(entry)
            self.log_stats['total_entries'] += 1
            
            # Update level counts
            level = entry['level'].lower()
            count_key = f'{level}_count'
            if count_key in self.log_stats:
                self.log_stats[count_key] += 1
        
        # Display new log entry
        print(f"📝 [{entry['level']}] {entry['file']}: {line}")
    
    def extract_log_level(self, log_line):
        """Extract log level from log line"""
        # Common log level patterns
        patterns = [
            r'\[?(ERROR|CRITICAL|FATAL)\]?',
            r'\[?(WARN|WARNING)\]?',
            r'\[?(INFO|INFORMATION)\]?',
            r'\[?(DEBUG|TRACE)\]?'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, log_line, re.IGNORECASE)
            if match:
                level = match.group(1).upper()
                if level in ['WARN', 'WARNING']:
                    return 'WARNING'
                elif level in ['INFO', 'INFORMATION']:
                    return 'INFO'
                elif level in ['ERROR', 'CRITICAL', 'FATAL']:
                    return 'ERROR'
                elif level in ['DEBUG', 'TRACE']:
                    return 'DEBUG'
        
        return 'UNKNOWN'
    
    def get_recent_logs(self, limit=10, level_filter=None):
        """Get recent log entries with optional filtering"""
        with self.lock:
            logs = list(self.log_entries)
        
        # Apply level filter if specified
        if level_filter:
            level_filter = level_filter.upper()
            logs = [log for log in logs if log['level'] == level_filter]
        
        # Apply limit
        if limit:
            logs = logs[-limit:]
            
        return logs
    
    def get_log_stats(self):
        """Get log statistics"""
        with self.lock:
            return self.log_stats.copy()


class SystemMetrics:
    """Collects and stores system metrics (enhanced version)"""
    
    def __init__(self, max_history=100):
        self.max_history = max_history
        self.metrics_history = deque(maxlen=max_history)
        self.is_collecting = False
        self.collection_thread = None
        self.lock = threading.Lock()  # Thread safety for API access
        
    def get_current_metrics(self):
        """Get current system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_gb = memory.used / (1024**3)
            memory_total_gb = memory.total / (1024**3)
            
            # Disk metrics (Windows compatible)
            disk = psutil.disk_usage('C:' if os.name == 'nt' else '/')
            disk_percent = disk.percent
            disk_used_gb = disk.used / (1024**3)
            disk_total_gb = disk.total / (1024**3)
            
            # Process count
            process_count = len(psutil.pids())
            
            # Network metrics
            try:
                network = psutil.net_io_counters()
                network_data = {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                }
            except:
                network_data = {'bytes_sent': 0, 'bytes_recv': 0, 'packets_sent': 0, 'packets_recv': 0}
            
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count
                },
                'memory': {
                    'percent': memory_percent,
                    'used_gb': round(memory_used_gb, 2),
                    'total_gb': round(memory_total_gb, 2)
                },
                'disk': {
                    'percent': disk_percent,
                    'used_gb': round(disk_used_gb, 2),
                    'total_gb': round(disk_total_gb, 2)
                },
                'processes': process_count,
                'network': network_data
            }
            
            return metrics
            
        except Exception as e:
            logging.error(f"Error collecting metrics: {e}")
            return None
    
    def collect_metrics_continuously(self, interval=5):
        """Continuously collect metrics in background thread"""
        while self.is_collecting:
            metrics = self.get_current_metrics()
            if metrics:
                with self.lock:
                    self.metrics_history.append(metrics)
                print(f"📊 [{metrics['timestamp'][:19]}] "
                      f"CPU: {metrics['cpu']['percent']:5.1f}% | "
                      f"Memory: {metrics['memory']['percent']:5.1f}% | "
                      f"Disk: {metrics['disk']['percent']:5.1f}% | "
                      f"Processes: {metrics['processes']}")
            time.sleep(interval)
    
    def start_collection(self, interval=5):
        """Start continuous metrics collection"""
        if not self.is_collecting:
            self.is_collecting = True
            self.collection_thread = threading.Thread(
                target=self.collect_metrics_continuously,
                args=(interval,),
                daemon=True
            )
            self.collection_thread.start()
            print("✅ Metrics collection started")
        else:
            print("⚠️  Metrics collection already running")
    
    def stop_collection(self):
        """Stop continuous metrics collection"""
        self.is_collecting = False
        if self.collection_thread:
            self.collection_thread.join(timeout=1)
        print("🛑 Metrics collection stopped")
    
    def get_metrics_history(self, limit=None):
        """Get metrics history with optional limit"""
        with self.lock:
            metrics = list(self.metrics_history)
        
        if limit:
            metrics = metrics[-limit:]
        
        return metrics


class LogMetricsCollector:
    """Main application class with Flask REST API"""
    
    def __init__(self, config=None):
        # Default configuration
        self.config = config or {
            'api': {'host': '0.0.0.0', 'port': 5000, 'debug': False},
            'metrics': {'collection_interval': 10, 'max_samples': 1000},
            'logging': {'directories': ['logs'], 'max_entries': 200}
        }
        
        # Initialize components
        self.metrics_collector = SystemMetrics(
            max_history=self.config['metrics']['max_samples']
        )
        self.log_collector = LogCollector(
            max_entries=self.config['logging']['max_entries']
        )
        self.file_observer = Observer()
        self.log_handler = LogFileHandler(self.log_collector)
        
        # Initialize Flask app
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for web browser access
        self.setup_api_routes()
        
        self.is_running = False
    
    def setup_api_routes(self):
        """Setup Flask REST API routes"""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0',
                'components': {
                    'metrics_collector': self.metrics_collector.is_collecting,
                    'log_monitor': self.is_running
                }
            }), 200
        
        @self.app.route('/metrics', methods=['GET'])
        def get_metrics():
            """Get system metrics"""
            try:
                # Get query parameters
                limit = request.args.get('limit', type=int)
                current_only = request.args.get('current', type=bool, default=False)
                
                if current_only:
                    # Return only current metrics
                    current_metrics = self.metrics_collector.get_current_metrics()
                    if current_metrics:
                        return jsonify({
                            'metrics': [current_metrics],
                            'count': 1,
                            'type': 'current'
                        }), 200
                    else:
                        return jsonify({'error': 'Could not collect current metrics'}), 500
                else:
                    # Return historical metrics
                    metrics = self.metrics_collector.get_metrics_history(limit=limit)
                    return jsonify({
                        'metrics': metrics,
                        'count': len(metrics),
                        'type': 'historical'
                    }), 200
                    
            except Exception as e:
                logging.error(f"Error in /metrics endpoint: {e}")
                return jsonify({'error': 'Internal server error'}), 500
        
        @self.app.route('/logs', methods=['GET'])
        def get_logs():
            """Get log entries with filtering"""
            try:
                # Get query parameters
                limit = request.args.get('limit', type=int, default=50)
                level_filter = request.args.get('level')
                
                logs = self.log_collector.get_recent_logs(
                    limit=limit, 
                    level_filter=level_filter
                )
                
                return jsonify({
                    'logs': logs,
                    'count': len(logs),
                    'filter': {
                        'level': level_filter,
                        'limit': limit
                    }
                }), 200
                
            except Exception as e:
                logging.error(f"Error in /logs endpoint: {e}")
                return jsonify({'error': 'Internal server error'}), 500
        
        @self.app.route('/logs/stats', methods=['GET'])
        def get_log_stats():
            """Get log statistics"""
            try:
                stats = self.log_collector.get_log_stats()
                return jsonify({
                    'statistics': stats,
                    'timestamp': datetime.now().isoformat()
                }), 200
            except Exception as e:
                logging.error(f"Error in /logs/stats endpoint: {e}")
                return jsonify({'error': 'Internal server error'}), 500
        
        @self.app.route('/status', methods=['GET'])
        def get_status():
            """Get application status and health"""
            try:
                return jsonify({
                    'status': 'running' if self.is_running else 'stopped',
                    'timestamp': datetime.now().isoformat(),
                    'components': {
                        'metrics_collector': {
                            'active': self.metrics_collector.is_collecting,
                            'samples_collected': len(self.metrics_collector.metrics_history),
                            'max_samples': self.metrics_collector.max_history
                        },
                        'log_monitor': {
                            'active': self.is_running,
                            'entries_collected': len(self.log_collector.log_entries),
                            'max_entries': self.log_collector.max_entries,
                            'monitored_directories': self.config['logging']['directories']
                        }
                    },
                    'configuration': {
                        'metrics_interval': self.config['metrics']['collection_interval'],
                        'api_host': self.config['api']['host'],
                        'api_port': self.config['api']['port']
                    }
                }), 200
            except Exception as e:
                logging.error(f"Error in /status endpoint: {e}")
                return jsonify({'error': 'Internal server error'}), 500
        
        @self.app.route('/config', methods=['GET'])
        def get_config():
            """Get current configuration"""
            return jsonify({
                'configuration': self.config,
                'timestamp': datetime.now().isoformat()
            }), 200
        
        # Add a root endpoint for API documentation
        @self.app.route('/', methods=['GET'])
        def api_info():
            """API information and available endpoints"""
            return jsonify({
                'name': 'Log & Metrics Collector API',
                'version': '1.0.0',
                'description': 'REST API for system metrics and log monitoring',
                'endpoints': {
                    'GET /': 'API information',
                    'GET /health': 'Health check',
                    'GET /metrics': 'System metrics (params: ?limit=N, ?current=true)',
                    'GET /logs': 'Log entries (params: ?limit=N, ?level=ERROR|WARNING|INFO|DEBUG)',
                    'GET /logs/stats': 'Log statistics',
                    'GET /status': 'Application status',
                    'GET /config': 'Current configuration'
                },
                'examples': {
                    'current_metrics': '/metrics?current=true',
                    'last_10_metrics': '/metrics?limit=10',
                    'error_logs': '/logs?level=ERROR&limit=20',
                    'recent_logs': '/logs?limit=50'
                }
            }), 200
    
    def start_monitoring(self, metrics_interval=10):
        """Start both metrics and log monitoring"""
        print("🚀 Starting Log & Metrics Collector with REST API...")
        
        # Start metrics collection
        self.metrics_collector.start_collection(metrics_interval)
        
        # Start log file monitoring
        self.start_log_monitoring()
        
        self.is_running = True
        print("✅ All monitoring systems active!")
        
        # Initial load of existing log files
        self.load_existing_logs()
    
    def start_log_monitoring(self):
        """Start log file monitoring"""
        for log_dir in self.config['logging']['directories']:
            if os.path.exists(log_dir):
                self.file_observer.schedule(
                    self.log_handler,
                    path=log_dir,
                    recursive=True
                )
                print(f"👀 Monitoring log directory: {log_dir}")
            else:
                print(f"⚠️  Log directory not found: {log_dir}")
                # Create directory if it doesn't exist
                os.makedirs(log_dir, exist_ok=True)
                print(f"📁 Created log directory: {log_dir}")
        
        self.file_observer.start()
    
    def load_existing_logs(self):
        """Load existing log entries from files"""
        print("📚 Loading existing log files...")
        
        for log_dir in self.config['logging']['directories']:
            if os.path.exists(log_dir):
                for filename in os.listdir(log_dir):
                    if filename.endswith('.log'):
                        file_path = os.path.join(log_dir, filename)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                lines = f.readlines()
                                # Load last 10 lines to show recent context
                                for line in lines[-10:]:
                                    line = line.strip()
                                    if line:
                                        self.log_collector.add_log_entry(file_path, line)
                        except Exception as e:
                            logging.error(f"Error loading {file_path}: {e}")
    
    def stop_monitoring(self):
        """Stop all monitoring"""
        print("\n🛑 Stopping monitoring systems...")
        
        self.is_running = False
        self.metrics_collector.stop_collection()
        self.file_observer.stop()
        self.file_observer.join()
        
        self.display_summary()
    
    def display_summary(self):
        """Display final summary"""
        print("\n" + "="*80)
        print("📈 MONITORING SESSION SUMMARY")
        print("="*80)
        
        # Metrics summary
        metrics_count = len(self.metrics_collector.metrics_history)
        print(f"📊 Collected {metrics_count} metric samples")
        
        if metrics_count > 0:
            latest_metrics = self.metrics_collector.metrics_history[-1]
            print(f"💻 Final CPU: {latest_metrics['cpu']['percent']}%")
            print(f"🧠 Final Memory: {latest_metrics['memory']['percent']}%")
            print(f"💾 Final Disk: {latest_metrics['disk']['percent']}%")
        
        # Log summary
        log_stats = self.log_collector.get_log_stats()
        print(f"\n📝 Log Statistics:")
        print(f"   Total entries: {log_stats['total_entries']}")
        print(f"   Errors: {log_stats['error_count']}")
        print(f"   Warnings: {log_stats['warning_count']}")
        print(f"   Info: {log_stats['info_count']}")
        
        print("="*80)
        print("👋 Goodbye!")
    
    def run_api_server(self):
        """Run the Flask API server"""
        host = self.config['api']['host']
        port = self.config['api']['port']
        debug = self.config['api']['debug']
        
        print(f"🌐 Starting REST API server on http://{host}:{port}")
        print(f"📚 API Documentation available at: http://{host}:{port}/")
        
        # Run Flask app
        self.app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True,
            use_reloader=False  # Disable reloader to avoid threading issues
        )


def load_config(config_file='config.json'):
    """Load configuration from JSON file"""
    default_config = {
        'api': {
            'host': '0.0.0.0',
            'port': 5000,
            'debug': False
        },
        'metrics': {
            'collection_interval': 10,
            'max_samples': 1000
        },
        'logging': {
            'directories': ['logs'],
            'max_entries': 200
        }
    }
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                # Merge configurations
                for section in user_config:
                    if section in default_config:
                        default_config[section].update(user_config[section])
                    else:
                        default_config[section] = user_config[section]
        except Exception as e:
            logging.warning(f"Error loading config file {config_file}: {e}")
            print(f"⚠️  Using default configuration due to config error: {e}")
    
    return default_config


def simulate_log_activity():
    """Generate some test log entries (for demo purposes)"""
    import random
    
    log_messages = [
        "[INFO] User authentication successful",
        "[INFO] Database query completed in 150ms",
        "[WARNING] High memory usage detected",
        "[ERROR] Failed to connect to external API",
        "[INFO] Backup process started",
        "[INFO] Cache cleared successfully",
        "[WARNING] Disk space running low",
        "[ERROR] Invalid user input received",
        "[INFO] System health check passed",
        "[DEBUG] Debug information logged",
        "[ERROR] Database connection timeout",
        "[WARNING] CPU usage above threshold"
    ]
    
    def write_random_logs():
        while True:
            time.sleep(random.randint(15, 45))  # Random interval
            message = random.choice(log_messages)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            os.makedirs('logs', exist_ok=True)
            with open("logs/test.log", "a") as f:
                f.write(f"{timestamp} {message}\n")
    
    # Start log simulation in background
    thread = threading.Thread(target=write_random_logs, daemon=True)
    thread.start()


def main():
    """Main function"""
    # Setup argument parser
    parser = argparse.ArgumentParser(description='Log & Metrics Collector with REST API')
    parser.add_argument('--config', '-c', default='config.json', 
                       help='Configuration file path')
    parser.add_argument('--port', '-p', type=int, 
                       help='API server port (overrides config)')
    parser.add_argument('--no-api', action='store_true',
                       help='Run without API server (console only)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='Logging level')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Load configuration
    config = load_config(args.config)
    
    # Override port if specified
    if args.port:
        config['api']['port'] = args.port
    
    print("🚀 Log & Metrics Collector - Enhanced Version with REST API")
    print("This tool monitors system metrics AND log files!")
    
    if args.no_api:
        print("Running in console-only mode (no API server)")
    else:
        print(f"REST API will be available at http://{config['api']['host']}:{config['api']['port']}")
    
    print("Press Ctrl+C to stop\n")
    
    # Create the main collector
    collector = LogMetricsCollector(config)
    
    try:
        # Start monitoring
        collector.start_monitoring(
            metrics_interval=config['metrics']['collection_interval']
        )
        
        # Start log simulation (for demo)
        simulate_log_activity()
        
        if not args.no_api:
            print(f"\n💡 API Endpoints available:")
            print(f"   http://localhost:{config['api']['port']}/")
            print(f"   http://localhost:{config['api']['port']}/health")
            print(f"   http://localhost:{config['api']['port']}/metrics")
            print(f"   http://localhost:{config['api']['port']}/logs")
            print(f"   http://localhost:{config['api']['port']}/status")
            print(f"\n💡 Try these commands in another terminal:")
            print(f"   curl http://localhost:{config['api']['port']}/health")
            print(f"   curl http://localhost:{config['api']['port']}/metrics?current=true")
            print(f"   curl http://localhost:{config['api']['port']}/logs?level=ERROR")
            print(f"\n📝 Add test logs:")
            print(f"   echo \"[ERROR] This is a test error\" >> logs/test.log")
            print(f"   echo \"[INFO] Application restarted\" >> logs/test.log\n")
            
            # Run API server (this will block)
            collector.run_api_server()
        else:
            # Console-only mode
            print("\n💡 Try adding entries to logs/test.log in another terminal:")
            print("   echo \"[ERROR] This is a test error\" >> logs/test.log")
            print("   echo \"[INFO] Application restarted\" >> logs/test.log\n")
            
            # Keep running
            while collector.is_running:
                time.sleep(1)
            
    except KeyboardInterrupt:
        collector.stop_monitoring()
    except Exception as e:
        logging.error(f"Application error: {e}")
        collector.stop_monitoring()


if __name__ == "__main__":
    main()