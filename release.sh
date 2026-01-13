#!/bin/bash
set -e

# Release script for tmui
# Usage: ./release.sh [patch|minor|major]

BUMP_TYPE="${1:-patch}"

# Extract current version from tmui.py
CURRENT_VERSION=$(grep -oP '__version__ = "\K[^"]+' tmui.py)
echo "Current version: $CURRENT_VERSION"

# Parse version components
IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT_VERSION"

# Bump version
case "$BUMP_TYPE" in
    major)
        MAJOR=$((MAJOR + 1))
        MINOR=0
        PATCH=0
        ;;
    minor)
        MINOR=$((MINOR + 1))
        PATCH=0
        ;;
    patch)
        PATCH=$((PATCH + 1))
        ;;
    *)
        echo "Usage: $0 [patch|minor|major]"
        exit 1
        ;;
esac

NEW_VERSION="$MAJOR.$MINOR.$PATCH"
echo "New version: $NEW_VERSION"

# Update version in tmui.py
sed -i "s/__version__ = \"$CURRENT_VERSION\"/__version__ = \"$NEW_VERSION\"/" tmui.py

# Update version in pyproject.toml if exists
if [ -f pyproject.toml ]; then
    sed -i "s/version = \"$CURRENT_VERSION\"/version = \"$NEW_VERSION\"/" pyproject.toml
fi

# Git operations
git add tmui.py pyproject.toml
git commit -m "Bump version to $NEW_VERSION"
git tag -a "v$NEW_VERSION" -m "Release v$NEW_VERSION"

echo ""
echo "Version bumped to $NEW_VERSION"
echo "To publish:"
echo "  git push origin main --tags"
echo "  python3 -m build"
echo "  python3 -m twine upload dist/*"
