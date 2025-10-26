import json
import sys

try:
    data = json.load(sys.stdin)
except json.JSONDecodeError as exc:
    sys.stderr.write(f"Failed to parse JSON input: {exc}\n")
    sys.exit(1)

pairs = data.get("top_correlations", [])
if not pairs:
    print("No correlation pairs found in input.")
    sys.exit(0)

pairs.sort(key=lambda x: x.get("correlation", 0.0), reverse=True)

print("Top 10 similar pairs:")
for entry in pairs[:10]:
    company1 = entry.get("company1", "?")
    company2 = entry.get("company2", "?")
    score = entry.get("correlation", 0.0)
    print(f"{company1} ↔ {company2}: {score:+.3f}")

print("\nLeast 10 similar pairs:")
least_sorted = sorted(pairs, key=lambda x: x.get("correlation", 0.0))
for entry in least_sorted[:10]:
    company1 = entry.get("company1", "?")
    company2 = entry.get("company2", "?")
    score = entry.get("correlation", 0.0)
    print(f"{company1} ↔ {company2}: {score:+.3f}")
