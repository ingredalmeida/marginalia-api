import { useCallback, useState } from 'react';

import type { AdminFeedback } from '@/components/AdminFeedbackModal';

export function useAdminFeedback() {
  const [feedback, setFeedback] = useState<AdminFeedback | null>(null);
  const dismissFeedback = useCallback(() => setFeedback(null), []);
  return { feedback, setFeedback, dismissFeedback };
}
