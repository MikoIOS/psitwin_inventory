import type { ReactNode } from 'react'
import { Link, type LinkProps } from 'react-router'
import { buttonClasses, type ButtonSize, type ButtonVariant } from './Button'
import { Icon, type IconName } from './Icon'

export interface LinkButtonProps extends LinkProps {
  variant?: ButtonVariant
  size?: ButtonSize
  icon?: IconName
  iconRight?: IconName
  fullWidth?: boolean
  children?: ReactNode
}

/** Enlace de navegación con apariencia de botón (no anidar <Button> dentro de <Link>). */
export function LinkButton({ variant = 'secondary', size = 'md', icon, iconRight, fullWidth, className, children, ...rest }: LinkButtonProps) {
  return (
    <Link {...rest} className={buttonClasses({ variant, size, fullWidth, className: typeof className === 'string' ? className : undefined })}>
      {icon && <Icon name={icon} className="size-4" />}
      {children}
      {iconRight && <Icon name={iconRight} className="size-4" />}
    </Link>
  )
}
