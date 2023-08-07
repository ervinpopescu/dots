#!/bin/bash

cd "$1" || exit 1

sed -i '/<!DOCTYPE html>/,/<\/html>/d' tree.md
tree -aH "" -I __pycache__ -I .git >>tree.md
sed -i '/<head>/,/<\/head>/d' tree.md
sed -i 's/h1/h2/g' tree.md
sed -i '/<p class="VERSION">/,/<\/p>/d' tree.md
sed -i '/\<hr\>/d' tree.md
sed -i '/<br><br><p>/d' tree.md
sed -i '/<a href=""><\/a><br>/d' tree.md