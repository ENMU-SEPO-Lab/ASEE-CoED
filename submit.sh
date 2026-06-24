#!/bin/bash
set -u  # error on unset variables

SUBMISSION_DIR="upload_here"          # match your actual submission dir
SUBMISSIONS_SOURCE="test_submissions"      # where the 40 student folders live

for submission_file in "$SUBMISSIONS_SOURCE"/*.java; do
    file_id=$(basename "$submission_file")   # store original file name for id in github job

    # Clear previous submission from the trigger dir
    git rm -r --quiet "$SUBMISSION_DIR"/* 2>/dev/null || true
    mkdir -p "$SUBMISSION_DIR" 
    # Copy the current submission to the submission dir
    cp "$submission_file" "$SUBMISSION_DIR"/CardDescription.java # file name needs to be modified for each assignment for the unit tests to work

    git add "$SUBMISSION_DIR"
    if git diff --staged --quiet; then
        echo "Skipping $file_id — nothing to commit."
        continue
    fi
    git commit -m "Submission: $file_id"
    git push

    echo "Pushed $file_id"
    sleep 10
done