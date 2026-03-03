/**
 * PanelProvider — Webview panel แสดง AI-TD Dashboard
 *
 * File view:      score gauge + dimension bars + function table + doc gaps
 * Workspace view: summary stats + file ranking table
 */

import * as vscode from 'vscode';
import { FileResult, WorkspaceResult } from './engineRunner';

export class PanelProvider {
    private panel: vscode.WebviewPanel | undefined;

    constructor(private context: vscode.ExtensionContext) {}

    show() {
        if (this.panel) { this.panel.reveal(vscode.ViewColumn.Beside); return; }
        this.panel = vscode.window.createWebviewPanel(
            'aitdPanel', 'AI-TD Dashboard',
            vscode.ViewColumn.Beside,
            { enableScripts: true, retainContextWhenHidden: true },
        );
        this.panel.webview.html = this.emptyHtml('เปิดไฟล์ Python / JavaScript / TypeScript แล้วบันทึกเพื่อเริ่มวิเคราะห์');
        this.panel.onDidDispose(() => { this.panel = undefined; });
    }

    updateFile(r: FileResult)           { if (this.panel) this.panel.webview.html = this.fileHtml(r); }
    updateWorkspace(r: WorkspaceResult) { if (this.panel) this.panel.webview.html = this.workspaceHtml(r); }

    // ── Private helpers ───────────────────────────────────────────────

    private sevColor(s: string) {
        return s === 'high' ? '#E53E3E' : s === 'medium' ? '#ED8936' : '#38A169';
    }

    private bar(score: number, label: string, weight: number): string {
        const pct = Math.round(score * 100);
        const c   = score > 0.6 ? '#E53E3E' : score > 0.3 ? '#ED8936' : '#38A169';
        return `
        <div style="margin:8px 0">
          <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:3px">
            <span><b>${label}</b> <span style="color:#718096;font-size:10px">w=${weight}</span></span>
            <span style="color:${c};font-weight:bold">${score.toFixed(4)}</span>
          </div>
          <div style="background:#4A5568;border-radius:3px;height:7px">
            <div style="width:${pct}%;background:${c};border-radius:3px;height:7px"></div>
          </div>
        </div>`;
    }

    private css = `
      body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
           background:#1A202C;color:#E2E8F0;padding:14px;font-size:13px;margin:0}
      h3{font-size:11px;color:#A0AEC0;margin:14px 0 6px;text-transform:uppercase;letter-spacing:.06em}
      .card{background:#2D3748;border-radius:8px;padding:12px;margin-bottom:10px}
      table{width:100%;border-collapse:collapse}
      th{text-align:left;padding:4px 8px;color:#718096;font-size:11px;border-bottom:1px solid #4A5568}
      td{padding:4px 8px;font-size:12px}
      tr:hover td{background:#4A5568}
      .badge{display:inline-block;padding:1px 7px;border-radius:3px;font-size:10px;font-weight:bold}
      .mono{font-family:'Courier New',monospace;font-size:11px}
    `;

    private emptyHtml(msg: string) {
        return `<!DOCTYPE html><html><head><meta charset="UTF-8"><style>${this.css}</style></head>
        <body><p style="color:#718096;margin-top:20px">${msg}</p></body></html>`;
    }

    private fileHtml(r: FileResult): string {
        const sc  = r.total_score;
        const col = this.sevColor(r.severity);
        const pct = Math.round(sc * 100);
        const d   = r.dimensions;

        const fnRows = [...r.annotations.functions]
            .sort((a, b) => b.cyclomatic - a.cyclomatic)
            .slice(0, 20)
            .map(fn => {
                const c = this.sevColor(fn.severity);
                return `<tr>
                  <td class="mono">${fn.name}</td>
                  <td style="text-align:center;color:${c};font-weight:bold">${fn.cyclomatic}</td>
                  <td style="text-align:center">${fn.cognitive}</td>
                  <td style="text-align:center">
                    <span class="badge" style="background:${c}22;color:${c}">${fn.severity.toUpperCase()}</span>
                  </td>
                  <td style="text-align:center;color:#718096">L${fn.start_line + 1}</td>
                </tr>`;
            }).join('');

        const gapRows = r.annotations.doc_gaps.slice(0, 15).map(g =>
            `<tr>
              <td class="mono">${g.name}</td>
              <td style="color:#718096">${g.type}</td>
              <td style="color:#718096">L${g.start_line + 1}</td>
            </tr>`
        ).join('');

        return `<!DOCTYPE html><html><head><meta charset="UTF-8"><style>${this.css}</style></head><body>

<!-- Score gauge card -->
<div class="card" style="text-align:center">
  <div style="font-size:11px;color:#718096;margin-bottom:6px">
    ${r.language.toUpperCase()} · ${r.file_path.split('/').pop()}
    ${r.parse_errors ? '<span style="color:#E53E3E;margin-left:6px">⚠ parse errors</span>' : ''}
  </div>
  <svg width="90" height="90" viewBox="0 0 36 36" style="display:block;margin:0 auto 6px">
    <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
          fill="none" stroke="#4A5568" stroke-width="3"/>
    <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
          fill="none" stroke="${col}" stroke-width="3"
          stroke-dasharray="${pct}, 100" stroke-linecap="round"/>
    <text x="18" y="21" font-size="7.5" text-anchor="middle" fill="${col}" font-weight="bold">${sc.toFixed(3)}</text>
  </svg>
  <span class="badge" style="background:${col}22;color:${col}">${r.severity.toUpperCase()}</span>
  <div style="font-size:10px;color:#718096;margin-top:6px">
    AI-TD = 0.30·C + 0.25·D + 0.20·Doc + 0.25·(1−E)
  </div>
</div>

<!-- Dimension bars -->
<div class="card">
  <h3>Dimensions</h3>
  ${this.bar(d.complexity.score,             'Complexity (C)',      0.30)}
  ${this.bar(d.duplication.score,            'Duplication (D)',     0.25)}
  ${this.bar(d.documentation.score,          'Documentation (Doc)', 0.20)}
  ${this.bar(1 - d.error_handling.score,     'Error Handling (1−E)', 0.25)}
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:3px;margin-top:10px;font-size:11px;color:#A0AEC0">
    <span>Avg CC: <b style="color:#E2E8F0">${d.complexity.avg_cyclomatic}</b></span>
    <span>Max CC: <b style="color:#E2E8F0">${d.complexity.max_cyclomatic}</b></span>
    <span>Dup ratio: <b style="color:#E2E8F0">${d.duplication.ratio_pct.toFixed(1)}%</b></span>
    <span>Doc cover: <b style="color:#E2E8F0">${(d.documentation.coverage_ratio * 100).toFixed(0)}%</b></span>
    <span>Bare except: <b style="color:#E2E8F0">${d.error_handling.bare_except_count}</b></span>
    <span>EH cover: <b style="color:#E2E8F0">${(d.error_handling.coverage_ratio * 100).toFixed(0)}%</b></span>
  </div>
</div>

${fnRows ? `
<div class="card">
  <h3>Functions — sorted by Cyclomatic Complexity</h3>
  <table>
    <thead><tr><th>Function</th><th>CC</th><th>Cog</th><th>Severity</th><th>Line</th></tr></thead>
    <tbody>${fnRows}</tbody>
  </table>
  ${r.annotations.functions.length > 20
    ? `<p style="color:#718096;font-size:11px;margin-top:6px">… และอีก ${r.annotations.functions.length - 20} functions</p>`
    : ''}
</div>` : ''}

${gapRows ? `
<div class="card">
  <h3>Missing Documentation (${r.annotations.doc_gaps.length})</h3>
  <table>
    <thead><tr><th>Name</th><th>Type</th><th>Line</th></tr></thead>
    <tbody>${gapRows}</tbody>
  </table>
</div>` : '<div class="card"><h3>Documentation</h3><p style="color:#38A169">✅ ทุก function/class มี docstring</p></div>'}

</body></html>`;
    }

