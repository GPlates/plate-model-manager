#!/bin/bash

# this script is used in .github/workflows/build.yml
# it assumes the main branch is in folder "main"
# the gh-pages branch is in folder "gh-pages"
rm -rf ./gh-pages/dev/*
cp -rf ./main/doc/build/html/* ./gh-pages/dev/
touch ./gh-pages/dev/.nojekyll

cd ./gh-pages/

# remove accidental self-referential "stable" links inside version folders
shopt -s nullglob
for maybe_stable_link in ./v*/stable; do
    if [ -L "$maybe_stable_link" ]; then
        rm "$maybe_stable_link"
    fi
done
shopt -u nullglob

git config --global user.name "michaelchin"
git config --global user.email "michael.chin@sydney.edu.au"

git add -A
git commit --message "GitHub Action to update github pages"
git push origin