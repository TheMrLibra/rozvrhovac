#!/bin/bash
# Script to help resolve merge conflict in docker-compose.prod.yml

echo "Resolving merge conflict in docker-compose.prod.yml..."

# Check if conflict markers exist
if grep -q "^<<<<<<< " docker-compose.prod.yml; then
    echo "Conflict markers found. Resolving..."
    
    # Use our version (the one we just created)
    echo "Using the new multi-tenant version..."
    
    # Backup the conflicted file
    cp docker-compose.prod.yml docker-compose.prod.yml.conflict-backup
    
    # Restore from stash to see both versions
    echo "To resolve manually:"
    echo "1. Review the conflict: git diff docker-compose.prod.yml"
    echo "2. Edit docker-compose.prod.yml and remove conflict markers"
    echo "3. Or use: git checkout --ours docker-compose.prod.yml (to use current branch version)"
    echo "4. Or use: git checkout --theirs docker-compose.prod.yml (to use stashed version)"
    echo ""
    echo "Recommended: Use --ours to keep the new multi-tenant version"
    
else
    echo "No conflict markers found. File may already be resolved."
fi

