#!/usr/bin/env python3
"""Generate schedule.html from talks.json."""

import json
import re
from html import escape

with open("talks.json") as f:
    talks = json.load(f)

# Tracks in display order (preserve original order)
track_order = [
    "Day 3 - Great Hall - Ground Floor",
    "Day 3 - Small Hall - Level 1",
    "Day 3 - Session Room 1 - Level -1",
    "Day 3 - Session Room 2 - Level -1",
]

TRACK_SHORT = {
    "Day 3 - Great Hall - Ground Floor":    "Great Hall",
    "Day 3 - Small Hall - Level 1":         "Small Hall",
    "Day 3 - Session Room 1 - Level -1":    "Session Room 1",
    "Day 3 - Session Room 2 - Level -1":    "Session Room 2",
}

def extract_time(time_str):
    """Return HH:MM from a time string like '17-04-2026 - 09:30'."""
    m = re.search(r'(\d{2}:\d{2})$', time_str.strip())
    return m.group(1) if m else time_str.strip()

# Build index: {track: {hhmm: talk}}
index = {}
for track in track_order:
    index[track] = {}
for talk in talks:
    track = talk["track"]
    if track in index:
        hhmm = extract_time(talk["time"])
        index[track][hhmm] = talk

# Collect all unique time slots, sorted
all_times = sorted(set(extract_time(t["time"]) for t in talks))

NON_TALK_TITLES = {"Registration and Breakfast", "Break", "Lunch", "Coffee Break",
                   "Start of Track 1", "Start of Track 2", "Start of Track 3", "Start of Track 4"}

def is_break(talk):
    return (not talk.get("speaker") and not talk.get("tags")) or talk["title"] in NON_TALK_TITLES

def render_cell(talk):
    if talk is None:
        return '<td class="empty"></td>'

    css_class = "break" if is_break(talk) else "talk"
    parts = [f'<td class="{css_class}">']

    parts.append(f'<div class="talk-title">{escape(talk["title"])}</div>')

    if talk.get("speaker"):
        parts.append(f'<div class="speaker-name">{escape(talk["speaker"])}</div>')
    if talk.get("speaker_role"):
        parts.append(f'<div class="speaker-role">{escape(talk["speaker_role"])}</div>')
    if talk.get("location"):
        parts.append(f'<div class="location">{escape(talk["location"])}</div>')
    if talk.get("tags"):
        tag_html = "".join(f'<span class="tag">{escape(tag)}</span>' for tag in talk["tags"])
        parts.append(f'<div class="tags">{tag_html}</div>')

    parts.append("</td>")
    return "".join(parts)

rows = []
for hhmm in all_times:
    cells = [f'<td class="time">{escape(hhmm)}</td>']
    for track in track_order:
        talk = index[track].get(hhmm)
        cells.append(render_cell(talk))
    rows.append(f"<tr data-time=\"{hhmm}\">{''.join(cells)}</tr>")

header_cells = ['<th class="time-header">Time</th>']
for track in track_order:
    header_cells.append(f'<th>{escape(TRACK_SHORT[track])}</th>')

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CityJS 2026 — Schedule</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; }}

    body {{
      font-family: system-ui, -apple-system, sans-serif;
      background: #f5f5f5;
      color: #1a1a1a;
      margin: 0;
      padding: 24px;
    }}

    h1 {{
      margin: 0 0 4px;
      font-size: 1.6rem;
    }}

    .subtitle {{
      color: #666;
      margin: 0 0 24px;
      font-size: 0.95rem;
    }}

    .table-wrapper {{
      overflow-x: auto;
    }}

    table {{
      border-collapse: collapse;
      width: 100%;
      min-width: 800px;
      background: #fff;
      border-radius: 8px;
      overflow: hidden;
      box-shadow: 0 1px 4px rgba(0,0,0,.1);
    }}

    thead th {{
      background: #1a1a1a;
      color: #fff;
      padding: 12px 14px;
      text-align: left;
      font-size: 0.85rem;
      font-weight: 600;
      letter-spacing: .03em;
      white-space: nowrap;
    }}

    thead th.time-header {{
      width: 60px;
    }}

    tbody tr:nth-child(even) td:not(.break):not(.talk) {{
      background: #fafafa;
    }}

    tbody tr + tr td {{
      border-top: 1px solid #eee;
    }}

    td {{
      padding: 10px 14px;
      vertical-align: top;
      font-size: 0.85rem;
    }}

    td.time {{
      color: #888;
      font-variant-numeric: tabular-nums;
      white-space: nowrap;
      font-size: 0.8rem;
      padding-top: 13px;
    }}

    td.empty {{
      background: #f9f9f9;
    }}

    td.break {{
      background: #f0f0f0;
      color: #888;
    }}

    td.break .talk-title {{
      font-weight: 500;
      color: #777;
    }}

    td.talk {{
      background: #fff;
    }}

    .talk-title {{
      font-weight: 600;
      margin-bottom: 4px;
      line-height: 1.35;
    }}

    .speaker-name {{
      font-weight: 500;
      color: #333;
      margin-top: 5px;
    }}

    .speaker-role {{
      color: #888;
      font-size: 0.78rem;
      margin-top: 2px;
    }}

    .location {{
      color: #aaa;
      font-size: 0.75rem;
      margin-top: 3px;
    }}

    .tags {{
      margin-top: 7px;
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
    }}

    .tag {{
      background: #eef2ff;
      color: #4f46e5;
      font-size: 0.7rem;
      padding: 2px 7px;
      border-radius: 99px;
      font-weight: 500;
    }}

    tr.current-row td {{
      background: #fffbe6 !important;
      border-top: 2px solid #f59e0b;
      border-bottom: 2px solid #f59e0b;
    }}

    tr.current-row td.time {{
      color: #d97706;
      font-weight: 700;
    }}
  </style>
</head>
<body>
  <h1>CityJS London 2026</h1>
  <p class="subtitle">Day 3 — 17 April 2026</p>
  <div class="table-wrapper">
    <table>
      <thead>
        <tr>{''.join(header_cells)}</tr>
      </thead>
      <tbody>
        {''.join(rows)}
      </tbody>
    </table>
  </div>
  <script>
    function highlightCurrentRow() {{
      const now = new Date();
      const hhmm = now.getHours().toString().padStart(2, '0') + ':' + now.getMinutes().toString().padStart(2, '0');
      const rows = Array.from(document.querySelectorAll('tbody tr[data-time]'));

      // Find the last row whose time is <= now
      let current = null;
      for (const row of rows) {{
        if (row.dataset.time <= hhmm) current = row;
        else break;
      }}

      rows.forEach(r => r.classList.remove('current-row'));
      if (current) {{
        current.classList.add('current-row');
        current.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
      }}
    }}

    highlightCurrentRow();
    setInterval(highlightCurrentRow, 60000);
  </script>
</body>
</html>
"""

with open("schedule.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"Written cityjs_schedule.html ({len(all_times)} time slots, {len(track_order)} tracks)")
