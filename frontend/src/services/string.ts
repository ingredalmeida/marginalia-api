export const classNames = (...classes: (string | undefined | null | false)[]) =>
  classes.filter(Boolean).join(' ');

export const joinStrings = (strings: string[]) =>
  strings.reduce(
    (previous, current, index) => `${previous}${index > 0 ? ` ${current}` : current}`,
    '',
  );
