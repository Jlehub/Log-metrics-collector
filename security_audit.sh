#!/bin/bash

echo "🔍 DevOps Security Audit - Pre-Git Push Check"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check for sensitive files
check_sensitive_files() {
    echo -e "\n${YELLOW}1. Checking for sensitive files...${NC}"
    
    sensitive_patterns=(
        "*.key"
        "*.pem"
        "*.p12"
        "*.pfx"
        "*password*"
        "*secret*"
        "*.env"
        "*credentials*"
        "*token*"
        "config.xml"
        "hudson.model.*"
        "identity.key*"
        "secret.key*"
    )
    
    found_sensitive=false
    for pattern in "${sensitive_patterns[@]}"; do
        files=$(find . -name "$pattern" -not -path "./jenkins_data/*" -not -path "./.git/*" 2>/dev/null)
        if [ ! -z "$files" ]; then
            echo -e "${RED}⚠️  Found potentially sensitive files:${NC}"
            echo "$files"
            found_sensitive=true
        fi
    done
    
    if [ "$found_sensitive" = false ]; then
        echo -e "${GREEN}✅ No sensitive files found in working directory${NC}"
    fi
}

# Function to check git status
check_git_status() {
    echo -e "\n${YELLOW}2. Git repository status...${NC}"
    git status --porcelain
}

# Function to check what would be committed
check_staged_files() {
    echo -e "\n${YELLOW}3. Files that would be committed...${NC}"
    git diff --cached --name-only
    if [ $? -eq 0 ] && [ -z "$(git diff --cached --name-only)" ]; then
        echo "No files currently staged for commit"
    fi
}

# Function to check for hardcoded secrets in code
check_hardcoded_secrets() {
    echo -e "\n${YELLOW}4. Scanning for hardcoded secrets in Python files...${NC}"
    
    secret_patterns=(
        "password\s*=\s*['\"][^'\"]*['\"]"
        "token\s*=\s*['\"][^'\"]*['\"]"
        "api_key\s*=\s*['\"][^'\"]*['\"]"
        "secret\s*=\s*['\"][^'\"]*['\"]"
        "key\s*=\s*['\"][a-zA-Z0-9+/]{20,}['\"]"
    )
    
    found_secrets=false
    for pattern in "${secret_patterns[@]}"; do
        matches=$(grep -r -n -i -E "$pattern" --include="*.py" . 2>/dev/null | grep -v ".git")
        if [ ! -z "$matches" ]; then
            echo -e "${RED}⚠️  Potential hardcoded secret found:${NC}"
            echo "$matches"
            found_secrets=true
        fi
    done
    
    if [ "$found_secrets" = false ]; then
        echo -e "${GREEN}✅ No hardcoded secrets found in Python files${NC}"
    fi
}

# Function to verify .gitignore coverage
check_gitignore_coverage() {
    echo -e "\n${YELLOW}5. Verifying .gitignore coverage...${NC}"
    
    if [ -f ".gitignore" ]; then
        echo -e "${GREEN}✅ .gitignore file exists${NC}"
        
        # Check if Jenkins data is ignored
        if grep -q "jenkins_data" .gitignore || grep -q "jenkins/" .gitignore; then
            echo -e "${GREEN}✅ Jenkins data directories are ignored${NC}"
        else
            echo -e "${RED}⚠️  Consider adding Jenkins data directories to .gitignore${NC}"
        fi
        
        # Check if sensitive patterns are covered
        critical_ignores=("*.key" "*.env" "secrets/" "credentials/")
        for ignore in "${critical_ignores[@]}"; do
            if grep -q "$ignore" .gitignore; then
                echo -e "${GREEN}✅ $ignore is ignored${NC}"
            else
                echo -e "${YELLOW}ℹ️  Consider adding $ignore to .gitignore${NC}"
            fi
        done
    else
        echo -e "${RED}❌ No .gitignore file found${NC}"
    fi
}

# Function to show files that would be pushed
show_push_preview() {
    echo -e "\n${YELLOW}6. Files that would be pushed to remote...${NC}"
    git diff --name-only HEAD origin/main 2>/dev/null || git diff --name-only HEAD 2>/dev/null || echo "Unable to compare with remote (this might be the first push)"
}

# Main execution
main() {
    echo "Starting security audit..."
    
    check_sensitive_files
    check_git_status
    check_staged_files
    check_hardcoded_secrets
    check_gitignore_coverage
    show_push_preview
    
    echo -e "\n${YELLOW}=============================================="
    echo "🛡️  Security Audit Complete"
    echo "=============================================="
    echo ""
    echo "Before pushing to GitHub:"
    echo "1. Review any warnings above"
    echo "2. Ensure no sensitive data is included"
    echo "3. Double-check your .gitignore file"
    echo "4. Consider using 'git add -A' and 'git commit' before push"
    echo -e "5. Push safely with: ${GREEN}git push origin main${NC}"
}

# Run the audit
main