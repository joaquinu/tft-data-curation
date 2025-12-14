# scripts/calc_timestamps.py
import sys
from datetime import datetime, timedelta, timezone

if len(sys.argv) != 2:
    print("ERROR: expected YYYYMMDD", file=sys.stderr)
    sys.exit(1)

date_str = sys.argv[1]

d = datetime.strptime(date_str, "%Y%m%d").replace(tzinfo=timezone.utc)
start = int(d.timestamp())
end = int((d + timedelta(days=1) - timedelta(seconds=1)).timestamp())

print(start, end)
