import type { ButtonHTMLAttributes, ReactNode, Ref } from 'react'
import { cn } from '@/lib/cn'
import { Icon, type IconName } from './Icon'
import { Spinner } from './Spinner'

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'subtle'
export type ButtonSize = 'sm' | 'md' | 'lg'

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
  /** Muestra spinner, deshabilita el botón y marca aria-busy. */
  loading?: boolean
  icon?: IconName
  iconRight?: IconName
  fullWidth?: boolean
  /** Solo icono: requiere `aria-label`. */
  iconOnly?: boolean
  ref?: Ref<HTMLButtonElement> | undefined
  children?: ReactNode
}

const VARIANTS: Record<ButtonVariant, string> = {
  primary:
    'bg-accent text-accent-fg hover:bg-accent-hover border border-[color-mix(in_srgb,var(--accent)_70%,black)] shadow-[inset_0_-2px_0_rgb(0_0_0/0.12)]',
  secondary: 'bg-surface text-fg border border-border-strong hover:bg-surface-2',
  ghost: 'bg-transparent text-fg-muted hover:bg-surface-2 hover:text-fg border border-transparent',
  subtle: 'bg-surface-2 text-fg hover:bg-surface-3 border border-transparent',
  danger: 'bg-danger text-white hover:bg-danger-hover border border-transparent',
}

const SIZES: Record<ButtonSize, string> = {
  sm: 'h-8 px-3 text-sm gap-1.5',
  md: 'h-10 px-4 text-sm gap-2',
  lg: 'h-12 px-5 text-base gap-2',
}

const ICON_ONLY: Record<ButtonSize, string> = {
  sm: 'h-8 w-8',
  md: 'h-10 w-10',
  lg: 'h-12 w-12',
}

/** Clases de botón reutilizables (ej. para <LinkButton> u otros elementos). */
export function buttonClasses(opts: { variant?: ButtonVariant; size?: ButtonSize; fullWidth?: boolean | undefined; iconOnly?: boolean | undefined; className?: string | undefined } = {}) {
  const { variant = 'primary', size = 'md', fullWidth, iconOnly, className } = opts
  return cn(
    'inline-flex shrink-0 items-center justify-center rounded-[var(--radius-ui)] font-medium whitespace-nowrap transition-colors select-none',
    'disabled:cursor-not-allowed disabled:opacity-55 aria-disabled:pointer-events-none aria-disabled:opacity-55',
    VARIANTS[variant],
    iconOnly ? ICON_ONLY[size] : SIZES[size],
    fullWidth && 'w-full',
    className,
  )
}

export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  icon,
  iconRight,
  fullWidth,
  iconOnly,
  className,
  children,
  disabled,
  type = 'button',
  ref,
  ...rest
}: ButtonProps) {
  return (
    <button
      ref={ref}
      type={type}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      className={buttonClasses({ variant, size, fullWidth, iconOnly, className })}
      {...rest}
    >
      {loading ? <Spinner size="sm" /> : icon ? <Icon name={icon} className="size-4" /> : null}
      {!iconOnly && children}
      {iconRight && !loading && <Icon name={iconRight} className="size-4" />}
    </button>
  )
}
