"""Refresh the contribution SVG locally: python refresh-snake.py (standard library only)."""
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


class Calendar(HTMLParser):
    def __init__(self):
        super().__init__()
        self.days = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "td" and "data-date" in attrs and "data-level" in attrs:
            self.days.append((date.fromisoformat(attrs["data-date"]), int(attrs["data-level"])))


def main():
    request = Request("https://github.com/users/BaidaneAyoub/contributions",
                      headers={"User-Agent": "BaidaneAyoub-profile"})
    with urlopen(request, timeout=30) as response:
        calendar = Calendar()
        calendar.feed(response.read().decode("utf-8"))
    days = sorted(calendar.days)
    if not 350 <= len(days) <= 371 or len({day for day, _ in days}) != len(days):
        raise ValueError("Unexpected contribution calendar; existing SVG left untouched.")
    if any(level not in range(5) for _, level in days):
        raise ValueError("Invalid contribution levels; existing SVG left untouched.")
    start = days[0][0].toordinal() - (days[0][0].weekday() + 1) % 7
    columns = (days[-1][0].toordinal() - start) // 7 + 1
    points = [(24 + col * 16, 52 + row * 16)
              for col in range(columns)
              for row in (range(7) if col % 2 == 0 else range(6, -1, -1))]
    # Walk back outside the calendar before each new loop.
    route = points + [(points[-1][0], 176), (24, 176), points[0]]
    path = "M " + " L ".join(f"{x} {y}" for x, y in route)
    width = 48 + (columns - 1) * 16
    duration = 32
    snapshot = datetime.now(timezone.utc).date().isoformat()
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="216" viewBox="0 0 {width} 216" role="img" aria-labelledby="title desc">',
        '<title id="title">BaidaneAyoub contribution snake</title>',
        f'<desc id="desc">Actual GitHub contribution levels from {days[0][0]} to {days[-1][0]}. Snapshot {snapshot}. Purple snake sweeps the calendar.</desc>',
        '<style>.cell{fill:#202735;stroke:#303849}.l1{fill:#544080}.l2{fill:#8056b8}.l3{fill:#ad7df0}.l4{fill:#d8b4fe}.snake{fill:#f0abfc}.label{fill:#cbd5e1;font:13px ui-monospace,monospace}@media(prefers-reduced-motion:reduce){.snake{display:none}.cell{opacity:1!important;animation:none!important}}',
    ]
    for day, level in days:
        offset = day.toordinal() - start
        col, row = divmod(offset, 7)
        index = col * 7 + (row if col % 2 == 0 else 6 - row)
        passed = (index + 1) / len(route)
        svg.append(f'@keyframes c{index}{{0%,{max(0, passed * 100 - 0.01):.3f}%{{opacity:1}}{passed * 100:.3f}%,97%{{opacity:.16}}100%{{opacity:1}}}}')
    svg += ['</style>', f'<rect width="{width}" height="216" rx="16" fill="#0d1117"/>',
            '<text x="20" y="25" class="label">CONTRIBUTION SNAKE</text>',
            f'<text x="20" y="201" class="label">GitHub activity · {snapshot} snapshot</text>']
    for day, level in days:
        offset = day.toordinal() - start
        col, row = divmod(offset, 7)
        index = col * 7 + (row if col % 2 == 0 else 6 - row)
        x, y = 24 + col * 16, 52 + row * 16
        svg.append(f'<rect class="cell l{level}" x="{x-5}" y="{y-5}" width="10" height="10" rx="2" style="animation:c{index} {duration}s linear infinite"><title>{day}: contribution level {level}/4</title></rect>')
    times = ";".join(f"{i/(len(route)-1):.6f}" for i in range(len(route)))
    coords = ";".join(f"{x},{y}" for x, y in route)
    # SMIL works inside SVG images on GitHub and needs no scripts or external assets.
    for segment in range(6, -1, -1):
        svg.append(f'<rect class="snake" x="-5" y="-5" width="10" height="10" rx="3" opacity="{1-segment*.09:.2f}"><animateMotion values="{coords}" keyTimes="{times}" calcMode="linear" dur="{duration}s" begin="{segment*.075}s" repeatCount="indefinite"/></rect>')
    svg.append('</svg>')
    content = "\n".join(svg)
    ET.fromstring(content)
    target = Path(__file__).parent / "github-snake.svg"
    target.parent.mkdir(exist_ok=True)
    target.write_text(content, encoding="utf-8")
    print(f"Generated {target.name}: {len(days)} real contribution days, {columns} weeks.")


if __name__ == "__main__":
    main()
