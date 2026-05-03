import React from 'react';
import { AiOutlineLoading3Quarters } from 'react-icons/ai';

import type { ButtonColorSchema, ButtonSize } from '@/services/buttonClasses';
import { mergeButtonClasses } from '@/services/buttonClasses';

export type { ButtonColorSchema, ButtonSize } from '@/services/buttonClasses';

export interface IButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  className?: string;
  size?: ButtonSize;
  colorSchema?: ButtonColorSchema;
  children: React.ReactNode;
  loading?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, IButtonProps>(
  (
    { children, className = '', size = 'md', colorSchema = 'primary', loading, disabled, type = 'button', ...rest },
    ref,
  ) => {
    return (
      <button
        ref={ref}
        type={type}
        disabled={loading || disabled}
        {...rest}
        className={mergeButtonClasses({ className, size, colorSchema })}
      >
        {loading && <AiOutlineLoading3Quarters className='animate-spin shrink-0' aria-hidden />}
        {children}
      </button>
    );
  },
);

Button.displayName = 'Button';

export default Button;
