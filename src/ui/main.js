Ext.namespace("SYNO.SDS.Synoiperf3");

// -----------------------------------------------------------------
// App entry point
// -----------------------------------------------------------------
Ext.define("SYNO.SDS._ThirdParty.App.Synoiperf3", {
    extend: "SYNO.SDS.AppInstance",
    appWindowName: "SYNO.SDS.Synoiperf3.MainWindow",
    constructor: function() {
        this.callParent(arguments);
    }
});

// -----------------------------------------------------------------
// Shared API helpers - two paths, two different response shapes.
// api.cgi: plain request/response JSON (settings only).
// stream.cgi: long-running SSE, consumed via EventSource, not apiCall.
// -----------------------------------------------------------------
SYNO.SDS.Synoiperf3.API_PATH = "/webman/3rdparty/Synoiperf3/api.cgi";
SYNO.SDS.Synoiperf3.STREAM_PATH = "/webman/3rdparty/Synoiperf3/stream.cgi";

SYNO.SDS.Synoiperf3.apiCall = function(action, params, callback) {
    Ext.Ajax.request({
        url: SYNO.SDS.Synoiperf3.API_PATH,
        method: "GET",
        params: Ext.apply({ action: action, _ts: new Date().getTime() }, params || {}),
        success: function(response) {
            var resp;
            try {
                resp = Ext.decode(response.responseText);
            } catch (e) {
                resp = { success: false, message: "Bad response from api.cgi" };
            }
            callback(resp);
        },
        failure: function() {
            callback({ success: false, message: "Request to api.cgi failed" });
        }
    });
};

