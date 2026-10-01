/**
 * Entry point.
 *
 * Style import order is deliberate: tokens, then reset/primitives, then the composed
 * layers, so later files can rely on the custom properties being defined.
 */

import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

import { App } from './App';
import './styles/tokens.css';
import './styles/base.css';
import './styles/shell.css';
import './styles/evidence.css';
import './styles/pages.css';
import './shaders/threeui.css';
import './styles/workspace.css';
import './styles/sidebar-glass.css';
import './styles/theme.css';

const container = document.getElementById('root');
if (!container) {
  throw new Error('index.html is missing the #root element.');
}

createRoot(container).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
