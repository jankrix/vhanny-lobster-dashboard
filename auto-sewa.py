#!/usr/bin/env python3
"""
Auto-sewa amortization script.
Runs on the 1st of each month (Jul 2026 - Jan 2027).
Adds the monthly sewa expense transaction if not already present.
"""
import json, subprocess, re, sys
from datetime import datetime

WORKDIR = "/Users/eliemarga/Documents/Erick-claude-workspace/Business Consultation/VhannyLobster"
JSON_PATH = f"{WORKDIR}/lobster-finance-data.json"
HTML_PATH = f"{WORKDIR}/index.html"

now = datetime.now()
year, month = now.year, now.month

# Only run for the 7-month period
valid_months = [(2026, 7), (2026, 8), (2026, 9), (2026, 10), (2026, 11), (2026, 12), (2027, 1)]
if (year, month) not in valid_months:
    print(f"No action needed — outside sewa period ({year}-{month})")
    sys.exit(0)

month_names = {7:"Juli",8:"Agustus",9:"September",10:"Oktober",11:"November",12:"Desember",1:"Januari"}
month_name = month_names[month]

# Map to month index 1-7
month_idx = valid_months.index((year, month)) + 1  # 1-indexed
monthly = 10714285
is_last = month_idx == 7
amount = monthly if not is_last else 75000000 - (monthly * 6)

# Date for transaction (last day of month)
last_day_map = {7:31,8:31,9:30,10:31,11:30,12:31,1:31}
tx_date = f"{year}-{month:02d}-{last_day_map[month]}"

# Read JSON
with open(JSON_PATH) as f:
    data = json.load(f)

# Check if this month already has a sewa expense
existing_ids = [t['id'] for t in data['transactions']]
already_exists = any(
    t['account_code'] == '6.10' and t['date'].startswith(f"{year}-{month:02d}")
    for t in data['transactions']
)

if already_exists:
    print(f"Sewa expense for {year}-{month:02d} already exists — skipping")
    sys.exit(0)

# Add transaction
next_id_num = max(int(t['id'].split('-')[1]) for t in data['transactions']) + 1
new_id = f"TRX-{next_id_num:03d}"

new_tx = {
    "id": new_id,
    "date": tx_date,
    "account_code": "6.10",
    "description": f"Beban Sewa {month_name} {year} ({month_idx}/7)",
    "amount": amount,
    "type": "expense",
    "payment_status": "lunas",
    "notes": f"Penyusutan sewa dibayar dimuka — bulan {month_idx}/7",
    "source_file": "Auto-amortisasi"
}
data['transactions'].append(new_tx)

# Write JSON
with open(JSON_PATH, 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print(f"✅ Added {new_id}: Sewa {month_name} {year} — Rp{amount:,}")

# Update HTML — find the transaction data section and insert the new transaction
# We do this by reading, adding the line before the closing of the transactions array
with open(HTML_PATH) as f:
    html = f.read()

# Find the last transaction entry and add ours after it
# Pattern: find the last } in the transactions array before the closing ]
import re
# Find the TRX section end
pattern = r'(\{id:"TRX-\d+".*?\}),\s*\n\s*\]'
def add_transaction(match):
    last_tx = match.group(1)
    # Format the new transaction as a JS object
    notes_escaped = new_tx['notes'].replace("'", "\\'")
    desc_escaped = new_tx['description']
    new_entry = f'    {last_tx},\n    {{id:"{new_id}",date:"{tx_date}",account_code:"6.10",description:"{desc_escaped}",amount:{amount},type:"expense",payment_status:"lunas",notes:"{notes_escaped}"}}'
    return new_entry + ',\n  ]'

# Try simpler approach: find the last TRX line before the closing ]
lines = html.split('\n')
for i in range(len(lines)-1, 0, -1):
    if 'TRX-' in lines[i] and lines[i].strip().endswith('},'):
        # Insert new line after this one
        desc = new_tx['description']
        new_line = f'    {{id:"{new_id}",date:"{tx_date}",account_code:"6.10",description:"{desc}",amount:{amount},type:"expense",payment_status:"lunas",notes:"Penyusutan sewa dibayar dimuka — bulan {month_idx}/7"}},'
        lines.insert(i+1, new_line)
        html = '\n'.join(lines)
        print(f"✅ Updated index.html with new transaction")
        break

with open(HTML_PATH, 'w') as f:
    f.write(html)

# Git add, commit, push
subprocess.run(["git", "add", "-A"], cwd=WORKDIR, capture_output=True)
subprocess.run(["git", "commit", "-m", f"Auto: Beban Sewa {month_name} {year} ({month_idx}/7)"],
               cwd=WORKDIR, capture_output=True)
result = subprocess.run(["git", "push"], cwd=WORKDIR, capture_output=True, text=True)
print(f"✅ Pushed to GitHub: {result.stdout.strip()[-80:] if result.stdout else 'done'}")

print(f"\n📊 Sisa Sewa Dibayar Dimuka setelah ini: Rp {75000000 - (month_idx * monthly):,}")
