#!/bin/sh

#
# Usage
#  ./demo-drupal-evidence-git.sh
#
#
# NOTES: 
#  - Need to source env-aws credential.sh credential file.
#  - Users may need to adjust values for their workstation configuration.
#  - Run from `utils` directory
#


# Generate evidence
echo "Taking screenshots of Git repository..."
python3 demo-drupal-repo.py --size 1024x1200 --format pdf cm_git.pdf

# Upload the evidence
echo "Uploading to evidence server 'demo-drupal-01'"
cd ../../evidence-tools/
python3 eu.py --bucket demo-drupal-01 --file ../demo-drupal-on-docker/utils/cm_git.pdf --family CM

