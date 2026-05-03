import { useCallback, useState } from 'react';

export function useSidebarExpanded(initial = false) {
  const [expanded, setExpanded] = useState(initial);
  const toggle = useCallback(() => setExpanded((v) => !v), []);
  return { expanded, setExpanded, toggle };
}
