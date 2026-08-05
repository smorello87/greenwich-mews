const BASE = import.meta.env.BASE_URL;

const stripTrailing = (path: string) => path.replace(/\/+$/, '') || '/';

/** Prefix a site-root-relative path with the configured `base`. */
export function withBase(path: string): string {
  return `${BASE.replace(/\/+$/, '')}/${path.replace(/^\/+/, '')}`;
}

/** True when `pathname` points at `path`, ignoring trailing-slash differences. */
export function isCurrent(pathname: string, path: string): boolean {
  return stripTrailing(pathname) === stripTrailing(withBase(path));
}
