import json, urllib.request, sys

url = 'http://127.0.0.1:8080/api/readings'
with urllib.request.urlopen(url) as resp:
    data = json.load(resp)

readings = data.get('readings', [])
print(f'Total readings: {len(readings)}')
print()

# All temperature readings
temps = [r for r in readings if r['type'] == 'temp']
print(f'Temperature readings ({len(temps)}):')
for r in temps:
    print(f"  [{r['sensor'][:55]}] {r['label']}: {r['value']} {r['unit']}")

print()

# GPU specific
gpu = [r for r in readings if 'gpu' in r['sensor'].lower()]
print(f'GPU readings ({len(gpu)}):')
for r in gpu:
    print(f"  {r['type']:8} | {r['sensor'][:55]} | {r['label']}: {r['value']} {r['unit']}")