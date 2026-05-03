import { classNames } from '@/services/string';

export type ButtonSize = 'sm' | 'md' | 'lg';
export type ButtonColorSchema = 'primary' | 'secondary' | 'styled';

const sizes: Record<ButtonSize, string> = {
  sm: 'px-2.5 py-1.5 text-xs min-h-8',
  md: 'px-3.5 py-2 text-sm min-h-10',
  lg: 'px-4 py-3 text-base min-h-12',
};

const colorSchemas: Record<ButtonColorSchema, string> = {
  primary: 'bg-ink text-cream hover:bg-ink/90',
  secondary: 'border border-input bg-background hover:bg-accent hover:text-accent-foreground text-foreground',
  styled: '',
};

const ariaStyles =
  'focus:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2';

const layoutStyles =
  'rounded-md font-medium transition-all duration-200 flex flex-row gap-2 items-center justify-center disabled:opacity-50 disabled:pointer-events-none';

export interface MergeButtonClassesOptions {
  className?: string;
  size?: ButtonSize;
  colorSchema?: ButtonColorSchema;
}

export const mergeButtonClasses = ({
  className = '',
  size = 'md',
  colorSchema = 'primary',
}: MergeButtonClassesOptions): string =>
  classNames(className, ariaStyles, layoutStyles, sizes[size], colorSchemas[colorSchema]);
