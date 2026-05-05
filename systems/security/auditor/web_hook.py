WEB_AUDITOR_TEMPLATE = """
<script>
(function() {
    console.warn("🛡️ ELAI Auditor Web Hook Active");

    function requestPermissionSync(action, details) {
        try {
            var xhr = new XMLHttpRequest();
            xhr.open("POST", "http://127.0.0.1:__IPC_PORT__", false);
            xhr.setRequestHeader("Content-Type", "application/json");
            xhr.send(JSON.stringify({action: action, details: details}));
            if (xhr.status === 200) {
                return JSON.parse(xhr.responseText).allow;
            }
        } catch(e) {}
        return false;
    }

    const originalFetch = window.fetch;
    window.fetch = async function() {
        if (!requestPermissionSync("Network Request (Fetch)", arguments[0])) {
            throw new Error("ELAI Security: Network access blocked by user.");
        }
        return originalFetch.apply(this, arguments);
    };

    const originalOpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(method, url) {
        if (!requestPermissionSync("Network Request (XHR)", url)) {
            throw new Error("ELAI Security: Network access blocked by user.");
        }
        return originalOpen.apply(this, arguments);
    };

    // Prevent overriding the hook methods
    try {
        Object.freeze(window.fetch);
        Object.freeze(XMLHttpRequest.prototype.open);
    } catch(e) {}
})();
</script>
"""