// -----------------------------------------------------------------
// Main window
// -----------------------------------------------------------------
Ext.define("SYNO.SDS.Synoiperf3.MainWindow", {
    extend: "SYNO.SDS.AppWindow",

    constructor: function(a) {
        this.appInstance = a.appInstance;
        SYNO.SDS.Synoiperf3.MainWindow.superclass.constructor.call(this, Ext.apply({
            layout: "fit",
            resizable: true,
            cls: "syno-app-win iperf3-win",
            maximizable: true,
            minimizable: true,
            showHelp: false,
            width: 710,
            height: 560,
            html: this.buildHtml(),
            listeners: {
                afterrender: {
                    fn: this.onAfterRender,
                    scope: this
                }
            }
        }, a));
    },

    buildHtml: function() {
        return [
            '<style>',
            '  .iperf3-log { -webkit-user-select: text; -moz-user-select: text; -ms-user-select: text; user-select: text; }',
            '  .iperf3-body { display:flex; flex-direction:column; height:100%; padding:8px; box-sizing:border-box; position:relative; }',
            '  .iperf3-form { flex:0 0 auto; display:flex; flex-wrap:wrap; gap:8px; align-items:center; padding-bottom:8px; }',
            '  .iperf3-form label { font-size:12px; color:#555; }',
            '  .iperf3-form input[type=text], .iperf3-form input[type=number], .iperf3-form select {',
            '    padding:4px 6px; border:1px solid #ccc; border-radius:4px; font-size:13px;',
            '  }',
            '  .iperf3-target { width:160px; }',
            '  .iperf3-port { width:70px; }',
            '  .iperf3-streams { width:50px; }',
            '  .iperf3-toolbar { flex:0 0 auto; padding-bottom:8px; display:flex; align-items:center; gap:8px; }',
            '  .iperf3-toolbar button { padding:5px 18px; cursor:pointer; border-radius:4px; font-size:13px; font-weight:bold; border:1px solid #ccc; background-color:#fff; color:#555; }',
            '  .iperf3-toolbar button:hover { border:1px solid #aaa; background-color:#f0f0f0; }',
            '  .iperf3-run { border:1px solid #1B8AED !important; background-color:#1B8AED !important; color:#fff !important; }',
            '  .iperf3-run:hover { border:1px solid #057FEB !important; background-color:#057FEB !important; }',
            '  .iperf3-run:disabled { opacity:0.6; cursor:default; }',
            '  .iperf3-status { font-size:13px; color:#888; }',
            '  .iperf3-log { flex:1 1 auto; margin:0; overflow:auto; background:#161eb5; color:#ddd; padding:8px; font-family:\'Courier New\',monospace; font-size:12px; white-space:pre-wrap; border-radius:4px; }',
            '  .iperf3-modal-backdrop { display:none; position:absolute; top:0; left:0; right:0; bottom:0; background:rgba(0,0,0,0.45); z-index:1000; align-items:center; justify-content:center; }',
            '  .iperf3-modal-backdrop.open { display:flex; }',
            '  .iperf3-modal { position:relative; background:#fff; color:#222; width:320px; padding:20px; border-radius:6px; box-shadow:0 4px 24px rgba(0,0,0,0.35); }',
            '  .iperf3-modal-close { position:absolute; top:8px; right:10px; border:none; background:none; font-size:16px; cursor:pointer; color:#666; line-height:1; padding:4px; }',
            '  .iperf3-modal-close:hover { color:#000; }',
            '  .iperf3-row { margin-bottom:14px; }',
            '  .iperf3-row label { display:inline-block; margin-bottom:4px; }',
            '  .iperf3-settings-buttons { text-align:right; margin-top:6px; }',
            '  .iperf3-settings-buttons button { padding:5px 18px; margin-left:8px; cursor:pointer; border-radius:4px; font-size:13px; font-weight:bold; }',
            '  .iperf3-cancel { border:1px solid #ccc; background-color:#fff; color:#555; }',
            '  .iperf3-cancel:hover { border:1px solid #aaa; background-color:#f0f0f0; }',
            '  .iperf3-save { border:1px solid #1B8AED; background-color:#1B8AED; color:#fff; }',
            '  .iperf3-save:hover { border:1px solid #057FEB; background-color:#057FEB; }',
            '  .iperf3-settings-status { font-size:12px; color:#888; min-height:16px; }',
            '</style>',
            '<div class="iperf3-body">',
            '  <div class="iperf3-form">',
            '    <label>Target: <input type="text" class="iperf3-target" placeholder="192.168.1.x"></label>',
            '    <label>Port: <input type="number" class="iperf3-port" value="5201"></label>',
            '    <label>Protocol:',
            '      <select class="iperf3-protocol"><option value="tcp">TCP</option><option value="udp">UDP</option></select>',
            '    </label>',
            '    <label>Mode:',
            '      <select class="iperf3-mode"><option value="upload">Upload</option><option value="download">Download</option></select>',
            '    </label>',
            '    <label>Streams: <input type="number" class="iperf3-streams" value="1" min="1" max="128"></label>',
            '  </div>',
            '  <div class="iperf3-toolbar">',
            '    <button type="button" class="iperf3-run">Run Speed Test</button>',
            '    <button type="button" class="iperf3-clear">Clear</button>',
            '    <button type="button" class="iperf3-settings">Settings</button>',
            '    <span class="iperf3-status"></span>',
            '  </div>',
            '  <pre class="iperf3-log">Set a target and click Run Speed Test.</pre>',
            '  <div class="iperf3-modal-backdrop">',
            '    <div class="iperf3-modal">',
            '      <button type="button" class="iperf3-modal-close" aria-label="Close">\u00d7</button>',
            '      <div class="iperf3-row">',
            '        <label>Default target IP:</label>',
            '        <input type="text" class="iperf3-default-target" style="width:100%">',
            '      </div>',
            '      <div class="iperf3-row">',
            '        <label>Default port:</label>',
            '        <input type="number" class="iperf3-default-port" style="width:80px">',
            '      </div>',
            '      <div class="iperf3-row iperf3-settings-status"></div>',
            '      <div class="iperf3-row iperf3-settings-buttons">',
            '        <button type="button" class="iperf3-cancel">Cancel</button>',
            '        <button type="button" class="iperf3-save">Save</button>',
            '      </div>',
            '    </div>',
            '  </div>',
            '</div>'
        ].join("");
    },

    onAfterRender: function() {
        var el = this.body.dom;
        this.logEl = el.querySelector(".iperf3-log");
        this.statusEl = el.querySelector(".iperf3-status");
        this.runBtn = el.querySelector(".iperf3-run");
        this.targetEl = el.querySelector(".iperf3-target");
        this.portEl = el.querySelector(".iperf3-port");
        this.protocolEl = el.querySelector(".iperf3-protocol");
        this.modeEl = el.querySelector(".iperf3-mode");
        this.streamsEl = el.querySelector(".iperf3-streams");
        this.backdropEl = el.querySelector(".iperf3-modal-backdrop");
        this.defaultTargetEl = el.querySelector(".iperf3-default-target");
        this.defaultPortEl = el.querySelector(".iperf3-default-port");
        this.settingsStatusEl = el.querySelector(".iperf3-settings-status");

        Ext.fly(this.runBtn).on("click", this.runTest, this);
        Ext.fly(el.querySelector(".iperf3-clear")).on("click", this.clearLog, this);
        Ext.fly(el.querySelector(".iperf3-settings")).on("click", this.openSettings, this);
        Ext.fly(el.querySelector(".iperf3-modal-close")).on("click", this.closeSettings, this);
        Ext.fly(el.querySelector(".iperf3-cancel")).on("click", this.closeSettings, this);
        Ext.fly(el.querySelector(".iperf3-save")).on("click", this.onSaveSettings, this);
        Ext.fly(this.backdropEl).on("click", function(ev) {
            if (ev.getTarget() === this.backdropEl) { this.closeSettings(); }
        }, this);

        Ext.fly(el).on("contextmenu", function(ev) { ev.stopPropagation(); });

        // Unlike CPUTemp, don't auto-run on open - this kicks off a real
        // 10-second network test, which shouldn't fire just because the
        // window opened. Just load saved defaults into the form instead.
        this.loadDefaultsIntoForm();
    },

    setStatus: function(msg) {
        if (this.statusEl) { this.statusEl.textContent = msg || ""; }
    },

    setSettingsStatus: function(msg) {
        if (this.settingsStatusEl) { this.settingsStatusEl.textContent = msg || ""; }
    },

    appendLog: function(text) {
        if (!this.logEl) { return; }
        if (this.logEl.textContent === "Set a target and click Run Speed Test." || this.logEl.textContent === "(log is empty)") {
            this.logEl.textContent = "";
        }
        this.logEl.textContent += text + "\n";
        this.logEl.scrollTop = this.logEl.scrollHeight;
    },

    clearLog: function() {
        if (this.logEl) { this.logEl.textContent = "(log is empty)"; }
    },

    loadDefaultsIntoForm: function() {
        SYNO.SDS.Synoiperf3.apiCall("getsettings", {}, (function(resp) {
            if (resp && resp.success) {
                if (resp.default_target) { this.targetEl.value = resp.default_target; }
                if (resp.default_port) { this.portEl.value = resp.default_port; }
            }
        }).createDelegate(this));
    },

    // Runs the live test via SSE. Not apiCall - stream.cgi is a
    // long-running response, not a single JSON reply.
    runTest: function() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }

        var target = this.targetEl.value.trim();
        if (!target) {
            this.setStatus("Enter a target IP first");
            return;
        }

        var params = Ext.urlEncode({
            target: target,
            port: this.portEl.value || 5201,
            protocol: this.protocolEl.value,
            mode: this.modeEl.value,
            streams: this.streamsEl.value || 1
        });

        this.clearLog();
        this.setStatus("Running\u2026");
        this.runBtn.disabled = true;

        var es = new EventSource(SYNO.SDS.Synoiperf3.STREAM_PATH + "?" + params);
        this.eventSource = es;

        es.onmessage = (function(ev) {
            this.appendLog(ev.data);
            // iperf3's own final line - use it as the signal to close the
            // connection ourselves. Without this, EventSource's default
            // behaviour on a closed connection is to auto-reconnect,
            // which would silently re-trigger stream.cgi and re-run
            // iperf3 in a loop.
            if (ev.data.indexOf("iperf Done.") !== -1 || ev.data.indexOf("error:") === 0) {
                this.finishTest();
            }
        }).createDelegate(this);

        es.onerror = (function() {
            // Fires both on a genuine network/proxy failure and on a
            // clean server-side close if we didn't already close first
            // above - treat it as "test ended" either way rather than
            // letting the browser retry.
            this.finishTest();
        }).createDelegate(this);
    },

    finishTest: function() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
        this.setStatus("");
        this.runBtn.disabled = false;
    },

    openSettings: function() {
        this.setSettingsStatus("");
        SYNO.SDS.Synoiperf3.apiCall("getsettings", {}, (function(resp) {
            if (resp && resp.success) {
                this.defaultTargetEl.value = resp.default_target || "";
                this.defaultPortEl.value = resp.default_port || 5201;
            } else {
                this.defaultTargetEl.value = "";
                this.defaultPortEl.value = 5201;
                this.setSettingsStatus((resp && resp.message) || "Could not load settings");
            }
            Ext.fly(this.backdropEl).addClass("open");
        }).createDelegate(this));
    },

    closeSettings: function() {
        Ext.fly(this.backdropEl).removeClass("open");
    },

    onSaveSettings: function() {
        this.setSettingsStatus("Saving\u2026");
        SYNO.SDS.Synoiperf3.apiCall("setsettings", {
            default_target: this.defaultTargetEl.value,
            default_port: this.defaultPortEl.value
        }, (function(resp) {
            if (resp && resp.success) {
                this.setSettingsStatus("");
                this.closeSettings();
                this.loadDefaultsIntoForm();
            } else {
                this.setSettingsStatus((resp && resp.message) || "Failed to save settings");
            }
        }).createDelegate(this));
    },

    onClose: function() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
        SYNO.SDS.Synoiperf3.MainWindow.superclass.onClose.apply(this, arguments);
        this.doClose();
        return true;
    }
});
