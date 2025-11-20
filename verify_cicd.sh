#!/bin/bash
# CI/CD Pipeline Verification Script

echo "========================================="
echo "CI/CD Pipeline Verification"
echo "========================================="
echo ""

# Check workflow files exist
echo "📁 Checking workflow files..."
if [ -f ".github/workflows/ci.yml" ]; then
    echo "  ✅ CI workflow exists"
else
    echo "  ❌ CI workflow missing"
fi

if [ -f ".github/workflows/publish.yml" ]; then
    echo "  ✅ Publish workflow exists"
else
    echo "  ❌ Publish workflow missing"
fi

if [ -f ".github/dependabot.yml" ]; then
    echo "  ✅ Dependabot config exists"
else
    echo "  ❌ Dependabot config missing"
fi

echo ""

# Validate YAML syntax
echo "🔍 Validating YAML syntax..."
uv run python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))" 2>/dev/null && echo "  ✅ CI workflow YAML is valid" || echo "  ❌ CI workflow YAML is invalid"
uv run python -c "import yaml; yaml.safe_load(open('.github/workflows/publish.yml'))" 2>/dev/null && echo "  ✅ Publish workflow YAML is valid" || echo "  ❌ Publish workflow YAML is invalid"
uv run python -c "import yaml; yaml.safe_load(open('.github/dependabot.yml'))" 2>/dev/null && echo "  ✅ Dependabot YAML is valid" || echo "  ❌ Dependabot YAML is invalid"

echo ""

# Check GitHub Actions versions
echo "📦 Checking GitHub Actions versions..."
grep -h "uses:" .github/workflows/*.yml | sort -u | sed 's/^[[:space:]]*/  /'

echo ""

# Check Python version
echo "🐍 Checking Python version..."
grep "uv python install" .github/workflows/*.yml | head -1 | sed 's/^[[:space:]]*/  /'

echo ""

# Check uv setup version
echo "🔧 Checking uv setup version..."
grep "astral-sh/setup-uv" .github/workflows/*.yml | head -1 | sed 's/^[[:space:]]*/  /'

echo ""

echo "========================================="
echo "Verification Complete"
echo "========================================="
