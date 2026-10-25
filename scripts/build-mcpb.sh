#!/usr/bin/env bash
# Builds monzo.mcpb, a one-click Claude Desktop extension, into build/.
# Claude Desktop installs the Python dependencies itself with uv, from
# pyproject.toml and uv.lock, so none are bundled.
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
stage="$root/build/mcpb"
out="$root/build/monzo.mcpb"
mcpb="npx -y @anthropic-ai/mcpb@2.1.2"

cd "$root"
rm -rf "$stage" "$out"
mkdir -p "$stage"
cp -R src pyproject.toml uv.lock README.md LICENSE "$stage/"
find "$stage" -name __pycache__ -type d -prune -exec rm -rf {} +
rm -rf "$stage"/src/*.egg-info

# Keep the manifest version in step with pyproject.toml.
python3 - manifest.json "$stage/manifest.json" <<'PY'
import json, re, sys
src, dest = sys.argv[1:]
manifest = json.load(open(src))
manifest["version"] = re.search(r'^version = "([^"]+)"', open("pyproject.toml").read(), re.M)[1]
open(dest, "w").write(json.dumps(manifest, indent=2) + "\n")
PY

$mcpb validate "$stage/manifest.json"
$mcpb pack "$stage" "$out"
echo "Built $out"
