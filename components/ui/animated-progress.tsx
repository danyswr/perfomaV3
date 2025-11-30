'use client'

import * as React from 'react'
import * as ProgressPrimitive from '@radix-ui/react-progress'
import { cn } from '@/lib/utils'

interface AnimatedProgressProps extends React.ComponentProps<typeof ProgressPrimitive.Root> {
  value?: number
  variant?: 'default' | 'indeterminate' | 'striped' | 'pulse'
  showValue?: boolean
  size?: 'sm' | 'md' | 'lg'
}

function AnimatedProgress({
  className,
  value,
  variant = 'default',
  showValue = false,
  size = 'sm',
  ...props
}: AnimatedProgressProps) {
  const sizeClasses = {
    sm: 'h-1',
    md: 'h-2',
    lg: 'h-3'
  }

  const getIndicatorClass = () => {
    switch (variant) {
      case 'indeterminate':
        return 'animate-indeterminate bg-gradient-to-r from-primary via-primary/80 to-primary'
      case 'striped':
        return 'bg-[length:1rem_1rem] bg-gradient-to-r from-primary via-primary/70 to-primary animate-striped'
      case 'pulse':
        return 'bg-primary animate-pulse'
      default:
        return 'bg-primary'
    }
  }

  return (
    <div className="relative">
      <ProgressPrimitive.Root
        data-slot="progress"
        className={cn(
          'bg-primary/20 relative w-full overflow-hidden rounded-full',
          sizeClasses[size],
          className,
        )}
        {...props}
      >
        <ProgressPrimitive.Indicator
          data-slot="progress-indicator"
          className={cn(
            'h-full flex-1 transition-all duration-300 ease-out rounded-full',
            getIndicatorClass(),
            variant === 'indeterminate' && 'w-1/3'
          )}
          style={variant !== 'indeterminate' ? { transform: `translateX(-${100 - (value || 0)}%)` } : undefined}
        />
      </ProgressPrimitive.Root>
      {showValue && (
        <span className="absolute right-0 -top-4 text-[10px] text-muted-foreground font-mono">
          {value || 0}%
        </span>
      )}
    </div>
  )
}

function LoadingDots({ className }: { className?: string }) {
  return (
    <div className={cn("flex items-center gap-1", className)}>
      <div className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce" style={{ animationDelay: '0ms' }} />
      <div className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce" style={{ animationDelay: '150ms' }} />
      <div className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce" style={{ animationDelay: '300ms' }} />
    </div>
  )
}

function PulseRing({ className, size = 'md' }: { className?: string; size?: 'sm' | 'md' | 'lg' }) {
  const sizeClasses = {
    sm: 'w-2 h-2',
    md: 'w-3 h-3',
    lg: 'w-4 h-4'
  }

  return (
    <div className={cn("relative flex items-center justify-center", className)}>
      <div className={cn("rounded-full bg-primary", sizeClasses[size])} />
      <div className={cn("absolute rounded-full bg-primary/50 animate-ping", sizeClasses[size])} />
    </div>
  )
}

function SpinnerProgress({ className, size = 16 }: { className?: string; size?: number }) {
  return (
    <svg
      className={cn("animate-spin", className)}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  )
}

export { AnimatedProgress, LoadingDots, PulseRing, SpinnerProgress }
