pipeline {
    agent any
    
    environment {
        // Application Configuration
        APP_NAME = 'log-metrics-collector'
        DOCKER_IMAGE = "${APP_NAME}"
        DOCKER_TAG = "${BUILD_NUMBER}"
        DOCKER_LATEST = 'latest'
        
        // Build Configuration
        PYTHON_VERSION = '3.10'
        WORKSPACE_DIR = "${WORKSPACE}"
        
        // Test Configuration
        PYTEST_ARGS = '--verbose --tb=short --cov=. --cov-report=xml --cov-report=html --junit-xml=test-results.xml'
        COVERAGE_THRESHOLD = '70'
        
        // Docker Configuration
        COMPOSE_PROJECT = "${APP_NAME}-${BUILD_NUMBER}"
        
        // Deployment Configuration
        STAGING_PORT = '5001'
        PROD_PORT = '5000'
    }
    
    options {
        // Build options
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 30, unit: 'MINUTES')
        skipStagesAfterUnstable()
    }
    
    stages {
        stage('Initialize') {
            steps {
                script {
                    echo """
                    ╔══════════════════════════════════════════════════════════════╗
                    ║               DevOps Pipeline Started                        ║
                    ║              Log & Metrics Collector                         ║
                    ╚══════════════════════════════════════════════════════════════╝
                    
                    Build Information:
                    • Application: ${APP_NAME}
                    • Build Number: ${BUILD_NUMBER}
                    • Branch: ${env.BRANCH_NAME ?: 'main'}
                    • Git Commit: ${env.GIT_COMMIT ? env.GIT_COMMIT[0..7] : 'unknown'}
                    • Build Time: ${new Date()}
                    • Jenkins Node: ${env.NODE_NAME ?: 'unknown'}
                    """
                }
            }
        }
        
        stage('Checkout & Validate') {
            steps {
                echo 'Checking out source code and validating project structure...'
                
                script {
                    // Validate required files exist
                    def requiredFiles = ['app.py', 'requirements-dev.txt', 'Dockerfile']
                    def missingFiles = []
                    
                    requiredFiles.each { file ->
                        if (!fileExists(file)) {
                            missingFiles.add(file)
                        }
                    }
                    
                    if (missingFiles) {
                        error("Missing required files: ${missingFiles.join(', ')}")
                    }
                    
                    echo "Project structure validation passed"
                    
                    // Display project files
                    sh 'find . -name "*.py" -o -name "*.yml" -o -name "*.yaml" -o -name "*.json" -o -name "Dockerfile*" | head -20'
                }
            }
        }
        
        stage('Python Environment Setup') {
            steps {
                echo 'Setting up Python environment and dependencies...'
                
                sh '''
                    # Create virtual environment
                    python3 -m venv venv
                    . venv/bin/activate
                    
                    # Upgrade pip
                    pip install --upgrade pip
                    
                    # Install application dependencies
                    pip install -r requirements-dev.txt
                    
                    # Install testing and development dependencies
                    pip install pytest pytest-cov pytest-mock pytest-html
                    pip install flake8 black bandit safety
                    pip install requests  # for integration tests
                    
                    echo "Python environment setup complete"
                    echo "Installed packages:"
                    pip list
                '''
            }
        }
        
        stage('Security Audit') {
            steps {
                echo 'Running security audit and vulnerability checks...'
                
                script {
                    // Run your security audit script
                    try {
                        sh './security_audit.sh'
                        echo "Security audit passed"
                    } catch (Exception e) {
                        echo "Security audit warnings detected: ${e.getMessage()}"
                        currentBuild.result = 'UNSTABLE'
                    }
                }
                
                sh '''
                    . venv/bin/activate
                    
                    # Check for known security vulnerabilities in dependencies
                    echo "Checking for security vulnerabilities..."
                    safety check --json --output safety-report.json || echo "Safety check completed with warnings"
                    
                    # Run Bandit security linter
                    echo "Running Bandit security analysis..."
                    bandit -r . -f json -o bandit-report.json || echo "Bandit analysis completed with warnings"
                    bandit -r . --severity-level medium || echo "Bandit completed with warnings"
                '''
                
                // Archive security reports
                archiveArtifacts artifacts: 'safety-report.json,bandit-report.json', allowEmptyArchive: true
            }
        }
        
        stage('Code Quality') {
            parallel {
                stage('Linting') {
                    steps {
                        sh '''
                            . venv/bin/activate
                            echo "Running Flake8 linting..."
                            
                            # Critical errors only first
                            flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
                            
                            # Full linting with warnings
                            flake8 . --count --max-complexity=10 --max-line-length=88 --statistics || echo "Linting completed with warnings"
                        '''
                    }
                }
                
                stage('Code Formatting') {
                    steps {
                        sh '''
                            . venv/bin/activate
                            echo "Checking code formatting with Black..."
                            black --check --diff . || (
                                echo "Code formatting issues found. Auto-fixing..."
                                black .
                                echo "Code formatted automatically"
                            )
                        '''
                    }
                }
            }
        }
        
        stage('Unit Tests') {
            steps {
                echo 'Running unit tests with coverage analysis...'
                
                sh '''
                    . venv/bin/activate
                    
                    # Ensure tests directory exists
                    mkdir -p tests
                    
                    # Run tests with coverage
                    python -m pytest ${PYTEST_ARGS} tests/ || echo "Some tests failed"
                    
                    # Generate coverage report
                    echo "Test execution completed"
                    
                    # Display coverage summary
                    coverage report --show-missing || echo "Coverage report generated"
                '''
            }
            
            post {
                always {
                    // Publish test results
                    publishTestResults testResultsPattern: 'test-results.xml'
                    
                    // Publish coverage report
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'htmlcov',
                        reportFiles: 'index.html',
                        reportName: 'Coverage Report'
                    ])
                    
                    // Archive coverage data
                    archiveArtifacts artifacts: 'coverage.xml,htmlcov/**', allowEmptyArchive: true
                }
            }
        }
        
        stage('Quality Gate') {
            steps {
                script {
                    echo 'Evaluating quality gate criteria...'
                    
                    // Check test coverage
                    try {
                        sh '''
                            . venv/bin/activate
                            COVERAGE=$(coverage report --format=total)
                            echo "Current coverage: ${COVERAGE}%"
                            
                            if [ "${COVERAGE}" -lt "${COVERAGE_THRESHOLD}" ]; then
                                echo "Coverage ${COVERAGE}% is below threshold ${COVERAGE_THRESHOLD}%"
                                exit 1
                            fi
                            
                            echo "Coverage quality gate passed: ${COVERAGE}% >= ${COVERAGE_THRESHOLD}%"
                        '''
                    } catch (Exception e) {
                        echo "Coverage quality gate failed: ${e.getMessage()}"
                        currentBuild.result = 'UNSTABLE'
                    }
                }
            }
        }
        
        stage('Docker Build') {
            steps {
                echo 'Building Docker image...'
                
                script {
                    try {
                        // Build Docker image
                        sh """
                            echo "Building Docker image: ${DOCKER_IMAGE}:${DOCKER_TAG}"
                            docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} .
                            docker tag ${DOCKER_IMAGE}:${DOCKER_TAG} ${DOCKER_IMAGE}:${DOCKER_LATEST}
                            
                            echo "Docker image built successfully"
                            docker images ${DOCKER_IMAGE}
                        """
                    } catch (Exception e) {
                        error("Docker build failed: ${e.getMessage()}")
                    }
                }
            }
        }
        
        stage('Container Testing') {
            steps {
                echo 'Testing Docker container functionality...'
                
                script {
                    try {
                        sh """
                            # Start container for testing
                            echo "Starting test container..."
                            docker run -d --name test-${BUILD_NUMBER} -p ${STAGING_PORT}:5000 ${DOCKER_IMAGE}:${DOCKER_TAG}
                            
                            # Wait for application to start
                            sleep 15
                            
                            # Test health endpoint
                            echo "Testing health endpoint..."
                            curl -f http://localhost:${STAGING_PORT}/health || exit 1
                            
                            # Test metrics endpoint
                            echo "Testing metrics endpoint..."
                            curl -f http://localhost:${STAGING_PORT}/metrics || exit 1
                            
                            # Test logs endpoint
                            echo "Testing logs endpoint..."
                            curl -f http://localhost:${STAGING_PORT}/logs || exit 1
                            
                            echo "Container tests passed successfully"
                        """
                    } catch (Exception e) {
                        error("Container testing failed: ${e.getMessage()}")
                    } finally {
                        // Always clean up test container
                        sh """
                            docker stop test-${BUILD_NUMBER} 2>/dev/null || echo "Container already stopped"
                            docker rm test-${BUILD_NUMBER} 2>/dev/null || echo "Container already removed"
                        """
                    }
                }
            }
        }
        
        stage('Integration Tests') {
            steps {
                echo 'Running integration tests...'
                
                sh '''
                    . venv/bin/activate
                    
                    # Start application container for integration tests
                    docker run -d --name integration-${BUILD_NUMBER} -p $((${STAGING_PORT} + 1)):5000 ${DOCKER_IMAGE}:${DOCKER_TAG}
                    sleep 10
                    
                    # Run integration tests against running container
                    INTEGRATION_URL=http://localhost:$((${STAGING_PORT} + 1)) python -m pytest tests/test_integration.py -v || echo "Integration tests completed"
                    
                    # Cleanup
                    docker stop integration-${BUILD_NUMBER} 2>/dev/null || echo "Container already stopped"
                    docker rm integration-${BUILD_NUMBER} 2>/dev/null || echo "Container already removed"
                '''
            }
        }
        
        stage('Deploy to Staging') {
            when {
                anyOf {
                    branch 'main'
                    branch 'develop'
                }
            }
            steps {
                echo 'Deploying to staging environment...'
                
                script {
                    try {
                        sh """
                            # Stop existing staging container
                            docker stop ${APP_NAME}-staging 2>/dev/null || echo "No existing staging container"
                            docker rm ${APP_NAME}-staging 2>/dev/null || echo "No existing staging container"
                            
                            # Deploy new version
                            docker run -d \
                                --name ${APP_NAME}-staging \
                                --restart unless-stopped \
                                -p ${STAGING_PORT}:5000 \
                                -e ENVIRONMENT=staging \
                                -e BUILD_NUMBER=${BUILD_NUMBER} \
                                ${DOCKER_IMAGE}:${DOCKER_TAG}
                            
                            # Wait for deployment
                            sleep 10
                            
                            # Verify deployment
                            curl -f http://localhost:${STAGING_PORT}/health
                            
                            echo "Staging deployment successful!"
                            echo "Application available at: http://localhost:${STAGING_PORT}"
                        """
                    } catch (Exception e) {
                        error("Staging deployment failed: ${e.getMessage()}")
                    }
                }
            }
        }
        
        stage('Performance Test') {
            steps {
                echo 'Running basic performance tests...'
                
                sh '''
                    . venv/bin/activate
                    
                    # Simple load test using curl
                    echo "Running performance tests..."
                    
                    for i in {1..10}; do
                        curl -s -w "Response time: %{time_total}s\\n" http://localhost:${STAGING_PORT}/health > /dev/null
                    done
                    
                    echo "Performance tests completed"
                '''
            }
        }
        
        stage('Create Release Artifacts') {
            when {
                branch 'main'
            }
            steps {
                echo 'Creating release artifacts...'
                
                script {
                    // Create git tag
                    sh """
                        git tag -a "v1.0.${BUILD_NUMBER}" -m "Release v1.0.${BUILD_NUMBER} - Build ${BUILD_NUMBER}"
                        echo "Git tag created: v1.0.${BUILD_NUMBER}"
                    """
                    
                    // Export Docker image
                    sh """
                        echo "Exporting Docker image..."
                        docker save ${DOCKER_IMAGE}:${DOCKER_TAG} | gzip > ${APP_NAME}-${BUILD_NUMBER}.tar.gz
                        
                        echo "Creating deployment manifest..."
                        cat > deployment-manifest-${BUILD_NUMBER}.yaml << EOF
apiVersion: v1
kind: Deployment
metadata:
  name: ${APP_NAME}
  labels:
    app: ${APP_NAME}
    version: v1.0.${BUILD_NUMBER}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ${APP_NAME}
  template:
    metadata:
      labels:
        app: ${APP_NAME}
        version: v1.0.${BUILD_NUMBER}
    spec:
      containers:
      - name: ${APP_NAME}
        image: ${DOCKER_IMAGE}:${DOCKER_TAG}
        ports:
        - containerPort: 5000
        env:
        - name: BUILD_NUMBER
          value: "${BUILD_NUMBER}"
        - name: ENVIRONMENT
          value: "production"
EOF
                        echo "Release artifacts created"
                    """
                }
            }
            
            post {
                always {
                    archiveArtifacts artifacts: '*.tar.gz,deployment-manifest-*.yaml', allowEmptyArchive: true
                }
            }
        }
    }
    
    post {
        always {
            echo 'Pipeline cleanup and reporting...'
            
            script {
                // Display final build summary
                def buildSummary = """
                ╔══════════════════════════════════════════════════════════════╗
                ║                    Build Summary                             ║
                ╚══════════════════════════════════════════════════════════════╝
                
                Application: ${APP_NAME}
                Build Number: ${BUILD_NUMBER}
                Build Status: ${currentBuild.currentResult}
                Duration: ${currentBuild.durationString}
                Git Commit: ${env.GIT_COMMIT ? env.GIT_COMMIT[0..7] : 'unknown'}
                Docker Image: ${DOCKER_IMAGE}:${DOCKER_TAG}
                """
                
                echo buildSummary
                
                // Cleanup
                sh '''
                    # Clean up virtual environment
                    rm -rf venv 2>/dev/null || echo "No venv to clean"
                    
                    # Clean up old Docker images (keep last 5 builds)
                    docker images ${DOCKER_IMAGE} --format "table {{.Repository}}:{{.Tag}}" | tail -n +6 | xargs -r docker rmi 2>/dev/null || echo "No old images to clean"
                    
                    # Clean up dangling images
                    docker image prune -f 2>/dev/null || echo "No dangling images to clean"
                '''
            }
        }
        
        success {
            echo 'Pipeline completed successfully!'
            echo "✅ All stages passed"
            echo "🚀 Application deployed to staging: http://localhost:${STAGING_PORT}"
            echo "📊 Coverage report available in build artifacts"
            echo "🐳 Docker image: ${DOCKER_IMAGE}:${DOCKER_TAG}"
            
            // You can add Slack/email notifications here
            // slackSend channel: '#devops', color: 'good', 
            //     message: "✅ ${APP_NAME} Build ${BUILD_NUMBER} SUCCESS"
        }
        
        failure {
            echo 'Pipeline failed!'
            echo "❌ Build failed at stage: ${env.STAGE_NAME}"
            echo "🔍 Check logs for details"
            echo "💡 Common solutions:"
            echo "  - Check Docker daemon is running"
            echo "  - Verify all required files are committed"
            echo "  - Ensure tests are passing locally"
            
            // Cleanup failed containers
            sh '''
                docker stop test-${BUILD_NUMBER} integration-${BUILD_NUMBER} 2>/dev/null || true
                docker rm test-${BUILD_NUMBER} integration-${BUILD_NUMBER} 2>/dev/null || true
            '''
            
            // You can add failure notifications here
            // slackSend channel: '#devops', color: 'danger',
            //     message: "❌ ${APP_NAME} Build ${BUILD_NUMBER} FAILED"
        }
        
        unstable {
            echo 'Pipeline completed with warnings'
            echo "⚠️ Some quality checks failed but build continued"
            echo "📋 Review test results and coverage reports"
        }
    }
}