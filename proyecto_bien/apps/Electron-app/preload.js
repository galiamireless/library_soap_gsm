const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  versions: process.versions,
  isElectron: true,
  openExternal: (url) => require('electron').shell.openExternal(url),
  ipc: ipcRenderer,
});
