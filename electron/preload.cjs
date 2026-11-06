// Sandboxed preload: exposes a minimal, allowlisted `require('electron')` shim so the
// renderer keeps working without nodeIntegration. Must be CommonJS (package is "type":"module").
const { contextBridge, ipcRenderer, webUtils } = require('electron');

const INVOKE = new Set([
  'get-stream-url', 'probe-seek-quality', 'optimize-for-seeking', 'cancel-seek-optimize',
  'extract-seek-frame', 'iptv-fetch', 'get-network-info', 'telemetry:get', 'telemetry:set',
]);
const SEND = new Set(['quit-app', 'restart-and-install']);
const ON = new Set(['update-available', 'update-downloaded', 'update-error', 'open-file']);

const wrappers = new Map(); // channel -> Map(renderer fn -> wrapper)

const api = {
  ipcRenderer: {
    invoke: (ch, ...args) => {
      if (!INVOKE.has(ch)) return Promise.reject(new Error('Blocked IPC channel: ' + ch));
      return ipcRenderer.invoke(ch, ...args);
    },
    send: (ch, ...args) => { if (SEND.has(ch)) ipcRenderer.send(ch, ...args); },
    on: (ch, fn) => {
      if (!ON.has(ch) || typeof fn !== 'function') return;
      const w = (_e, ...a) => fn({}, ...a); // never leak the IpcRendererEvent
      if (!wrappers.has(ch)) wrappers.set(ch, new Map());
      wrappers.get(ch).set(fn, w);
      ipcRenderer.on(ch, w);
    },
    removeListener: (ch, fn) => {
      const m = wrappers.get(ch);
      const w = m && m.get(fn);
      if (w) { ipcRenderer.removeListener(ch, w); m.delete(fn); }
    },
  },
  webUtils: { getPathForFile: (file) => webUtils.getPathForFile(file) },
};

// Keeps the existing `window.require('electron')` call sites in App.tsx working unchanged.
contextBridge.exposeInMainWorld('require', (name) => {
  if (name === 'electron') return api;
  throw new Error('Module not available: ' + name);
});
