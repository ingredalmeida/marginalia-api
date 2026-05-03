import { AlertCircle, CheckCircle2 } from 'lucide-react';

import Button from '@/components/Button';
import { classNames } from '@/services/string';

export type AdminFeedback = { type: 'success' | 'error'; message: string };

type AdminFeedbackModalProps = {
  feedback: AdminFeedback | null;
  onDismiss: () => void;
  idPrefix?: string;
};

const AdminFeedbackModal = ({ feedback, onDismiss, idPrefix = 'admin-feedback' }: AdminFeedbackModalProps) => {
  if (!feedback) {
    return null;
  }

  return (
    <div
      className='fixed inset-0 z-[60] flex items-center justify-center p-4 bg-ink/40'
      role='alertdialog'
      aria-labelledby={`${idPrefix}-title`}
      aria-describedby={`${idPrefix}-desc`}
    >
      <div
        className={classNames(
          'max-w-sm w-full rounded-2xl border p-6 shadow-book animate-fade-up bg-card',
          feedback.type === 'success' ? 'border-teal/25' : 'border-coral/25',
        )}
      >
        <div className='flex gap-4'>
          {feedback.type === 'success' ? (
            <CheckCircle2 className='w-10 h-10 text-teal shrink-0' aria-hidden />
          ) : (
            <AlertCircle className='w-10 h-10 text-coral shrink-0' aria-hidden />
          )}
          <div className='min-w-0'>
            <p id={`${idPrefix}-title`} className='font-serif text-lg text-ink mb-1'>
              {feedback.type === 'success' ? 'Tudo certo' : 'Algo deu errado'}
            </p>
            <p
              id={`${idPrefix}-desc`}
              className={classNames(
                'text-sm leading-relaxed',
                feedback.type === 'success' ? 'text-muted-foreground' : 'text-coral',
              )}
            >
              {feedback.message}
            </p>
          </div>
        </div>
        <Button type='button' colorSchema='primary' className='w-full mt-6 rounded-xl h-11' onClick={onDismiss}>
          OK
        </Button>
      </div>
    </div>
  );
};

export default AdminFeedbackModal;
