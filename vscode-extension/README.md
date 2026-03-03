# AI-TD Detector — VS Code Extension

ตรวจจับ **Technical Debt จาก AI-generated code** แบบ real-time ใน VS Code

## Features

- **Inline Annotations** — แสดง `⚡ CC=N` บน function ที่ซับซ้อน + `📝 missing docstring`
- **Status Bar Score** — `🟢 AI-TD: 0.1234` แสดง score ตลอดเวลา
- **Dashboard Panel** — gauge + dimension bars + function table
- **Auto-analyze on Save** — วิเคราะห์อัตโนมัติเมื่อกด Ctrl+S
- **Workspace Scan** — วิเคราะห์ทุกไฟล์ใน project พร้อมกัน

## Requirements

- Python 3.11+ พร้อม dependencies ของ AI-TD Engine:
  ```bash
  pip install -r engine/requirements.txt
  ```

## Setup

1. ติดตั้ง Extension
2. ตั้งค่า `aitd.enginePath` ให้ชี้ไปที่ project root (โฟลเดอร์ที่มี `engine/`)
3. ตั้งค่า `aitd.pythonPath` ถ้า Python ไม่ได้อยู่ใน PATH

## Build

```bash
cd vscode-extension
npm install
npm run compile   # dev build
npm run package   # production build → dist/extension.js
```

## Commands

| Command | Shortcut | Description |
|---------|----------|-------------|
| AI-TD: Analyze Current File | — | วิเคราะห์ไฟล์ที่เปิดอยู่ |
| AI-TD: Analyze Entire Workspace | — | วิเคราะห์ทั้ง project |
| AI-TD: Show Dashboard | — | เปิด panel แสดงผล |
| AI-TD: Clear Annotations | — | ล้าง annotation ทั้งหมด |

## AI-TD Score Formula

```
AI-TD Score = 0.30·C + 0.25·D + 0.20·Doc + 0.25·(1−E)
```

| Dimension | Weight | Meaning |
|-----------|--------|---------|
| C — Complexity | 30% | Cyclomatic + Cognitive complexity |
| D — Duplication | 25% | Code clone ratio |
| Doc — Documentation | 20% | Docstring coverage deficit |
| E — Error Handling | 25% | Try/except coverage (inverted) |

## Severity

| Score | Level | Color |
|-------|-------|-------|
| 0.00–0.30 | 🟢 LOW | Green |
| 0.30–0.60 | 🟡 MEDIUM | Orange |
| 0.60–1.00 | 🔴 HIGH | Red |

---

*Buriram Rajabhat University — กรวิชญ์ ชูเลื่อน (969112230013)*
