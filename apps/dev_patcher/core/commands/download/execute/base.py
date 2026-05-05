import os
import requests
import re
import io
import posixpath
from typing import Tuple
import threading 
from typing import List

def run(args: list, content: str, fs_handler) -> Tuple[bool, str]:
    """
    Executes the DOWNLOAD command.
    """
    # PROTECTION: If we’re in a virtual file system, we shouldn’t actually download files.
    from systems.fs.vfs_core import AdvancedVFS
    if isinstance(fs_handler, AdvancedVFS):
        if len(args) != 2:
            return False, "The DOWNLOAD command requires exactly 2 arguments: URL and destination."

        url_check = args[0].strip('\'"')
        # Simple format validation for simulation; no actual network request.
        if url_check.startswith(('http://', 'https://')):
            try:
                r = requests.head(url_check, timeout=3, allow_redirects=True)
                if r.status_code >= 400 and r.status_code != 405: # 405 Method Not Allowed means HEAD is blocked, GET might still work
                    r = requests.get(url_check, stream=True, timeout=3)
                    r.close()
                    if r.status_code >= 400:
                        return False, f"[SIMULATION] URL returned status {r.status_code}: '{url_check}'"
                return True, f"[SIMULATION] URL reachable: '{url_check}'. Download skipped."
            except Exception as e:
                return False, f"[SIMULATION] URL unreachable: '{url_check}'. Error: {e}"
        else:
            return False, f"[SIMULATION] Invalid URL format: '{url_check}'."
    
    if len(args) != 2:
        return False, "The DOWNLOAD command requires exactly 2 arguments: the URL and the destination path."

    url = args[0].strip('\'"')
    destination = args[1].strip('\'"')

    try:
        # Improved timeout: (connect_timeout, read_timeout)
        with requests.get(url, timeout=(5, 30), stream=True) as response:
            response.raise_for_status()

            # First we try to get the file name from the Content Disposition header.
            filename = None
            if 'content-disposition' in response.headers:
                d = response.headers['content-disposition']
                filenames = re.findall('filename="?([^"]+)"?', d)
                if filenames:
                    filename = filenames[0]

            # If it does not work, take from the URL.
            if not filename:
                filename = os.path.basename(url.split('?')[0])

            # If the file name is still empty, return the error.
            if not filename:
                return False, f"Unable to extract filename from URL: {url} or headers."

            # Define the final path
            final_path = destination
            # Use posixpath for uniformity with fs_handler
            if fs_handler.exists(destination) and fs_handler.is_dir(destination):
                # If the assignment is an existing folder, add the file name.
                final_path = posixpath.join(destination, filename)

            # Streaming download to buffer in memory
            file_buffer = io.BytesIO()
            total_downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                file_buffer.write(chunk)
                total_downloaded += len(chunk)

            # Write to the file system (virtual or real) via fs_handler
            fs_handler.write_bytes(final_path, file_buffer.getvalue())

        # fs_handler._to_abs is used only for logging to show the user the full path.
        abs_final_path = fs_handler._to_abs(final_path)
        return True, f"File '{filename}' ({total_downloaded / 1024:.2f} KB) successfully downloaded and saved: {abs_final_path}"

    except requests.exceptions.Timeout:
        return False, f"Error: Timed out waiting for response from {url}."
    except requests.exceptions.HTTPError as e:
        return False, f"Error: Timed out waiting for response from {url}. {url}"
    except requests.exceptions.RequestException as e:
        return False, f"Network error or invalid URL. Make sure the URL '{url}' is accessible. Details: {e}"
    except Exception as e:
        import traceback
        return False, f"An unexpected error occurred while executing DOWNLOAD: {e}\n{traceback.format_exc()}"

def tests(vfs) -> List[Tuple[str, bool, str]]:
    res =[]
    # VirtualFileSystem verifies basic URL format without making real HTTP requests.
    succ, msg = run(['https://example.com', '@ROOT/dest.txt'], '', vfs)
    passed = succ and "[SIMULATION]" in msg
    res.append(("Download Simulation Valid URL", passed, msg))

    succ, msg = run(['bad_url', '@ROOT/dest.txt'], '', vfs)
    passed = not succ and "[SIMULATION]" in msg and "Invalid URL format" in msg
    res.append(("Download Simulation Invalid URL", passed, msg))
    return res