import os
from typing import Tuple

def parse(args_list: list) -> bool:
    if '-web' in args_list:
        return True
    return False

def run(fs, launch_file: str, dependencies: list, project_name: str, server_type: str, platforms: set) -> Tuple[bool, str]:
    try:
        files_created = []

        # 1. Generate index.html content
        scripts_block = ""
        for dep in dependencies:
            if dep.startswith('src:'):
                url = dep.split('src:', 1)[1]
                scripts_block += f'    <script src="{url}"></script>\n'
            elif dep.startswith('css:'):
                url = dep.split('css:', 1)[1]
                scripts_block += f'    <link rel="stylesheet" href="{url}">\n'
            elif dep.endswith('.css'):
                scripts_block += f'    <link rel="stylesheet" href="{dep}">\n'
            else:
                scripts_block += f'    <script src="{dep}"></script>\n'

        # If launch_file is not index.html, we assume it's a main js file we should link
        main_script_link = ""
        if launch_file.endswith('.js'):
            main_script_link = f'    <script src="{launch_file}"></script>'
        
        html_content = get_index_html_template().format(
            project_name=project_name,
            scripts=scripts_block,
            main_script=main_script_link
        )

        # Only create index.html if it doesn't exist, to avoid overwriting user content unless it's a fresh setup
        if not fs.exists("@ROOT/index.html"):
            fs.write("@ROOT/index.html", html_content)
            files_created.append("index.html")

        # 2. Generate Server Scripts if requested
        if server_type:
            svr_type = server_type.lower()
            if svr_type == 'python':
                cmd_win = "python -m http.server 5050"
                cmd_unix = "python3 -m http.server 5050"
                
            elif svr_type == 'nodejs':
                # Create a simple server.js to avoid external deps like http-server
                server_js_content = get_nodejs_server_code()
                fs.write("@ROOT/simple_server.js", server_js_content)
                files_created.append("simple_server.js")
                
                cmd_win = "node simple_server.js"
                cmd_unix = "node simple_server.js"
            else:
                return False, f"Unknown server type: {server_type}"

            # Create Launch Scripts for Server
            if 'win' in platforms:
                fs.write("@ROOT/server.bat", get_server_bat_template().format(cmd=cmd_win))
                files_created.append("server.bat")
            
            if 'unix' in platforms:
                sh_content = get_server_sh_template().format(cmd=cmd_unix)
                fs.write_bytes("@ROOT/server.sh", sh_content.replace('\\r\\n', '\\n').encode('utf-8'))
                files_created.append("server.sh")

        return True, f"Web project initialized. Files created: {', '.join(files_created)}"

    except Exception as e:
        return False, f"Error creating web files: {e}"

def get_index_html_template():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project_name}</title>
    <style>
        body {{ margin: 0; background-color: #111; color: #eee; font-family: sans-serif; }}
        #app {{ display: flex; justify-content: center; align-items: center; height: 100vh; }}
    </style>
{scripts}
</head>
<body>
    <div id="app">
        <h1>{project_name}</h1>
    </div>
{main_script}
</body>
</html>"""

def get_server_bat_template():
    return """@echo off
echo Starting local server...
echo Access at http://localhost:5050
{cmd}
pause
"""

def get_server_sh_template():
    return """#!/bin/bash
echo "Starting local server..."
echo "Access at http://localhost:5050"
{cmd}
"""

def get_nodejs_server_code():
    return """const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 5050;

http.createServer((req, res) => {
    let filePath = '.' + req.url;
    if (filePath === './') filePath = './index.html';

    const extname = path.extname(filePath);
    let contentType = 'text/html';
    switch (extname) {
        case '.js': contentType = 'text/javascript'; break;
        case '.css': contentType = 'text/css'; break;
        case '.json': contentType = 'application/json'; break;
        case '.png': contentType = 'image/png'; break;
        case '.jpg': contentType = 'image/jpg'; break;
        case '.wav': contentType = 'audio/wav'; break;
    }

    fs.readFile(filePath, (error, content) => {
        if (error) {
            if(error.code === 'ENOENT') {
                res.writeHead(404);
                res.end('404 Not Found');
            } else {
                res.writeHead(500);
                res.end('Error: ' + error.code);
            }
        } else {
            res.writeHead(200, { 'Content-Type': contentType });
            res.end(content, 'utf-8');
        }
    });
}).listen(PORT);

console.log(`Server running at http://localhost:${PORT}/`);
"""

from typing import List, Tuple

def tests(vfs) -> List[Tuple[str, bool, str]]:
    res =[]
    parsed = parse(['-web'])
    res.append(("Parse Web", parsed is True, str(parsed)))

    succ, msg = run(vfs, 'index.js',['src:https://cdn/phaser.js', 'style.css'], 'WebProj', 'Python', {'win'})
    passed = succ and vfs.exists('@ROOT/index.html') and vfs.exists('@ROOT/server.bat')
    res.append(("Web Project Generate", passed, msg))
    return res
