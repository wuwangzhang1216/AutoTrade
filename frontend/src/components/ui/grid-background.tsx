import React from "react";
import { cn } from "../../lib/utils";

export const GridBackground = ({
  children,
  className,
  containerClassName,
}: {
  children?: React.ReactNode;
  className?: string;
  containerClassName?: string;
}) => {
  return (
    <div className={cn("relative w-full h-full", containerClassName)}>
      <div className={cn("absolute inset-0", className)}>
        <div className="absolute inset-0 bg-gradient-to-br from-elite-950 via-black to-elite-990" />
        <div className="absolute inset-0 bg-grid-white/[0.02] bg-[size:50px_50px]" />
        <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent" />
      </div>
      <div className="relative z-10">{children}</div>
    </div>
  );
};
