NODE_AUDITOR_TEMPLATE = """
const fs = require('fs');
const path = require('path');
const http = require('http');
const https = require('https');
const child_process = require('child_process');

const SANDBOX_ROOT = String.raw`__SANDBOX_ROOT__`;
const IPC_PORT = __IPC_PORT__;

function requestPermissionSync(action, details) {
    try {
        const payload = JSON.stringify({action: action, details: details});
        const pyScript = `
import urllib.request, json, sys
req = urllib.request.Request('http://127.0.0.1:${IPC_PORT}', data=sys.argv[1].encode('utf-8'), headers={'Content-Type': 'application/json'})
try:
    resp = urllib.request.urlopen(req, timeout=65)
    print(json.loads(resp.read().decode())['allow'])
except:
    print("False")
`;
        const pyExe = process.platform === 'win32' ? 'python' : 'python3';
        const res = child_process.execFileSync(pyExe,['-c', pyScript, payload], {encoding: 'utf8'});
        return res.trim() === 'True';
    } catch(e) { return false; }
}

function isSafePath(targetPath) {
    if (!targetPath || typeof targetPath !== 'string') return true;
    const absPath = path.resolve(targetPath);
    return absPath.startsWith(path.resolve(SANDBOX_ROOT));
}

function checkPath(file, action) {
    if (!isSafePath(file)) {
        if (!requestPermissionSync("Modify File/Dir", file)) {
            console.error(`\\x1b[31m🚫 [ELAI-AUDITOR-BLOCK] Blocked ${action} external file: ${file}\\x1b[0m`);
            throw new Error(`ELAI Security: ${action} outside sandbox is strictly forbidden without permission!`);
        }
    }
}

function isWriteFlag(flag) {
    if (!flag) return false;
    const strFlag = String(flag);
    return strFlag.includes('w') || strFlag.includes('a') || strFlag.includes('+');
}

const originalWriteFile = fs.writeFile;
const originalWriteFileSync = fs.writeFileSync;
const originalUnlink = fs.unlink;
const originalUnlinkSync = fs.unlinkSync;
const originalOpen = fs.open;
const originalOpenSync = fs.openSync;

fs.writeFile = function() { checkPath(arguments[0], 'writing to'); return originalWriteFile.apply(this, arguments); };
fs.writeFileSync = function() { checkPath(arguments[0], 'writing to'); return originalWriteFileSync.apply(this, arguments); };
fs.unlink = function() { checkPath(arguments[0], 'deleting'); return originalUnlink.apply(this, arguments); };
fs.unlinkSync = function() { checkPath(arguments[0], 'deleting'); return originalUnlinkSync.apply(this, arguments); };

fs.open = function(p, flags) { 
    if(isWriteFlag(flags)) checkPath(p, 'opening for write'); 
    return originalOpen.apply(this, arguments); 
};
fs.openSync = function(p, flags) { 
    if(isWriteFlag(flags)) checkPath(p, 'opening for write'); 
    return originalOpenSync.apply(this, arguments); 
};

const originalDlopen = process.dlopen;
process.dlopen = function(module, filename) {
    if (!requestPermissionSync("Load Native Addon", filename)) {
        console.error(`\\x1b[31m🚫[ELAI-AUDITOR-BLOCK] Blocked loading native addon: ${filename}\\x1b[0m`);
        throw new Error("ELAI Security: Native addons are forbidden without permission!");
    }
    return originalDlopen.apply(this, arguments);
};

if (fs.promises) {
    const originalPWriteFile = fs.promises.writeFile;
    const originalPUnlink = fs.promises.unlink;
    const originalPOpen = fs.promises.open;

    fs.promises.writeFile = function() { checkPath(arguments[0], 'writing to'); return originalPWriteFile.apply(this, arguments); };
    fs.promises.unlink = function() { checkPath(arguments[0], 'deleting'); return originalPUnlink.apply(this, arguments); };
    fs.promises.open = function(p, flags) { 
        if(isWriteFlag(flags)) checkPath(p, 'opening for write'); 
        return originalPOpen.apply(this, arguments); 
    };
}

const originalExec = child_process.exec;
child_process.exec = function(command) {
    if (!requestPermissionSync("Execute Command", command.toString())) {
        throw new Error("ELAI Security: Execution blocked by user.");
    }
    return originalExec.apply(this, arguments);
};

const originalHttpRequest = http.request;
http.request = function() {
    const url = arguments[0];
    const host = typeof url === 'string' ? url : (url.host || url.hostname || 'unknown');
    if (!requestPermissionSync("Network Request (HTTP)", host)) {
        throw new Error("ELAI Security: Network access blocked by user.");
    }
    return originalHttpRequest.apply(this, arguments);
};

const originalHttpsRequest = https.request;
https.request = function() {
    const url = arguments[0];
    const host = typeof url === 'string' ? url : (url.host || url.hostname || 'unknown');
    if (!requestPermissionSync("Network Request (HTTPS)", host)) {
        throw new Error("ELAI Security: Network access blocked by user.");
    }
    return originalHttpsRequest.apply(this, arguments);
};

// Prevent un-patching in older Node versions (Fallback protection)
try {
    // Block VM and process.binding to prevent sandbox escape
    process.binding = function() { throw new Error("ELAI Security: process.binding is strictly forbidden."); };
    const vm = require('vm');
    vm.runInContext = function() { throw new Error("ELAI Security: vm module is blocked."); };
    vm.runInNewContext = function() { throw new Error("ELAI Security: vm module is blocked."); };
    vm.runInThisContext = function() { throw new Error("ELAI Security: vm module is blocked."); };
    vm.compileFunction = function() { throw new Error("ELAI Security: vm module is blocked."); };
    Object.freeze(vm);

    Object.freeze(fs);
    if (fs.promises) Object.freeze(fs.promises);
    Object.freeze(child_process);
    Object.freeze(http);
    Object.freeze(https);
} catch(e) {}
"""