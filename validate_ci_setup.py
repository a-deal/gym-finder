#!/usr/bin/env python3
"""
CI/CD Setup Validation Script
Validates that our CI/CD pipeline configuration is correct
"""

import os
import yaml
import json
from pathlib import Path


def validate_github_workflows():
    """Validate GitHub Actions workflow files"""
    print("🔍 Validating GitHub Actions workflows...")
    
    workflows_dir = Path(".github/workflows")
    if not workflows_dir.exists():
        print("❌ .github/workflows directory not found")
        return False
    
    # Check for CI workflow
    ci_file = workflows_dir / "ci.yml"
    if not ci_file.exists():
        print("❌ ci.yml workflow not found")
        return False
    
    try:
        with open(ci_file, 'r') as f:
            ci_config = yaml.safe_load(f)
        
        # Validate required sections (note: 'on' gets parsed as True in YAML)
        has_name = 'name' in ci_config
        has_on = 'on' in ci_config or True in ci_config  # GitHub Actions 'on' keyword
        has_jobs = 'jobs' in ci_config
        
        if not has_name:
            print("❌ Missing 'name' section in ci.yml")
            return False
        if not has_on:
            print("❌ Missing 'on' section in ci.yml") 
            return False
        if not has_jobs:
            print("❌ Missing 'jobs' section in ci.yml")
            return False
        
        # Validate job structure
        if 'test' not in ci_config['jobs']:
            print("❌ Missing 'test' job in ci.yml")
            return False
        
        print("✅ GitHub Actions workflow validation passed")
        return True
        
    except yaml.YAMLError as e:
        print(f"❌ Invalid YAML in ci.yml: {e}")
        return False


def validate_pre_commit_config():
    """Validate pre-commit configuration"""
    print("🔍 Validating pre-commit configuration...")
    
    precommit_file = Path(".pre-commit-config.yaml")
    if not precommit_file.exists():
        print("❌ .pre-commit-config.yaml not found")
        return False
    
    try:
        with open(precommit_file, 'r') as f:
            precommit_config = yaml.safe_load(f)
        
        # Validate structure
        if 'repos' not in precommit_config:
            print("❌ Missing 'repos' section in .pre-commit-config.yaml")
            return False
        
        # Check for essential hooks
        repos = precommit_config['repos']
        found_hooks = set()
        
        for repo in repos:
            if 'hooks' in repo:
                for hook in repo['hooks']:
                    found_hooks.add(hook['id'])
        
        essential_hooks = {'black', 'flake8', 'isort', 'bandit'}
        missing_hooks = essential_hooks - found_hooks
        
        if missing_hooks:
            print(f"⚠️  Missing essential hooks: {missing_hooks}")
        
        print("✅ Pre-commit configuration validation passed")
        return True
        
    except yaml.YAMLError as e:
        print(f"❌ Invalid YAML in .pre-commit-config.yaml: {e}")
        return False


def validate_issue_templates():
    """Validate GitHub issue templates"""
    print("🔍 Validating GitHub issue templates...")
    
    templates_dir = Path(".github/ISSUE_TEMPLATE")
    if not templates_dir.exists():
        print("❌ .github/ISSUE_TEMPLATE directory not found")
        return False
    
    required_templates = ['bug_report.md', 'feature_request.md']
    missing_templates = []
    
    for template in required_templates:
        template_file = templates_dir / template
        if not template_file.exists():
            missing_templates.append(template)
    
    if missing_templates:
        print(f"❌ Missing issue templates: {missing_templates}")
        return False
    
    print("✅ Issue templates validation passed")
    return True


def validate_pr_template():
    """Validate pull request template"""
    print("🔍 Validating pull request template...")
    
    pr_template = Path(".github/pull_request_template.md")
    if not pr_template.exists():
        print("❌ Pull request template not found")
        return False
    
    # Check minimum content
    with open(pr_template, 'r') as f:
        content = f.read()
    
    required_sections = [
        "## 📋 Description",
        "## 🎯 Type of Change", 
        "## 🧪 Testing Checklist",
        "## 🔍 Code Quality Checklist"
    ]
    
    missing_sections = []
    for section in required_sections:
        if section not in content:
            missing_sections.append(section)
    
    if missing_sections:
        print(f"❌ Missing PR template sections: {missing_sections}")
        return False
    
    print("✅ Pull request template validation passed")
    return True


