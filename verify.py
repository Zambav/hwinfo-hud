from reader import read_hwinfo

try:
    data = read_hwinfo()
    readings = data["readings"]
    print(f"OK, {len(readings)} readings found")
    for r in readings[:10]:
        print(f"  {r['sensor']} / {r['label']}: {r['value']} {r['unit']}")
except Exception as e:
    print(f"FAILED: {e}")
