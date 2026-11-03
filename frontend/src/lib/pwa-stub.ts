// Usato solo dalla build di anteprima, dove il service worker non esiste.
export function registerSW() { return () => Promise.resolve(); }
