/**
 * Minimal hash router.
 *
 * The dashboard needs six views and nothing more, so a 60-line hash router is a smaller
 * dependency surface than a routing library (the locked stack names React, TypeScript and
 * Vite only - SRS Sec.24). Hash routing also means the built bundle can be served as
 * static files with no server rewrite rules.
 */

import { useEffect, useState } from 'react';
import type { AnchorHTMLAttributes, ReactNode } from 'react';

export const DEFAULT_ROUTE = '/overview';

export function currentPath(): string {
  const raw = window.location.hash.replace(/^#/, '');
  if (!raw || !raw.startsWith('/')) return DEFAULT_ROUTE;
  return raw;
}

export function navigate(path: string): void {
  if (currentPath() === path) return;
  window.location.hash = path;
}

export function useRoutePath(): string {
  const [path, setPath] = useState<string>(() => currentPath());

  useEffect(() => {
    const onChange = () => setPath(currentPath());
    window.addEventListener('hashchange', onChange);
    return () => window.removeEventListener('hashchange', onChange);
  }, []);

  return path;
}

/** Splits `/live/abc123` into `['live', 'abc123']`. */
export function segments(path: string): string[] {
  return path.split('/').filter((part) => part.length > 0);
}

interface LinkProps extends Omit<AnchorHTMLAttributes<HTMLAnchorElement>, 'href'> {
  to: string;
  children: ReactNode;
}

export function Link({ to, children, ...rest }: LinkProps) {
  return (
    <a href={`#${to}`} {...rest}>
      {children}
    </a>
  );
}
