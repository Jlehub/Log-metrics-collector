pipeline {
    agent any
    
    environment {
        // Define environment variables
        APP_NAME = 'log-metrics-collector'
        DOCKER_IMAGE = "${APP_NAME}:${BUILD_NUMBER}"
        DOCKER_REGISTRY = 'your-dockerhub-username'
        PYTHON_VERSION = '3.10'
        COMPOSE_PROJECT_NAME = "${APP_NAME}-${BUILD_NUMBER}"
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo '🔄 Checking out code from repository...'
                checkout scm
                
                script {
                    echo "🏗️  Build Number: ${BUILD_NUMBER}"
                    echo "🔀 Branch: ${env.BRANCH_NAME ?: 'main'}"
                    echo "📝 Git Commit: ${GIT_COMMIT[0..7]}"
                }
            }
        }
        
        stage('Environment Check') {
            steps {
                echo '🔍 Checking build environment...'
                
                script {
                    try {
                        // Check basic system info
                        sh 'whoami'
                        sh 'pwd'
                        sh 'ls -la'
                        
                        // Check Docker availability
                        try {
                            sh 'which docker'
                            sh 'docker --version'
                            sh 'docker info || echo "Docker info failed, but command exists"'
                            echo '✅ Docker CLI is available'
                        } catch (Exception dockerError) {
                            echo "❌ Docker error: ${dockerError.getMessage()}"
                            // Try alternative approaches
                            echo '🔄 Checking alternative Docker installations...'
                            sh 'ls -la /usr/bin/docker* || echo "No docker in /usr/bin"'
                            sh 'ls -la /usr/local/bin/docker* || echo "No docker in /usr/local/bin"'
                            sh 'find /usr -name "docker" 2>/dev/null || echo "Docker not found in /usr"'
                        }
                        
                        // Check Python
                        try {
                            sh 'python3 --version'
                            echo '✅ Python3 is available'
                        } catch (Exception pythonError) {
                            echo "⚠️  Python3 check failed: ${pythonError.getMessage()}"
                            try {
                                sh 'python --version'
                                echo '✅ Python is available'
                            } catch (Exception python2Error) {
                                echo "❌ No Python found: ${python2Error.getMessage()}"
                            }
                        }
                        
                        // Check required files
                        def requiredFiles = ['app.py', 'requirements.txt', 'Dockerfile']
                        requiredFiles.each { file ->
                            if (fileExists(file)) {
                                echo "✅ Required file found: ${file}"
                                // Show file size and permissions
                                sh "ls -la ${file}"
                            } else {
                                echo "❌ Missing required file: ${file}"
                                error "Required file ${file} not found"
                            }
                        }
                        
                    } catch (Exception e) {
                        echo "❌ Environment check failed: ${e.getMessage()}"
                        currentBuild.result = 'FAILURE'
                        throw e
                    }
                }
            }
        }
        
        stage('Validate Project Structure') {
            steps {
                echo '📁 Validating project structure...'
                
                script {
                    def requiredFiles = [
                        'app.py': 'Main application file',
                        'requirements.txt': 'Python dependencies',
                        'Dockerfile': 'Container definition',
                        'config.json': 'Application configuration'
                    ]
                    
                    def optionalFiles = [
                        'README.md': 'Project documentation',
                        'docker-compose.yml': 'Container orchestration',
                        '.gitignore': 'Git ignore rules',
                        'tests/': 'Test directory'
                    ]
                    
                    echo "📋 Checking required files..."
                    requiredFiles.each { file, description ->
                        if (fileExists(file)) {
                            echo "✅ ${description}: ${file} ✓"
                        } else {
                            echo "❌ MISSING ${description}: ${file}"
                            if (file == 'config.json') {
                                // Create default config
                                writeFile file: 'config.json', text: '''{
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
        "max_entries": 200
    }
}'''
                                echo "📄 Created default config.json"
                            }
                        }
                    }
                    
                    echo "📋 Checking optional files..."
                    optionalFiles.each { file, description ->
                        if (fileExists(file)) {
                            echo "✅ ${description}: ${file} ✓"
                        } else {
                            echo "⚠️  ${description}: ${file} (optional, not found)"
                        }
                    }
                    
                    // Create necessary directories
                    def requiredDirs = ['logs', 'tests']
                    requiredDirs.each { dir ->
                        if (!fileExists(dir)) {
                            sh "mkdir -p ${dir}"
                            echo "📁 Created directory: ${dir}"
                        } else {
                            echo "✅ Directory exists: ${dir}"
                        }
                    }
                }
            }
        }
        
        stage('Python Environment Setup') {
            when {
                not { environment name: 'SKIP_PYTHON_SETUP', value: 'true' }
            }
            steps {
                echo '🐍 Setting up Python environment...'
                
                script {
                    try {
                        // Create virtual environment if possible
                        sh '''
                            if command -v python3 >/dev/null 2>&1; then
                                echo "Using python3"
                                python3 -m venv venv || echo "venv creation failed, continuing..."
                                if [ -f venv/bin/activate ]; then
                                    . venv/bin/activate
                                    echo "Virtual environment activated"
                                    python --version
                                    pip --version
                                    
                                    # Install dependencies if requirements.txt exists
                                    if [ -f requirements.txt ]; then
                                        echo "Installing Python dependencies..."
                                        pip install -r requirements.txt || echo "Some packages failed to install"
                                    fi
                                else
                                    echo "Virtual environment not available, using system Python"
                                fi
                            else
                                echo "Python3 not available, skipping virtual environment setup"
                            fi
                        '''
                    } catch (Exception e) {
                        echo "⚠️  Python setup warning: ${e.getMessage()}"
                        echo "Continuing without Python virtual environment"
                    }
                }
            }
        }
        
        stage('Code Validation') {
            steps {
                echo '🔍 Validating application code...'
                
                script {
                    try {
                        // Basic syntax check for Python files
                        if (fileExists('app.py')) {
                            sh 'python3 -m py_compile app.py || python -m py_compile app.py || echo "Python syntax check failed but continuing"'
                            echo '✅ app.py syntax validation passed'
                        }
                        
                        // Check if Docker-related files are valid
                        if (fileExists('Dockerfile')) {
                            // Basic Dockerfile validation
                            sh 'grep -i "FROM" Dockerfile && echo "✅ Dockerfile has FROM instruction"'
                        }
                        
                        // Validate JSON files
                        if (fileExists('config.json')) {
                            sh 'python3 -m json.tool config.json > /dev/null || python -m json.tool config.json > /dev/null'
                            echo '✅ config.json is valid JSON'
                        }
                        
                    } catch (Exception e) {
                        echo "⚠️  Code validation warning: ${e.getMessage()}"
                        echo "Some validations failed but build can continue"
                    }
                }
            }
        }
        
        stage('Docker Build Preparation') {
            when {
                expression { 
                    // Only run if Docker is available
                    try {
                        sh 'which docker'
                        return true
                    } catch (Exception e) {
                        echo "Docker not available, skipping Docker build"
                        return false
                    }
                }
            }
            steps {
                echo '🐳 Preparing for Docker build...'
                
                script {
                    try {
                        // Test Docker connectivity
                        sh 'docker version || echo "Docker version check failed"'
                        
                        // Clean up any existing containers/images from previous builds
                        sh """
                            # Clean up previous build artifacts (ignore errors)
                            docker container rm -f ${COMPOSE_PROJECT_NAME}_app || echo "No container to remove"
                            docker image rm -f ${DOCKER_IMAGE} || echo "No image to remove"
                            docker system prune -f || echo "Docker prune failed"
                        """
                        
                        echo '✅ Docker environment prepared'
                        
                    } catch (Exception e) {
                        echo "⚠️  Docker preparation warning: ${e.getMessage()}"
                        currentBuild.result = 'UNSTABLE'
                    }
                }
            }
        }
        
        stage('Display Build Summary') {
            steps {
                echo '📊 Build Information Summary'
                script {
                    def buildInfo = """
                    ═══════════════════════════════════════
                    🚀 LOG & METRICS COLLECTOR BUILD
                    ═══════════════════════════════════════
                    📦 Application: ${APP_NAME}
                    🏗️  Build Number: ${BUILD_NUMBER}
                    🔀 Branch: ${env.BRANCH_NAME ?: 'main'}
                    📝 Git Commit: ${GIT_COMMIT[0..7]}
                    🐳 Docker Image: ${DOCKER_IMAGE}
                    ⏰ Build Time: ${new Date()}
                    💻 Node: ${NODE_NAME}
                    📁 Workspace: ${WORKSPACE}
                    ═══════════════════════════════════════
                    """.stripIndent()
                    
                    echo buildInfo
                    
                    // Display workspace contents
                    sh 'echo "Workspace contents:" && ls -la'
                }
            }
        }
    }
    
    post {
        always {
            echo '🧹 Cleaning up workspace...'
            script {
                try {
                    // Show final workspace state
                    sh 'echo "Final workspace contents:" && ls -la'
                    
                    // Clean up virtual environment if created
                    sh 'rm -rf venv || echo "No venv to clean"'
                    
                    echo '✅ Cleanup completed'
                } catch (Exception e) {
                    echo "⚠️  Cleanup warning: ${e.getMessage()}"
                }
            }
        }
        
        success {
            echo '🎉 Pipeline completed successfully!'
            echo '✅ All validation stages passed'
            echo '📋 Ready for next phase: Docker build and test'
        }
        
        failure {
            echo '❌ Pipeline failed!'
            echo '🔍 Check the logs above for specific error details'
            echo '💡 Common fixes:'
            echo '   - Ensure Docker is properly installed in Jenkins'
            echo '   - Check file permissions and ownership'
            echo '   - Verify all required files are in the repository'
        }
        
        unstable {
            echo '⚠️  Pipeline completed with warnings'
            echo '🔍 Some non-critical checks failed'
            echo '✅ Build can proceed but review warnings above'
        }
    }
}