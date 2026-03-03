<div align="center">

# 🔍 AI-TD Detector

### ระบบตรวจจับและวัดระดับหนี้ทางเทคนิคที่เกิดจากการสร้างโค้ดด้วย AI อัตโนมัติ

**Automated Detection of AI-Induced Technical Debt in Software Projects Using Static Analysis**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Tree-sitter](https://img.shields.io/badge/Tree--sitter-0.21-green)](https://tree-sitter.github.io)
[![Tests](https://img.shields.io/badge/Tests-36%20passed-brightgreen)](engine/tests/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [AI-TD Score Formula](#-ai-td-score-formula)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [Usage](#-usage)
- [Demo Results](#-demo-results)
- [Tech Stack](#-tech-stack)
- [Research Background](#-research-background)
- [Roadmap](#-roadmap)
- [License](#-license)

---

## 🌟 Overview

ในยุคที่เครื่องมือ AI อย่าง GitHub Copilot, ChatGPT และ Claude กลายเป็นส่วนหนึ่งของการพัฒนาซอฟต์แวร์ โค้ดมากถึง **40%** ในบางทีมมาจาก AI โดยตรง แต่ความเร็วที่เพิ่มขึ้นมาพร้อมกับ **หนี้ทางเทคนิค (Technical Debt)** ที่ซ่อนอยู่

**AI-TD Detector** เป็นระบบตรวจจับและวัดระดับหนี้ทางเทคนิคที่เกิดจาก AI-generated code โดยใช้ **Static Code Analysis** ผ่าน **Tree-sitter AST Parser** วิเคราะห์โค้ดใน 4 มิติ แล้วคำนวณเป็น **AI-TD Score** เพียงค่าเดียว

### ปัญหาที่แก้

| ปัญหา | สิ่งที่ AI-TD Detector ทำ |
|--------|---------------------------|
| เครื่องมืออย่าง SonarQube ไม่แยกแยะโค้ด AI vs Human | วิเคราะห์เฉพาะ patterns ที่พบบ่อยใน LLM output |
| ไม่มี composite metric สำหรับ AI-specific debt | เสนอ **AI-TD Score** 4 มิติ พร้อม weight justification |
| ทีมพัฒนาไม่รู้ว่าสะสม AI debt อยู่ระดับใด | แจ้งเตือน LOW / MEDIUM / HIGH ทันที |

---

## ✨ Key Features

- 🌳 **Tree-sitter AST Parsing** — วิเคราะห์โค้ดในระดับ Abstract Syntax Tree รองรับ Python, JavaScript, TypeScript
- 📊 **4-Dimensional Analysis** — Complexity, Duplication, Documentation, Error Handling
- 🎯 **AI-TD Score** — Composite metric 0.0–1.0 พร้อม severity classification
- 🔬 **Bayesian Weight Framing** — น้ำหนักอ้างอิงจากงานวิจัยที่ผ่าน peer review
- 🧪 **36 Unit Tests** — ครอบคลุมทุก analyzer + scoring engine
- 🐙 **GitHub API Integration** — ดึง commit history + ตรวจจับ AI commit markers อัตโนมัติ
- 📁 **CLI Interface** — ใช้งานง่ายผ่าน command line

---

## 📐 AI-TD Score Formula

```
AI-TD Score = 0.30·C + 0.25·D + 0.20·Doc + 0.25·(1−E)
```

| Dimension | Weight | Metric | Reference |
|-----------|--------|--------|-----------|
| **Complexity (C)** | 30% | Cyclomatic + Cognitive Complexity | McCabe (1976), Herbold et al. (2022) |
| **Duplication (D)** | 25% | Code clone ratio (hash-based) | Roy & Cordy (2007) |
| **Documentation (Doc)** | 20% | Docstring/comment coverage | Aghajani et al. (2020) |
| **Error Handling (E)** | 25% | Try/except coverage + quality | Perry et al. (2023) |

> **Note:** `(1−E)` เพราะ E ยิ่งสูง = handling ยิ่งดี = debt ยิ่งน้อย

### Severity Thresholds

| Score Range | Severity | Meaning |
|-------------|----------|---------|
| 0.00 – 0.30 | 🟢 **LOW** | Technical debt อยู่ในระดับยอมรับได้ |
| 0.30 – 0.60 | 🟡 **MEDIUM** | ควรทบทวนและปรับปรุงโค้ด |
| 0.60 – 1.00 | 🔴 **HIGH** | มี technical debt สูง ต้องแก้ไขเร่งด่วน |

---

## 📁 Project Structure

```
ai-td-detector/
├── README.md
├── demo_poc.py                         # PoC demo: AI vs Human comparison
├── engine/
│   ├── main.py                         # CLI entry point
│   ├── requirements.txt
│   ├── parsers/
│   │   └── tree_sitter_parser.py       # Tree-sitter AST parser (Python/JS/TS)
│   ├── analyzers/
│   │   ├── complexity.py               # Dimension C — Cyclomatic + Cognitive
│   │   ├── duplication.py              # Dimension D — Hash-based clone detection
│   │   ├── documentation.py            # Dimension Doc — Docstring/comment coverage
│   │   └── error_handling.py           # Dimension E — Try/except coverage
│   ├── scoring/
│   │   └── ai_td_score.py             # AI-TD Score composite calculator
│   ├── github/
│   │   └── commit_analyzer.py          # GitHub API + AI commit marker detection
│   └── tests/                          # 36 unit tests
│       ├── test_complexity.py
│       ├── test_duplication.py
│       ├── test_documentation.py
│       ├── test_error_handling.py
│       └── test_scoring.py
├── samples/
│   ├── ai_generated_example.py         # Simulated AI-generated code
│   └── human_written_example.py        # Well-written human code
├── vscode-extension/                    # ✅ VS Code Extension (Ready to install)
│   ├── package.json                     # Extension manifest + commands
│   ├── src/                            # TypeScript source files
│   │   ├── extension.ts                 # Main entry point
│   │   ├── engineRunner.ts              # Python bridge
│   │   ├── decorationManager.ts         # Inline annotations
│   │   ├── panelProvider.ts             # Dashboard webview
│   │   └── statusBarItem.ts             # Status bar integration
│   ├── python-bridge/bridge.py          # Python subprocess bridge
│   ├── ai-td-detector-1.0.0.vsix        # Installable package (34KB)
│   └── README.md                        # Extension usage guide
├── web-dashboard/                       # ✅ Web Dashboard (Flask + Plotly)
│   ├── app.py                          # Flask backend with API endpoints
│   ├── templates/index.html             # Interactive frontend
│   └── requirements.txt                 # Python dependencies
├── scripts/                            # Data collection & analysis scripts
│   ├── data_collector.py                # GitHub API data collection
│   ├── human_collector.py               # Human repo collector (control group)
│   ├── real_repo_analyzer.py            # Real-time repo analysis
│   └── statistical_analysis.py          # Dataset analysis
└── test_extension.*                    # Test files for extension (py/js/ts)
└── data/                               # Dataset & analysis results
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- pip

### Installation

```bash
git clone https://github.com/taeezx44/ai-td-detector.git
cd ai-td-detector
pip install -r engine/requirements.txt
```

### 🎯 VS Code Extension (Recommended)

**Install Extension:**
```bash
# Download and install the .vsix package
code --install-extension vscode-extension/ai-td-detector-1.0.0.vsix
```

**Configure Extension:**
1. Open VS Code → Settings → Extensions → AI-TD Detector
2. Set `aitd.enginePath` to project root (folder containing `engine/`)
3. Set `aitd.pythonPath` to your Python interpreter

**Use Extension:**
- **Analyze Current File**: `Ctrl+Shift+P → "AI-TD: Analyze Current File"`
- **Analyze Workspace**: `Ctrl+Shift+P → "AI-TD: Analyze Entire Workspace"`
- **Show Dashboard**: `Ctrl+Shift+P → "AI-TD: Show Dashboard"`
- **Auto-analyze**: Enable `aitd.autoAnalyzeOnSave` for real-time analysis

### 🌐 Web Dashboard

**Start Dashboard:**
```bash
cd web-dashboard
pip install -r requirements.txt
python app.py
```

**Access:** http://localhost:5000

**Features:**
- Real-time repository analysis
- Interactive charts (Plotly)
- Repository filtering and search
- Export results to CSV

### 🧪 Command Line Interface

**Analyze a Single File:**

```bash
python engine/main.py --file samples/ai_generated_example.py
```

**Analyze Directory:**

```bash
python engine/main.py --directory path/to/your/project
```

**Analyze GitHub Repository:**

```bash
python scripts/real_repo_analyzer.py --repo https://github.com/user/repo
```

### Run Tests

```bash
python -m pytest engine/tests/ -v
```

Expected:
```
36 passed in 0.07s
```

---

## 💻 Usage

### Analyze a Single File

```bash
python engine/main.py --file samples/ai_generated_example.py
```

Output:
```
═══ AI-TD Score Report ═══
Language:    python
Total Score: 0.6714 [HIGH]

  Complexity (C):      0.0000  × 0.30 = 0.0000
  Duplication (D):     1.0000  × 0.25 = 0.2500
  Documentation (Doc): 0.8571  × 0.20 = 0.1714
  Error Handling (E):  0.0000  × 0.25 = 0.2500  (inverted: 1−E)
```

### Analyze a Directory

```bash
python engine/main.py --dir ./src --output results.json
```

### Custom Weights

```bash
python engine/main.py --file code.py --weights '{"complexity":0.4,"duplication":0.2,"documentation":0.2,"error_handling":0.2}'
```

### Full Comparison Demo

```bash
python demo_poc.py
```

---

## 📊 Demo Results

### VS Code Extension Demo

**Before Analysis:**
```
test_extension.py  (untagged)
```

**After AI-TD Analysis:**
```
test_extension.py  🟡 AI-TD: 0.45 [MEDIUM]
⚡ CC=12  (complex_function)
📝 missing docstring  (undocumented_function)
⚠️ no error handling  (processTypeA)
```

### Web Dashboard Demo

**Features:**
- 📈 **Real-time Gauge**: Overall AI-TD score visualization
- 📊 **Dimension Bars**: Complexity, Duplication, Documentation, Error Handling
- 🔍 **Repository Table**: Sortable, filterable results
- 📥 **Export**: Download analysis results as CSV

### Command Line Demo

| Dimension | AI Code | Human Code | Delta |
|-----------|---------|------------|-------|
| **AI-TD Score** | **0.6714 🔴 HIGH** | **0.1500 🟢 LOW** | **+0.5214** |
| Complexity (C) | 0.0000 | 0.0000 | +0.0000 |
| Duplication (D) | 1.0000 | 0.0000 | +1.0000 |
| Documentation (Doc) | 0.8571 | 0.0000 | +0.8571 |
| Error Handling (E) | 0.0000 | 0.4000 | −0.4000 |

**Key Findings:**
- AI code มี AI-TD Score สูงกว่า Human code **4.5 เท่า**
- **Duplication** แตกต่างมากที่สุด — AI code มี copy-paste patterns ชัดเจน
- **Documentation** ขาดหายเกือบทั้งหมด (0/4 functions มี docstring)
- **Error Handling** ไม่มีเลยใน AI code

---

## 🛠 Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **AST Parser** | Tree-sitter 0.21 | Multi-language parsing |
| **Engine** | Python 3.11 | Core analysis + scoring |
| **Clone Detection** | MD5 hash-based | Sliding window duplication |
| **GitHub** | REST API v3 | Commit + AI marker detection |
| **Testing** | pytest 9.0 | 36 unit tests |
| **VS Code Extension** | TypeScript 5 *(planned)* | Real-time annotations |
| **Dashboard** | React 18 + PostgreSQL *(planned)* | Trend visualization |

---

## 🎓 Research Background

| | Detail |
|---|---|
| **Title (TH)** | ระบบตรวจจับและวัดระดับหนี้ทางเทคนิคที่เกิดจากการสร้างโค้ดด้วย AI อัตโนมัติ |
| **Title (EN)** | Automated Detection of AI-Induced Technical Debt in Software Projects Using Static Analysis |
| **Researcher** | Korawit Chuluen (กรวิชญ์ ชูเลื่อน) — 969112230013 |
| **University** | Buriram Rajabhat University |
| **Program** | Computer Science, B.Sc. |
| **Year** | 2569 (2026) |

### Research Questions

1. **RQ1:** Do AI-generated code segments exhibit statistically higher technical debt than human-written code? *(Wilcoxon Signed-Rank Test, α=0.05)*
2. **RQ2:** Which dimensions of technical debt are most strongly associated with AI-assisted code generation? *(Per-Dimension Analysis + Feature Importance)*
3. **RQ3:** *(Exploratory)* Is there a preliminary association between AI-TD Score and short-term maintainability indicators?

### Theoretical Foundation

- **Technical Debt Theory** — Cunningham (1992)
- **TD Taxonomy** — Alves et al. (2016)
- **ISO/IEC 25010** — Maintainability & Reliability framework
- **AI-TD Lifecycle Framework** — Proposed in this research (Inception → Accumulation → Interaction → Manifestation)

---

## 🗺 Roadmap

- [x] Detection Engine v1.0 (Tree-sitter + 4 Analyzers)
- [x] AI-TD Score composite metric
- [x] GitHub commit AI marker detection
- [x] CLI interface + Unit tests (36 tests)
- [x] VS Code Extension (real-time annotations)
- [x] Web Dashboard (longitudinal trends)
- [x] Dataset: 40+ GitHub repos (AI vs Human)
- [x] Statistical analysis (Wilcoxon + Effect Size)
- [x] Manual verification pipeline (Cohen's κ)
- [x] Complete research workflow automation
- [x] GitHub repository with full source code
- [ ] PCA weight recalibration from empirical data
- [ ] Paper submission (TSEC / ECTI-CON)
- [ ] Real-world dataset expansion (n=500+)

---

## 📊 Current Status & Achievements

### ✅ Completed (March 2026)
- **Detection Engine**: Tree-sitter AST parser + 4 technical debt analyzers
- **AI-TD Score**: Composite metric with Bayesian weight justification  
- **Unit Tests**: 36+ tests passing (core functionality verified)
- **CLI Tool**: Working command-line interface with AI-TD scoring
- **VS Code Extension**: Real-time annotations and analysis (1.0.0 released)
- **Web Dashboard**: Interactive Flask dashboard with Plotly visualizations
- **Dataset**: 40+ repositories (AI-assisted vs human-written control group)
- **Statistical Analysis**: Wilcoxon Signed-Rank Test + Effect size calculation
- **Demo Results**: AI code shows measurable technical debt differences
- **Research Workflow**: Complete 7-phase automation pipeline
- **GitHub Repository**: Full source code published and installable

### 📈 Key Findings
- **RQ1**: AI-generated code shows higher technical debt (AI: 0.51 vs Human: 0.35)
- **RQ2**: Documentation (0.40 vs 0.22) and Error Handling (0.46 vs 0.19) are most distinguishing
- **Statistical Significance**: P-value = 0.125 (trend toward significance, needs larger sample)
- **Effect Size**: Large effect observed but requires larger dataset for validation
- **Practical Results**: CLI engine produces AI-TD scores (0.6714 [HIGH] for AI-generated code)

### 🚀 Ready For
- **Academic Review**: Complete research artifacts with statistical analysis
- **Industrial Application**: Production-ready CLI tool and VS Code extension
- **Real-world Testing**: Web dashboard for repository analysis
- **Dataset Expansion**: Automated collection pipeline for larger studies
- **Conference Submission**: Research ready for TSEC/ECTI-CON submission

---

## 🤝 Contributing

Contributions are welcome! This is an open-source research project.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 📚 Key References

1. Cunningham, W. (1992). *The WyCash Portfolio Management System.* OOPSLA '92.
2. McCabe, T.J. (1976). *A complexity measure.* IEEE TSE, 2(4).
3. Perry, N. et al. (2023). *Do users write more insecure code with AI assistants?* ACM CCS.
4. Roy, C.K. & Cordy, J.R. (2007). *A survey on software clone detection research.*
5. Aghajani, E. et al. (2020). *Software documentation issues unveiled.* ICSE 2020.
6. Herbold, S. et al. (2022). *A large-scale comparison of Python code smells.* IEEE TSE.
7. GitClear (2025). *Code quality analysis of AI-assisted development.*

---

<div align="center">

**Built with ❤️ at Buriram Rajabhat University**

*Department of Computer Science • Faculty of Science and Technology*

</div>
