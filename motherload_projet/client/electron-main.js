import { app, BrowserWindow } from 'electron';
import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

// Fix for __dirname in ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

let mainWindow;
let pythonProcess;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false, // For simple IPC to Python if needed
        },
        titleBarStyle: 'hiddenInset', // Mac-style seamless header
        backgroundColor: '#0f172a', // Slate 950
        show: false, // Wait until ready to show
    });

    // Load the React app
    // In dev: localhost
    // In prod: index.html
    const startUrl = process.env.ELECTRON_START_URL || 'http://localhost:5173';
    mainWindow.loadURL(startUrl);

    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
    });

    mainWindow.on('closed', function () {
        mainWindow = null;
    });
}

function startPythonBackend() {
    const isDev = process.env.NODE_ENV === 'development';
    // Adjust path to python executable
    // In dev: ../.venv/bin/python
    // In prod: bundled executable
    const pythonExecutable = path.resolve(__dirname, '../../.venv/bin/python');
    const mainScript = path.resolve(__dirname, '../../motherload_projet/cli.py');

    console.log(`Starting Python backend: ${pythonExecutable} -m motherload_projet.cli --start-server`);

    pythonProcess = spawn(pythonExecutable, ['-m', 'motherload_projet.cli', '--start-server'], {
        cwd: path.resolve(__dirname, '../../'),
        stdio: 'inherit' // Pipe output to Electron console
    });

    pythonProcess.on('error', (err) => {
        console.error('Failed to start Python backend:', err);
    });
}

app.on('ready', () => {
    startPythonBackend();
    // Wait a bit for Python to boot before showing window? 
    // Ideally we define a retry loop in the frontend
    setTimeout(createWindow, 2000);
});

app.on('window-all-closed', function () {
    if (process.platform !== 'darwin') app.quit();
});

app.on('activate', function () {
    if (mainWindow === null) createWindow();
});

app.on('will-quit', () => {
    if (pythonProcess) {
        console.log('Killing Python backend...');
        pythonProcess.kill();
    }
});