def validate_documentation():
    """Validate required documentation files"""
    print("🔍 Validating documentation files...")
    
    required_docs = [
        'README.md',
        'ARCHITECTURE.md', 
        'TESTING.md',
        'CONTRIBUTING.md',
        'CI_CD_SETUP.md'
    ]
    
    missing_docs = []
    for doc in required_docs:
        if not Path(doc).exists():
            missing_docs.append(doc)
    
    if missing_docs:
        print(f"❌ Missing documentation files: {missing_docs}")
        return False
    
    # Validate README minimum content
    readme_path = Path('README.md')
    with open(readme_path, 'r') as f:
        readme_content = f.read()
    
    if len(readme_content) < 2000:  # Minimum characters
        print("⚠️  README.md seems too short (< 2000 characters)")
    
    print("✅ Documentation validation passed")
    return True


def validate_test_files():
    """Validate test file structure"""
    print("🔍 Validating test files...")
    
    required_test_files = [
        'tests/test_gym_finder.py',
        'tests/run_tests.py',
        'tests/run_gym_search.py',
        'tests/examples.py',
        'tests/benchmark.py'
    ]
    
    missing_files = []
    for file in required_test_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing test files: {missing_files}")
        return False
    
    print("✅ Test files validation passed")
    return True


def validate_requirements():
    """Validate requirements.txt structure"""
    print("🔍 Validating requirements.txt...")
    
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print("❌ requirements.txt not found")
        return False
    
    with open(requirements_file, 'r') as f:
        content = f.read()
    
    # Check for essential dependencies
    essential_deps = [
        'requests',
        'click', 
        'python-dotenv',
        'pytest',
        'black',
        'flake8'
    ]
    
    missing_deps = []
    for dep in essential_deps:
        if dep not in content:
            missing_deps.append(dep)
    
    if missing_deps:
        print(f"❌ Missing essential dependencies: {missing_deps}")
        return False
    
    print("✅ Requirements validation passed")
    return True


def validate_env_example():
    """Validate .env.example file"""
    print("🔍 Validating environment configuration...")
    
    env_example = Path(".env.example")
    if env_example.exists():
        print("✅ .env.example found")
    else:
        print("⚠️  .env.example not found (recommended)")
    
    # Check if .env exists
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env file exists")
        
        # Validate API keys are configured
        with open(env_file, 'r') as f:
            env_content = f.read()
        
        if 'YELP_API_KEY' in env_content and 'GOOGLE_PLACES_API_KEY' in env_content:
            print("✅ API keys configured in .env")
        else:
            print("⚠️  API keys may not be fully configured")
    else:
        print("⚠️  .env file not found (required for full functionality)")
    
    return True


def run_integration_smoke_test():
    """Run a quick integration test"""
    print("🔍 Running integration smoke test...")
    
    try:
        # Test imports with new structure
        import sys
        import os
        sys.path.insert(0, os.path.join(os.getcwd(), 'src'))
        
        from src.gym_finder import GymFinder
        from src.yelp_service import YelpService
        from src.google_places_service import GooglePlacesService
        
        # Test instance creation
        gym_finder = GymFinder()
        yelp_service = YelpService("test_key")
        google_service = GooglePlacesService("test_key")
        
        # Test basic functionality
        normalized = gym_finder.normalize_address("123 Test Street")
        phone = gym_finder.normalize_phone("(555) 123-4567")
        similarity = gym_finder.token_based_name_similarity("Gym A", "Gym B")
        
        print("✅ Integration smoke test passed")
        return True
        
    except Exception as e:
        print(f"❌ Integration smoke test failed: {e}")
        return False


def main():
    """Run all validation checks"""
    print("🚀 GymIntel CI/CD Setup Validation")
    print("=" * 50)
    
    validations = [
        ("GitHub Workflows", validate_github_workflows),
        ("Pre-commit Config", validate_pre_commit_config),
        ("Issue Templates", validate_issue_templates),
        ("PR Template", validate_pr_template),
        ("Documentation", validate_documentation),
        ("Test Files", validate_test_files),
        ("Requirements", validate_requirements),
        ("Environment Config", validate_env_example),
        ("Integration Test", run_integration_smoke_test)
    ]
    
    results = []
    
    for name, validator in validations:
        print(f"\n{'='*50}")
        print(f"🔍 {name}")
        print("-" * 50)
        
        try:
            result = validator()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Validation error: {e}")
            results.append((name, False))
    
    # Summary
    print(f"\n{'='*50}")
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{name:<20} {status}")
        if result:
            passed += 1
    
    print("-" * 50)
    print(f"Overall: {passed}/{total} validations passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL VALIDATIONS PASSED!")
        print("✅ CI/CD setup is ready for production")
        return 0
    else:
        print(f"\n⚠️  {total-passed} validation(s) failed")
        print("❌ Please fix the issues above before proceeding")
        return 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)