import { useSyncExternalStore } from 'react';

// The preference lasts for this page visit. Every new document starts in dark mode.
let darkMode = true;
const listeners = new Set<() => void>();
function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => { listeners.delete(listener); };
}
function snapshot() { return darkMode; }
function toggle() {
  darkMode = !darkMode;
  document.documentElement.dataset.theme = darkMode ? 'dark' : 'light';
  const meta = document.querySelector<HTMLMetaElement>('meta[name="theme-color"]');
  if (meta) meta.content = darkMode ? '#18100b' : '#f8f6f5';
  listeners.forEach(listener => listener());
}
export function useColorMode() {
  return { darkMode: useSyncExternalStore(subscribe, snapshot), toggleColorMode: toggle };
}
