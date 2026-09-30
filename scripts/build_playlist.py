#!/usr/bin/env python3
"""Build a conservative family IPTV candidate playlist from public M3U sources."""

from __future__ import annotations

import csv
import re
import urllib.request
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TIMEOUT = 20
MAX_BACKUPS = 3
UA = "Mozilla/5.0 Sichuan-IPTV/1.0"


@dataclass
class Wanted:
    canonical: str
    group: str
    priority: int
    aliases: list[str]


def norm(value: str) -> str:
    value = value.upper().replace("＋", "+")
    return re.sub(r"[^0-9A-Z+\u4e00-\u9fff]", "", value)


def load_wanted() -> list[Wanted]:
    rows: list[Wanted] = []
    with (ROOT / "config/channels.csv").open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            rows.append(Wanted(
                row["canonical"].strip(),
                row["group"].strip(),
                int(row["priority"]),
                [x.strip() for x in row["aliases"].split("|") if x.strip()],
            ))
    return sorted(rows, key=lambda x: x.priority)


def parse_m3u(text: str):
    meta = ""
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("#EXTINF:"):
            meta = line
        elif line and not line.startswith("#") and meta:
            name = meta.rsplit(",", 1)[-1].strip()
            yield name, line
            meta = ""


def fetch(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return response.read().decode("utf-8-sig", errors="replace")


def match(name: str, wanted: list[Wanted]) -> Wanted | None:
    key = norm(name)
    # Longer aliases first, reducing CCTV-5 and CCTV-5+ ambiguity.
    candidates = sorted(
        ((norm(alias), item) for item in wanted for alias in item.aliases),
        key=lambda x: len(x[0]),
        reverse=True,
    )
    for alias, item in candidates:
        if key == alias or (len(alias) >= 4 and alias in key):
            return item
    return None


def main() -> None:
    wanted = load_wanted()
    source_urls = [
        line.strip()
        for line in (ROOT / "config/sources.txt").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    found: dict[str, list[str]] = {x.canonical: [] for x in wanted}
    source_log: list[str] = []

    for source in source_urls:
        try:
            text = fetch(source)
            count = 0
            for name, url in parse_m3u(text):
                item = match(name, wanted)
                if not item or url in found[item.canonical]:
                    continue
                if len(found[item.canonical]) < MAX_BACKUPS:
                    found[item.canonical].append(url)
                    count += 1
            source_log.append(f"- OK: {source}（新增 {count} 条候选）")
        except Exception as exc:
            source_log.append(f"- FAIL: {source}（{type(exc).__name__}: {exc}）")

    lines = ["#EXTM3U"]
    matched = 0
    for item in wanted:
        urls = found[item.canonical]
        for index, url in enumerate(urls):
            suffix = "" if index == 0 else f" · 备用{index}"
            lines.append(
                f'#EXTINF:-1 group-title="{item.group}",{item.canonical}{suffix}'
            )
            lines.append(url)
            matched += 1

    # Never replace the candidate file with an empty build.
    if matched:
        (ROOT / "output/parents-test.m3u").write_text(
            "\n".join(lines) + "\n", encoding="utf-8"
        )

    missing = [x.canonical for x in wanted if not found[x.canonical]]
    report = [
        "# 构建报告",
        "",
        f"- 目标频道：{len(wanted)}",
        f"- 输出候选线路：{matched}",
        f"- 缺失频道：{len(missing)}",
        "",
        "## 来源状态",
        "",
        *source_log,
        "",
        "## 尚未找到",
        "",
        *([f"- {name}" for name in missing] or ["- 无"]),
        "",
        "> 云端构建结果只是候选，不代表成都移动家庭网络一定可播。",
    ]
    (ROOT / "output/report.md").write_text(
        "\n".join(report) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
