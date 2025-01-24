import * as React from "react";

import { cn } from "@/lib/utils";

/**
 * Props for the Input component
 */
export interface InputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "onChange" | "value"> {
  value: number;
  onChange: (value: number) => void;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, value, onChange, ...props }, ref) => {
    /**
     * Handle change event for the input
     * @param event - React change event
     */
    const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = parseInt(event.target.value, 10);
      if (!isNaN(newValue)) {
        onChange(newValue);
      }
    };

    return (
      <input
        type="number"
        className={cn(
          "flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
          className
        )}
        value={value}
        onChange={handleChange}
        ref={ref}
        {...props}
      />
    );
  }
);
Input.displayName = "Input";

export { Input };