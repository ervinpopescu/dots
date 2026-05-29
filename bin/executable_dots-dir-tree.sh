#!/bin/bash

cd "$1" || exit 1

sed -i.bak '/<!DOCTYPE html>/,/<\/html>/d' tree.md
tree -aH "" -I __pycache__ -I .git >>tree.md
sed -i.bak '/<head>/,/<\/head>/d' tree.md
sed -i.bak 's/h1/h2/g' tree.md
sed -i.bak '/<p class="VERSION">/,/<\/p>/d' tree.md
sed -i.bak '/\<hr\>/d' tree.md
sed -i.bak '/<br><br><p>/d' tree.md
sed -i.bak '/<a href=""><\/a><br>/d' tree.md
rm tree.md.bak