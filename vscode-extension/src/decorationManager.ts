/**
 * DecorationManager — แสดง inline annotation ใน VS Code editor
 *
 * 🔴 HIGH   — พื้นหลังแดง + ข้อความ end-of-line "⚡ CC=N"
 * 🟡 MEDIUM — พื้นหลังส้มอ่อน
 * 📝 DOC GAP — ตัวอักษรสีเทา "📝 missing docstring"
 */

import * as vscode from 'vscode';
import { FileResult } from './engineRunner';

// ── Decoration type definitions ───────────────────────────────────────

const highDeco = vscode.window.createTextEditorDecorationType({
    backgroundColor: 'rgba(229,62,62,0.10)',
    overviewRulerColor: '#e53e3e',
    overviewRulerLane: vscode.OverviewRulerLane.Right,
    after: { color: '#e53e3e', fontStyle: 'italic', margin: '0 0 0 20px' },
});

const mediumDeco = vscode.window.createTextEditorDecorationType({
    backgroundColor: 'rgba(237,137,54,0.08)',
    overviewRulerColor: '#ed8936',
    overviewRulerLane: vscode.OverviewRulerLane.Right,
    after: { color: '#ed8936', fontStyle: 'italic', margin: '0 0 0 20px' },
});

const docGapDeco = vscode.window.createTextEditorDecorationType({
    after: { color: '#718096', fontStyle: 'italic', margin: '0 0 0 16px' },
});

// ── Class ─────────────────────────────────────────────────────────────

export class DecorationManager {

    clearAll() {
        for (const editor of vscode.window.visibleTextEditors) {
            editor.setDecorations(highDeco, []);
            editor.setDecorations(mediumDeco, []);
            editor.setDecorations(docGapDeco, []);
        }
    }

    apply(doc: vscode.TextDocument, result: FileResult) {
        const editor = vscode.window.visibleTextEditors.find(e => e.document === doc);
        if (!editor) { return; }

        const cfg = vscode.workspace.getConfiguration('aitd');
        if (!cfg.get<boolean>('showInlineAnnotations')) { return; }

        const threshold = cfg.get<string>('severityThreshold') ?? 'medium';
        const highRanges: vscode.DecorationOptions[]  = [];
        const medRanges:  vscode.DecorationOptions[]  = [];
        const docRanges:  vscode.DecorationOptions[]  = [];

        // ── Function complexity ───────────────────────────────────────
        for (const fn of result.annotations.functions) {
            const line = Math.min(fn.start_line, doc.lineCount - 1);
            const range = doc.lineAt(line).range;
            const label = `  ⚡ CC=${fn.cyclomatic} Cog=${fn.cognitive}`;

            if (fn.severity === 'high') {
                highRanges.push({
                    range,
                    hoverMessage: new vscode.MarkdownString(
                        `**🔴 AI-TD: High Complexity** — \`${fn.name}\`\n\n` +
                        `| Metric | Value | Threshold |\n|---|---|---|\n` +
                        `| Cyclomatic | **${fn.cyclomatic}** | > 15 = high |\n` +
                        `| Cognitive  | **${fn.cognitive}**  | — |\n\n` +
                        `_แนะนำให้แยก function ย่อยหรือลด nesting_`
                    ),
                    renderOptions: { after: { contentText: label } },
                });
            } else if (fn.severity === 'medium' && threshold === 'low') {
                medRanges.push({
                    range,
                    hoverMessage: new vscode.MarkdownString(
                        `**🟡 AI-TD: Medium Complexity** — \`${fn.name}\`\n\n` +
                        `Cyclomatic: ${fn.cyclomatic}  Cognitive: ${fn.cognitive}`
                    ),
                    renderOptions: { after: { contentText: label } },
                });
            }
        }

        // ── Documentation gaps ────────────────────────────────────────
        for (const gap of result.annotations.doc_gaps) {
            const line = Math.min(gap.start_line, doc.lineCount - 1);
            docRanges.push({
                range: doc.lineAt(line).range,
                hoverMessage: new vscode.MarkdownString(
                    `**📝 AI-TD: Missing Docstring** — \`${gap.name}\` (${gap.type})\n\n` +
                    `เพิ่ม docstring เพื่อเพิ่ม maintainability`
                ),
                renderOptions: { after: { contentText: '  📝 missing docstring' } },
            });
        }

        editor.setDecorations(highDeco,  highRanges);
        editor.setDecorations(mediumDeco, medRanges);
        editor.setDecorations(docGapDeco, docRanges);
    }

    dispose() {
        highDeco.dispose();
        mediumDeco.dispose();
        docGapDeco.dispose();
    }
}
