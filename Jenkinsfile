pipeline {
    agent any
    
    environment {
        // Define environment variables
        APP_NAME = 'log-metrics-collector'
        DOCKER_IMAGE = "${APP_NAME}:${BUILD_NUMBER}"
        DOCKER_REGISTRY = 'your-dockerhub-username'  // Change this to your Docker Hub username
        PYTHON_VERSION = '3.10'
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo '🔄 Checking out code from repository...'
                checkout scm
                
                // Display build information
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
                        // Check Docker
                        sh 'docker --version'
                        sh 'docker info'
                        echo '✅ Docker is available'
                        
                        // Check Python
                        sh 'python3 --version || python --version'
                        echo '✅ Python is available'
                        
                        // Check required files
                        sh 'ls -la'
                        
                        if (fileExists('app.py')) {
                            echo '✅ app.py found'
                        } else {
                            error '❌ app.py not found'
                        }
                        
                        if (fileExists('Dockerfile')) {
                            echo '✅ Dockerfile found'
                        } else {
                            error '❌ Dockerfile not found'
                        }
                        
                        if (fileExists('requirements.txt')) {
                            echo '✅ requirements.txt found'
                        } else {
                            error '❌ requirements.txt not found'
                        }
                        
                    } catch (Exception e) {
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
                        'app.py',
                        'requirements.txt',
                        'Dockerfile',
                        'config.json'
                    ]
                    
                    def requiredDirs = [
                        'logs',
                        'tests'
                    ]
                    
                    // Check required files
                    requiredFiles.each { file ->
                        if (fileExists(file)) {
                            echo "✅ Required file found: ${file}"
                        } else {
                            echo "⚠️  Missing file: ${file}"
                        }
                    }
                    
                    // Check required directories
                    requiredDirs.each { dir ->
                        if (fileExists(dir)) {
                            echo "✅ Required directory found: ${dir}"
                        } else {
                            echo "⚠️  Missing directory: ${dir}"
                            // Create missing directories
                            sh "mkdir -p ${dir}"
                            echo "📁 Created directory: ${dir}"
                        }
                    }
                }
            }
        }
        
        stage('Display Build Info') {
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
                    ═══════════════════════════════════════
                    """.stripIndent()
                    
                    echo buildInfo
                }
            }
        }
    }
    
    post {
        always {
            echo '🧹 Cleaning up workspace...'
            // Clean workspace but keep important files
            script {
                try {
                    // List what we're about to clean
                    sh 'echo "Current workspace contents:"'
                    sh 'ls -la'
                    
                    echo '✅ Pipeline completed'
                } catch (Exception e) {
                    echo "⚠️  Cleanup warning: ${e.getMessage()}"
                }
            }
        }
        
        success {
            echo '🎉 Pipeline completed successfully!'
        }
        
        failure {
            echo '❌ Pipeline failed!'
        }
        
        unstable {
            echo '⚠️  Pipeline completed with warnings'
        }
    }
}