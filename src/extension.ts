import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { spawn, ChildProcess } from 'child_process';

export function activate(context: vscode.ExtensionContext) {
    console.log('[MCP-ACTIVATE] Extension is now active.');

    const startCommand = vscode.commands.registerCommand('mcp-agent.start', async () => {
        const workspaceInfo = await setupWorkspace(context);
        if (!workspaceInfo) {
            vscode.window.showErrorMessage("Failed to set up MCP workspace.");
            return;
        }

        console.log("[MCP-COMMAND] Workspace is ready. Creating panel...");
        McpPanel.createOrShow(context, workspaceInfo.backendScriptPath, workspaceInfo.backendCwd);
    });

    context.subscriptions.push(startCommand);
}

interface WorkspaceInfo {
    backendScriptPath: string;
    backendCwd: string; 
}

async function setupWorkspace(context: vscode.ExtensionContext): Promise<WorkspaceInfo | undefined> {
    const globalStorageUri = context.globalStorageUri;
    const finalWorkspaceRoot = vscode.Uri.joinPath(globalStorageUri, 'mcp-session-workspace');
    
    const backendSourcePath = path.join(context.extensionPath, 'backend');
    const backendDestPath = path.join(finalWorkspaceRoot.fsPath, 'backend');
    const workspacePath = path.join(finalWorkspaceRoot.fsPath, 'workspace');

    try {
        if (!fs.existsSync(workspacePath)) {
            fs.mkdirSync(workspacePath, { recursive: true });
        }
        if (!fs.existsSync(backendDestPath)) {
            vscode.window.showInformationMessage("Setting up MCP backend for the first time...");
            fs.cpSync(backendSourcePath, backendDestPath, { recursive: true });
            fs.chmodSync(path.join(backendDestPath, 'run_controller.sh'), '755');
        }

        return {
            backendScriptPath: path.join(backendDestPath, 'run_controller.sh'),
            backendCwd: backendDestPath
        };

    } catch (err: any) {
        vscode.window.showErrorMessage(`Error setting up workspace: ${err.message}`);
        return undefined;
    }
}

class McpPanel {
    public static currentPanel: McpPanel | undefined;
    private readonly _panel: vscode.WebviewPanel;
    private _disposables: vscode.Disposable[] = [];
    private _backendProcess: ChildProcess | null = null;

    private constructor(panel: vscode.WebviewPanel, context: vscode.ExtensionContext, backendScriptPath: string, backendCwd: string) {
        this._panel = panel;
        this._disposables.push(this._panel.onDidDispose(() => this.dispose()));

        this._panel.webview.html = this._getHtmlForWebview(context);
        
        this._panel.webview.onDidReceiveMessage(message => {
            if (message.command === 'userMessage' && this._backendProcess?.stdin) {
                this._backendProcess.stdin.write(message.text + '\n');
            }
        }, null, this._disposables);

        this.startBackendProcess(backendScriptPath, backendCwd);
    }

    public static createOrShow(context: vscode.ExtensionContext, backendScriptPath: string, backendCwd: string) {
        const column = vscode.ViewColumn.Two;
        if (McpPanel.currentPanel) {
            McpPanel.currentPanel._panel.reveal(column);
            return;
        }
        const panel = vscode.window.createWebviewPanel('mcpAgent', 'MCP Agent', column, {
            enableScripts: true,
            localResourceRoots: [vscode.Uri.joinPath(context.extensionUri, 'src', 'webview')]
        });
        McpPanel.currentPanel = new McpPanel(panel, context, backendScriptPath, backendCwd);
    }

    private startBackendProcess(scriptPath: string, cwd: string) {
        if (!fs.existsSync(scriptPath)) {
            this.postMessageToWebview('systemError', `ERROR: run_controller.sh not found at ${scriptPath}!`);
            return;
        }
        console.log(`[MCP-PANEL] Starting backend process: ${scriptPath}`);
        this._backendProcess = spawn('/bin/bash', [scriptPath], { cwd });

        this._backendProcess.stdout?.on('data', (data) => this.postMessageToWebview('agentMessage', data.toString()));
        this._backendProcess.stderr?.on('data', (data) => this.postMessageToWebview('systemError', data.toString()));
        this._backendProcess.on('close', (code) => {
            this.postMessageToWebview('systemStatus', `Backend process exited with code ${code}`);
            this._backendProcess = null;
        });
    }

    private postMessageToWebview(command: string, text: string) {
        this._panel.webview.postMessage({ command, text });
    }

    public dispose() {
        McpPanel.currentPanel = undefined;
        this._panel.dispose();
        if (this._backendProcess) {
            this._backendProcess.kill('SIGKILL');
        }
        while (this._disposables.length) {
            this._disposables.pop()?.dispose();
        }
    }

    private _getHtmlForWebview(context: vscode.ExtensionContext): string {
        const webview = this._panel.webview;
        const scriptUri = webview.asWebviewUri(vscode.Uri.joinPath(context.extensionUri, 'src', 'webview', 'main.js'));
        const styleUri = webview.asWebviewUri(vscode.Uri.joinPath(context.extensionUri, 'src', 'webview', 'style.css'));
        return `<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><link href="${styleUri}" rel="stylesheet"><title>MCP Agent</title></head><body><div id="chat-container"><div id="message-list"></div><div id="input-container"><input type="text" id="message-input" placeholder="Type your request..."><button id="send-button">Send</button></div></div><script src="${scriptUri}"></script></body></html>`;
    }
}

export function deactivate() {
    if (McpPanel.currentPanel) {
        McpPanel.currentPanel.dispose();
    }
}