import * as vscode from 'vscode';
import { spawn, ChildProcess } from 'child_process';

let dockerProcess: ChildProcess | null = null;

export function activate(context: vscode.ExtensionContext) {
    console.log('[MCP-ACTIVATE] Extension is now active.');

    const startCommand = vscode.commands.registerCommand('mcp-agent.start', () => {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders || workspaceFolders.length === 0) {
            vscode.window.showErrorMessage("You must open a folder in VS Code to use the MCP Agent.");
            return;
        }
        const activeWorkspacePath = workspaceFolders[0].uri.fsPath;
        console.log(`[MCP-COMMAND] Active workspace is: ${activeWorkspacePath}`);

        startBackend(activeWorkspacePath).then(() => {
            McpPanel.createOrShow(context);
        }).catch(error => {
            vscode.window.showErrorMessage(`Failed to start the backend: ${error.message}`);
        });
    });

    context.subscriptions.push(startCommand);
}


async function startBackend(workspacePath: string): Promise<void> {
    return new Promise((resolve, reject) => {
        if (dockerProcess) {
            console.log("[MCP-DOCKER] Backend is already running.");
            resolve();
            return;
        }

        console.log("[MCP-DOCKER] Starting Docker services in the background...");
        
        const command = 'docker';
        const args = ['compose', 'up', '--build', '-d'];
        const options = {
            cwd: workspacePath,
            env: {
                ...process.env,
                COMPOSE_FILE: vscode.Uri.joinPath(vscode.extensions.getExtension('undefined_publisher.mcp-server')!.extensionUri, 'backend/docker-compose.yml').fsPath
            }
        };

        dockerProcess = spawn(command, args, options);

        if (dockerProcess.stdout) {
            dockerProcess.stdout.on('data', (data) => {
                console.log(`[DOCKER-STDOUT]: ${data}`);
            });
        }

        if (dockerProcess.stderr) {
            dockerProcess.stderr.on('data', (data) => {
                console.error(`[DOCKER-STDERR]: ${data}`);
            });
        };
        
        setTimeout(() => {
            console.log("[MCP-DOCKER] Backend should be ready.");
            resolve();
        }); 

        dockerProcess.on('close', (code) => {
            console.log(`[MCP-DOCKER] Process exited with code ${code}`);
            dockerProcess = null;
            if (code !== 0) {
                reject(new Error(`Docker Compose failed to start with exit code ${code}. Check the debug console.`));
            }
        });
    });
}

async function stopBackend(): Promise<void> {
    if (dockerProcess) {
        console.log("[MCP-DOCKER] Stopping backend services...");
        const options = dockerProcess.spawnargs.length > 2 ? { cwd: (dockerProcess as any).spawnoptions.cwd, env: (dockerProcess as any).spawnoptions.env } : {};
        spawn('docker', ['compose', 'down'], options);
        dockerProcess.kill();
        dockerProcess = null;
    }
}


class McpPanel {
    public static currentPanel: McpPanel | undefined;
    private readonly _panel: vscode.WebviewPanel;
    private _disposables: vscode.Disposable[] = [];

    private constructor(panel: vscode.WebviewPanel, context: vscode.ExtensionContext) {
        this._panel = panel;
        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);
        this._panel.webview.html = this._getHtmlForWebview(context);
        
        this._panel.webview.onDidReceiveMessage(
            async (message) => {
                if (message.command === 'userMessage') {
                    this.postMessageToWebview('agentThinking', '🤖 Thinking...');
                    try {
                        const response = await fetch('http://localhost:8000/run-task', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ prompt: message.text }),
                        });
                        const result = await response.json() as { status: string, result?: any, message?: string };
                         if (result.status === 'success') {
                            this.postMessageToWebview('agentResponse', JSON.stringify(result.result, null, 2));
                        } else {
                            this.postMessageToWebview('systemError', `Backend Error: ${result.message}`);
                        }
                    } catch (error: any) {
                         this.postMessageToWebview('systemError', `Network Error: ${error.message}`);
                    }
                }
            }, 
            null, 
            this._disposables
        );
    }
    
    public static createOrShow(context: vscode.ExtensionContext) {
        const column = vscode.ViewColumn.Two;
        if (McpPanel.currentPanel) {
            McpPanel.currentPanel._panel.reveal(column);
            return;
        }
        const panel = vscode.window.createWebviewPanel('mcpAgent', 'MCP Agent', column, {
            enableScripts: true,
            localResourceRoots: [vscode.Uri.joinPath(context.extensionUri, 'src', 'webview')]
        });
        McpPanel.currentPanel = new McpPanel(panel, context);
    }

    private postMessageToWebview(command: string, text: string) {
        this._panel.webview.postMessage({ command, text });
    }

    public dispose() {
        McpPanel.currentPanel = undefined;
        this._panel.dispose();
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
    return stopBackend();
}
