#!/bin/bash

# this script is used in .github/workflows/build.yml
# it assumes the main branch is in folder "main"
# the gh-pages branch is in folder "gh-pages"
rm -rf ./gh-pages/dev/*
cp -rf ./main/doc/build/html/* ./gh-pages/dev/
touch ./gh-pages/dev/.nojekyll

cd ./gh-pages/

git config --global user.name "michaelchin"
git config --global user.email "michael.chin@sydney.edu.au"

git add -A
git commit --message "GitHub Action to update github pages"
git push origin