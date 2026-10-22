#!/usr/bin/env bash
set -eo pipefail
REPO=$(cd "$(dirname "$0")/.." && pwd)
fetch_dependency() {
  local url=$1 revision=$2 target=$3
  if [ ! -e "$target" ]; then
    git clone "$url" "$target"
    git -C "$target" checkout --detach "$revision"
  else
    if [ ! -d "$target/.git" ] || [ "$(git -C "$target" rev-parse HEAD)" != "$revision" ]; then
      echo "Dependency already exists with a different version: $target"; exit 2
    fi
    if [ -n "$(git -C "$target" status --porcelain)" ]; then
      echo "Dependency has local changes; preserve and review them: $target"; exit 2
    fi
  fi
}
fetch_dependency https://github.com/huokumo/experiment5.git \
  807de9e2454d0c6bd7ab3067e6743acf429e19f9 "$REPO/src/experiment5"
fetch_dependency https://github.com/huokumo/experiment7.git \
  81833b8fbf3e633f7e4fafc677fd121ecc01c3ba "$REPO/src/experiment7"
echo 'Experiment5 models and Experiment7 simulator are ready. Next: bash tools/build.sh'
