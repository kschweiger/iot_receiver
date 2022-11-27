#!/bin/zsh

echo "Bumping Version"
new_version=$(poetry version --dry-run --short $1)
bump_msg=$(poetry version $1)

echo "Updating changelog"
conventional-changelog -p conventionalcommits -i CHANGELOG.md -s
if [[ $? != 0 ]]
then
  echo "Generating changelog failed. Exiting..."
  exit 1
fi

git add CHANGELOG.md pyproject.toml
git commit -n -m "build: ${bump_msg}"
git tag ${new_version}

echo "Pushing"
git push
echo "Pushing tag"
git push --tag