    private workspaceHtml(r: WorkspaceResult): string {
        const avgCol = this.sevColor(r.average_score > 0.6 ? 'high' : r.average_score > 0.3 ? 'medium' : 'low');
        const d = r.severity_distribution;

        const fileRows = [...r.files]
            .sort((a, b) => b.total_score - a.total_score)
            .slice(0, 40)
            .map(f => {
                const c = this.sevColor(f.severity);
                const name = f.file_path.split('/').slice(-2).join('/');
                return `<tr>
                  <td class="mono" style="max-width:220px;overflow:hidden;text-overflow:ellipsis">${name}</td>
                  <td style="text-align:center;color:${c};font-weight:bold">${f.total_score.toFixed(4)}</td>
                  <td style="text-align:center">
                    <span class="badge" style="background:${c}22;color:${c}">${f.severity.toUpperCase()}</span>
                  </td>
                  <td style="text-align:center;color:#718096">${f.language}</td>
                </tr>`;
            }).join('');

        return `<!DOCTYPE html><html><head><meta charset="UTF-8"><style>${this.css}</style></head><body>

<div class="card">
  <h3>Workspace Summary</h3>
  <div style="display:flex;gap:6px;flex-wrap:wrap;text-align:center">
    <div style="flex:1;background:#4A5568;border-radius:6px;padding:8px">
      <div style="font-size:18px;font-weight:bold">${r.files_analyzed}</div>
      <div style="font-size:10px;color:#A0AEC0">FILES</div>
    </div>
    <div style="flex:1;background:#4A5568;border-radius:6px;padding:8px">
      <div style="font-size:18px;font-weight:bold;color:${avgCol}">${r.average_score.toFixed(4)}</div>
      <div style="font-size:10px;color:#A0AEC0">AVG SCORE</div>
    </div>
    <div style="flex:1;background:#4A5568;border-radius:6px;padding:8px">
      <div style="font-size:18px;font-weight:bold;color:#38A169">${d.low}</div>
      <div style="font-size:10px;color:#A0AEC0">LOW</div>
    </div>
    <div style="flex:1;background:#4A5568;border-radius:6px;padding:8px">
      <div style="font-size:18px;font-weight:bold;color:#ED8936">${d.medium}</div>
      <div style="font-size:10px;color:#A0AEC0">MEDIUM</div>
    </div>
    <div style="flex:1;background:#4A5568;border-radius:6px;padding:8px">
      <div style="font-size:18px;font-weight:bold;color:#E53E3E">${d.high}</div>
      <div style="font-size:10px;color:#A0AEC0">HIGH</div>
    </div>
  </div>
  <div style="margin-top:8px;font-size:11px;color:#718096">
    Max: ${r.max_score.toFixed(4)} · Min: ${r.min_score.toFixed(4)} · Skipped: ${r.files_skipped}
  </div>
</div>

<div class="card">
  <h3>Files — Ranked by AI-TD Score (top 40)</h3>
  <table>
    <thead><tr><th>File</th><th>Score</th><th>Severity</th><th>Lang</th></tr></thead>
    <tbody>${fileRows}</tbody>
  </table>
  ${r.files.length > 40
    ? `<p style="color:#718096;font-size:11px;margin-top:8px">… และอีก ${r.files.length - 40} ไฟล์</p>`
    : ''}
</div>

</body></html>`;
    }
}
