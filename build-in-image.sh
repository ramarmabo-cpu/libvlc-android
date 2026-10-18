#!/bin/bash
set -euo pipefail

LIBVLCJNI_REPO=https://code.videolan.org/videolan/libvlcjni.git
LIBVLCJNI_COMMIT=a498cf1fefd93c4a2ec7253ac33cd6dd5b344dde

here="$(cd "$(dirname "$0")" && pwd)"
stage=$1
dir="$(mkdir -p "$2" && cd "$2" && pwd)"

apply_once() {
  git apply --reverse --check "$1" 2>/dev/null || git apply "$1"
}

case $stage in
  sources)
    [[ -d $dir/libvlcjni ]] || git clone -q -b libvlcjni-3.x "$LIBVLCJNI_REPO" "$dir/libvlcjni"
    cd "$dir/libvlcjni"
    git checkout -q "$LIBVLCJNI_COMMIT"
    apply_once "$here/libvlcjni-lgpl.patch"
    [[ -d vlc ]] || GIT_AUTHOR_NAME=build GIT_AUTHOR_EMAIL=build@localhost \
      GIT_COMMITTER_NAME=build GIT_COMMITTER_EMAIL=build@localhost ./buildsystem/get-vlc.sh
    (cd vlc && apply_once "$here/vlc-codec-cuts.patch")
    ;;
  abi)
    cd "$dir/libvlcjni"
    ./buildsystem/compile-libvlc.sh -a "$3" --release --license a
    ;;
  aar)
    cd "$dir/libvlcjni"
    GRADLE_ABI=all gradle --no-daemon -q :libvlc:assembleRelease
    cp libvlc/build/outputs/aar/*-release.aar "$dir/libvlc-lgpl.aar"
    ;;
  *)
    echo "usage: $0 sources|abi|aar DIR [arm|arm64]" >&2
    exit 2
    ;;
esac
