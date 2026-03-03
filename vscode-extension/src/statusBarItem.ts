/**
 * StatusBarItem — แสดง AI-TD score ใน status bar ด้านล่างขวา
 *
 *  READY   → "$(search) AI-TD"
 *  LOADING → "$(sync~spin) AI-TD…"
 *  SCORE   → "🟢 AI-TD: 0.1234"  / "🟡 …" / "🔴 …"
 *  ERROR   → "$(warning) AI-TD: Error"
 */

import * as vscode from 'vscode';

const ICON: Record<string, string> = { low: '🟢', medium: '🟡', high: '🔴' };
const COLOR: Record<string, vscode.ThemeColor> = {
    low:    new vscode.ThemeColor('testing.iconPassed'),
    medium: new vscode.ThemeColor('editorWarning.foreground'),
    high:   new vscode.ThemeColor('editorError.foreground'),
};

export class StatusBarItem {
    private readonly item: vscode.StatusBarItem;

    constructor() {
        this.item = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
        this.item.command = 'aitd.showPanel';
        this.item.tooltip = 'AI-TD Detector — คลิกเพื่อเปิด Dashboard';
        this.item.show();
    }

    setReady()   { this.item.text = '$(search) AI-TD'; this.item.color = undefined; }
    setLoading() { this.item.text = '$(sync~spin) AI-TD…'; this.item.color = undefined; }

    setScore(score: number, severity: string) {
        this.item.text    = `${ICON[severity] ?? '⚪'} AI-TD: ${score.toFixed(4)}`;
        this.item.color   = COLOR[severity];
        this.item.tooltip = `AI-TD Score: ${score.toFixed(4)} [${severity.toUpperCase()}]\nคลิกเพื่อดูรายละเอียด`;
    }

    setError(msg: string) {
        this.item.text    = '$(warning) AI-TD: Error';
        this.item.color   = new vscode.ThemeColor('editorError.foreground');
        this.item.tooltip = `AI-TD Error: ${msg}`;
    }

    dispose() { this.item.dispose(); }
}
