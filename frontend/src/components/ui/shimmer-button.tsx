import React from "react";
import { motion } from "framer-motion";
import { cn } from "../../lib/utils";

const animationProps = {
  initial: { "--x": "100%", scale: 0.8 } as any,
  animate: { "--x": "-100%", scale: 1 } as any,
  whileTap: { scale: 0.95 },
  transition: {
    repeat: Infinity,
    repeatType: "loop" as const,
    repeatDelay: 1,
    type: "spring" as const,
    stiffness: 20,
    damping: 15,
    mass: 2,
    scale: {
      type: "spring" as const,
      stiffness: 200,
      damping: 5,
      mass: 0.5,
    },
  },
};

interface ShimmerButtonProps {
  children?: React.ReactNode;
  className?: string;
  shimmerColor?: string;
  shimmerSize?: string;
  borderRadius?: string;
  shimmerDuration?: string;
  background?: string;
}

const ShimmerButton = React.forwardRef<HTMLButtonElement, ShimmerButtonProps>(
  (
    {
      children = "Shimmer Button",
      className = "",
      shimmerColor = "#ffffff",
      shimmerSize = "0.1em",
      shimmerDuration = "3s",
      borderRadius = "100px",
      background = "rgba(0, 0, 0, 1)",
      ...props
    },
    ref
  ) => {
    return (
      <motion.button
        style={
          {
            "--spread": "90deg",
            "--shimmer-color": shimmerColor,
            "--radius": borderRadius,
            "--speed": shimmerDuration,
            "--cut": shimmerSize,
            "--bg": background,
          } as React.CSSProperties
        }
        className={cn(
          "group relative z-0 flex cursor-pointer items-center justify-center overflow-hidden whitespace-nowrap border border-white/10 px-6 py-3 text-white [background:var(--bg)] [border-radius:var(--radius)] transition-all duration-300 hover:scale-105 active:scale-95",
          "before:absolute before:inset-0 before:overflow-hidden before:[background:linear-gradient(var(--spread),transparent_0%,var(--shimmer-color)_50%,transparent_100%)] before:[transform:translateX(var(--x))] before:transition-transform before:duration-[var(--speed)] before:content-['']",
          "after:absolute after:inset-0 after:[border-radius:var(--radius)] after:[box-shadow:0_0_0_1px_var(--shimmer-color)] after:opacity-0 after:transition-opacity after:duration-500 after:content-[''] group-hover:after:opacity-100",
          className
        )}
        ref={ref}
        {...animationProps}
        {...props}
      >
        <span className="relative z-10">{children}</span>
      </motion.button>
    );
  }
);

ShimmerButton.displayName = "ShimmerButton";

export default ShimmerButton;
