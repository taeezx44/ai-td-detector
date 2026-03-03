/**
 * AI-TD Detector — VS Code Extension Entry Point
 *
 * Flow:
 *   extension.ts ──► engineRunner.ts ──► bridge.py ──► Python Engine
 *                ──► decorationManager.ts  (inline annotations)
 *                ──► panelProvider.ts      (webview dashboard)
 *                ──► statusBarItem.ts      (score ใน status bar)
 */

import * as vscode from 'vscode';
import { EngineRunner } from './engineRunner';
import { DecorationManager } from './decorationManager';
import { PanelProvider } from './panelProvider';
import { StatusBarItem } from './statusBarItem';

const SUPPORTED_LANGS = new Set(['python', 'javascript', 'typescript']);

let runner: EngineRunner;
let decorations: DecorationManager;
let panel: PanelProvider;
let statusBar: StatusBarItem;

// ── Activate ──────────────────────────────────────────────────────────

export function activate(context: vscode.ExtensionContext) {
    console.log('AI-TD Detector: activated');

    runner     = new EngineRunner(context);
    decorations = new DecorationManager();
    panel      = new PanelProvider(context);
    statusBar  = new StatusBarItem();

    // Register commands
    context.subscriptions.push(
        vscode.commands.registerCommand('aitd.analyzeFile',      () => analyzeCurrentFile()),
        vscode.commands.registerCommand('aitd.analyzeWorkspace', () => analyzeWorkspace()),
        vscode.commands.registerCommand('aitd.showPanel',        () => panel.show()),
        vscode.commands.registerCommand('aitd.clearDecorations', () => {
            decorations.clearAll();
            statusBar.setReady();
        }),
    );

    // Auto-analyze on save
    context.subscriptions.push(
        vscode.workspace.onDidSaveTextDocument(async (doc) => {
            const cfg = vscode.workspace.getConfiguration('aitd');
            if (cfg.get<boolean>('autoAnalyzeOnSave') && isSupported(doc)) {
                await analyzeDoc(doc);
            }
        }),
    );

    // Clear old decorations when switching files
    context.subscriptions.push(
        vscode.window.onDidChangeActiveTextEditor(async (editor) => {
            decorations.clearAll();
            if (editor && isSupported(editor.document)) {
                statusBar.setLoading();
                await analyzeDoc(editor.document);
            } else {
                statusBar.setReady();
            }
        }),
    );

    // Analyze file that's open on startup
    const active = vscode.window.activeTextEditor;
    if (active && isSupported(active.document)) {
        analyzeDoc(active.document);
    }

    statusBar.setReady();
}

export function deactivate() {
    decorations.dispose();
    statusBar.dispose();
}

// ── Helpers ───────────────────────────────────────────────────────────

function isSupported(doc: vscode.TextDocument): boolean {
    return SUPPORTED_LANGS.has(doc.languageId) && doc.uri.scheme === 'file';
}

async function analyzeCurrentFile() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showWarningMessage('AI-TD: ไม่มีไฟล์ที่เปิดอยู่');
        return;
    }
    if (!isSupported(editor.document)) {
        vscode.window.showWarningMessage('AI-TD: รองรับเฉพาะ Python, JavaScript, TypeScript');
        return;
    }
    await analyzeDoc(editor.document);
}

async function analyzeDoc(doc: vscode.TextDocument) {
    statusBar.setLoading();
    try {
        const result = await runner.analyzeFile(doc.uri.fsPath);
        if (result.error) {
            statusBar.setError(result.error);
            vscode.window.showErrorMessage(`AI-TD Error: ${result.error}`);
            return;
        }
        decorations.apply(doc, result);
        statusBar.setScore(result.total_score, result.severity);
        panel.updateFile(result);
    } catch (e: any) {
        statusBar.setError('Engine error');
        vscode.window.showErrorMessage(`AI-TD: ${e.message}`);
    }
}

async function analyzeWorkspace() {
    const folders = vscode.workspace.workspaceFolders;
    if (!folders?.length) {
        vscode.window.showWarningMessage('AI-TD: ไม่มี workspace folder ที่เปิดอยู่');
        return;
    }
    await vscode.window.withProgress(
        { location: vscode.ProgressLocation.Notification, title: 'AI-TD: กำลังวิเคราะห์ workspace…', cancellable: false },
        async () => {
            try {
                const result = await runner.analyzeDirectory(folders[0].uri.fsPath);
                if (result.error) {
                    vscode.window.showErrorMessage(`AI-TD Error: ${result.error}`);
                    return;
                }
                panel.updateWorkspace(result);
                panel.show();
                vscode.window.showInformationMessage(
                    `AI-TD: วิเคราะห์ ${result.files_analyzed} ไฟล์ — avg score ${result.average_score.toFixed(4)}`
                );
            } catch (e: any) {
                vscode.window.showErrorMessage(`AI-TD: ${e.message}`);
            }
        },
    );
}
