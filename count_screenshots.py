import os, re
folder = "./public/output_pngs"
rx = re.compile(r'^(Foil|Set)_(\d+)_(elong|orig)_(glossy|matte)_(\d)_(after|before)\.png$')
required = [
    ('elong','glossy','3','after'), ('elong','glossy','3','before'),
    ('elong','matte','2','after'),  ('elong','matte','2','before'),
    ('orig','glossy','1','after'),  ('orig','glossy','1','before'),
    ('orig','matte','0','after'),   ('orig','matte','0','before'),
]
groups = {}
for f in os.listdir(folder):
    m = rx.match(f)
    if not m: 
        continue
    gkey = f"{m.group(1)}_{m.group(2)}"
    vkey = (m.group(3), m.group(4), m.group(5), m.group(6))
    groups.setdefault(gkey, set()).add(vkey)

missing_any = False
for gkey, have in sorted(groups.items()):
    missing = [v for v in required if v not in have]
    if missing:
        missing_any = True
        print(f"{gkey}: have {len(have)}/8, missing -> " + ", ".join(["_".join(v) for v in missing]))
if not missing_any:
    print("All groups complete (8/8).")