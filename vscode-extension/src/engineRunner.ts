/**
 * EngineRunner — เรียก bridge.py และ parse JSON ที่ได้กลับมา
 */

import * as vscode from 'vscode';
import * as path from 'path';
import * as cp from 'child_process';

// ── Types ─────────────────────────────────────────────────────────────

export interface FunctionAnnotation {
    name: string;
    start_line: number;   // 0-indexed
    end_line: number;
    cyclomatic: number;
    cognitive: number;
    severity: 'low' | 'medium' | 'high';
}

export interface DocGap {
    name: string;
    type: string;
    start_line: number;
}

export interface FileResult {
    file_path: string;
    language: string;
    parse_errors: boolean;
    total_score: number;
    severity: 'low' | 'medium' | 'high';
    dimensions: {
        complexity:     { score: number; avg_cyclomatic: number; max_cyclomatic: number; avg_cognitive: number; function_count: number };
        duplication:    { score: number; ratio_pct: number; duplicated_lines: number; total_lines: number };
        documentation:  { score: number; coverage_ratio: number; documented_funcs: number; total_funcs: number; has_module_doc: boolean };
        error_handling: { score: number; coverage_ratio: number; bare_except_count: number; funcs_handled: number; total_functions: number };
    };
    annotations: { functions: FunctionAnnotation[]; doc_gaps: DocGap[] };
    error?: string;
}

export interface WorkspaceResult {
    directory: string;
    files_analyzed: number;
    files_skipped: number;
    average_score: number;
    max_score: number;
    min_score: number;
    severity_distribution: { low: number; medium: number; high: number };
    files: FileResult[];
    error?: string;
}

// ── Class ─────────────────────────────────────────────────────────────

export class EngineRunner {
    private readonly bridgePath: string;

    constructor(private context: vscode.ExtensionContext) {
        this.bridgePath = path.join(context.extensionPath, 'python-bridge', 'bridge.py');
    }

    private get pythonPath(): string {
        return vscode.workspace.getConfiguration('aitd').get<string>('pythonPath') || 'python';
    }

    private get enginePath(): string {
        return vscode.workspace.getConfiguration('aitd').get<string>('enginePath') || '';
    }

    private get weightsJson(): string {
        const cfg = vscode.workspace.getConfiguration('aitd');
        return JSON.stringify({
            complexity:     cfg.get<number>('weights.complexity')    ?? 0.30,
            duplication:    cfg.get<number>('weights.duplication')   ?? 0.25,
            documentation:  cfg.get<number>('weights.documentation') ?? 0.20,
            error_handling: cfg.get<number>('weights.errorHandling') ?? 0.25,
        });
    }

    private run(args: string[]): Promise<any> {
        return new Promise((resolve, reject) => {
            const env: NodeJS.ProcessEnv = { ...process.env };
            if (this.enginePath) { env['AITD_ENGINE_PATH'] = this.enginePath; }

            const proc = cp.spawn(
                this.pythonPath,
                [this.bridgePath, ...args, '--weights', this.weightsJson],
                { env },
            );

            let stdout = '';
            let stderr = '';
            proc.stdout.on('data', (d: Buffer) => { stdout += d.toString(); });
            proc.stderr.on('data', (d: Buffer) => { stderr += d.toString(); });

            proc.on('error', (err: Error) =>
                reject(new Error(`ไม่สามารถเรียก Python ได้: ${err.message}\nตรวจสอบ aitd.pythonPath`))
            );

            proc.on('close', () => {
                if (!stdout.trim()) {
                    reject(new Error(`Engine ไม่มี output. stderr: ${stderr.slice(0, 300)}`));
                    return;
                }
                try {
                    resolve(JSON.parse(stdout));
                } catch {
                    reject(new Error(`Engine output ไม่ใช่ JSON: ${stdout.slice(0, 200)}`));
                }
            });
        });
    }

    async analyzeFile(filePath: string): Promise<FileResult> {
        return this.run(['--file', filePath]);
    }

    async analyzeDirectory(dirPath: string): Promise<WorkspaceResult> {
        return this.run(['--dir', dirPath]);
    }
}
