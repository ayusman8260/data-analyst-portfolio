#!/bin/bash
# Run with:  bash push_to_github.sh
# Before running: create an EMPTY repo on github.com (don't tick "Add README") and copy its URL.
set -e
cd "$(dirname "$0")"

echo "=== Push portfolio to GitHub ==="

# Git identity (only asked if not already set)
if [ -z "$(git config --global user.name)" ]; then
  read -p "Your name (for commits): " name
  git config --global user.name "$name"
fi
if [ -z "$(git config --global user.email)" ]; then
  read -p "Your email (same as GitHub): " email
  git config --global user.email "$email"
fi

# Create the local repo and commit
[ -d .git ] || git init -q
git add .

# Safety check: never upload raw data files or the database (results CSVs in outputs/ are fine)
bad=$(git diff --cached --name-only | grep -E '(/data/.*\.csv|\.db)$' || true)
if [ -n "$bad" ]; then
  echo "STOPPING: these data files would be uploaded:"; echo "$bad"
  echo "Remove them (or add them to .gitignore) and run again."
  exit 1
fi

git commit -q -m "Add data analyst portfolio: 5 projects" 2>/dev/null || echo "(nothing new to commit)"
git branch -M main

# Remote URL
read -p "Paste your GitHub repo URL (https://github.com/USERNAME/REPO.git): " url
git remote remove origin 2>/dev/null || true
git remote add origin "$url"

echo "Pushing... (a browser window may open to sign in to GitHub)"
git push -u origin main

echo
echo "Done! Open your repo on GitHub and check the Actions tab for the kpi-report run."
