#!/usr/bin/env bash
# One command to bring the website up to date with the paper repository.
#
#   pipeline/sync.sh            rebuild site/data from the paper clone, test, commit, push (Pages deploys)
#   pipeline/sync.sh --no-push  rebuild and test only
#
# Refuses to publish when the paper's subsection list changed (ids would no longer mean the same
# thing for the stream): run pipeline/remap_stream.py with an old-to-new map first, then rerun.
set -euo pipefail
cd "$(dirname "$0")/.."

PAPER="${PAPER_REPO:-/Users/minglai.yang/Desktop/Scale_AI_LaTeX_Paper_Template/ai-control-tooling}"
export PAPER_TOOLING="$PAPER"
PUSH=1; [ "${1:-}" = "--no-push" ] && PUSH=0

titles() { python3 -c "import json,sys; t=json.load(open(sys.argv[1])); print('\n'.join(ss['title'] for s in t['sections'] for ss in s['subsections']))" "$1"; }
BEFORE="$(titles site/data/taxonomy.json)"

python3 pipeline/build_data.py
AFTER="$(titles site/data/taxonomy.json)"
if [ "$BEFORE" != "$AFTER" ]; then
  echo "subsection list changed; stream.json needs a remap before publishing:" >&2
  diff <(echo "$BEFORE") <(echo "$AFTER") >&2 || true
  git checkout -- site/data 2>/dev/null || true
  exit 2
fi

python3 pipeline/tests/test_build_data.py
python3 pipeline/tests/test_contrast.py
python3 -m unittest discover -s pipeline/tests -p 'test_collector.py'

if git diff --quiet -- site/data; then echo "site data unchanged"; exit 0; fi
git add site/data
PAPER_REV="$(git -C "$PAPER" rev-parse --short HEAD 2>/dev/null || echo unknown)"
git commit -q -m "data: rebuild from paper repo ${PAPER_REV}"
echo "committed rebuild from paper repo ${PAPER_REV}"
if [ "$PUSH" = 1 ]; then git push -q origin main && echo "pushed; GitHub Pages redeploys in about a minute"; fi
