import type { ReactNode } from "react";

interface CardProps {
  children: ReactNode;
  borderColor?: string;
  className?: string;
}

export function Card({ children, borderColor, className = "" }: CardProps) {
  return (
    <div
      className={`bg-surface rounded-lg shadow p-4 ${borderColor ? `border-l-4 ${borderColor}` : ""} ${className}`}
    >
      {children}
    </div>
  );
}
