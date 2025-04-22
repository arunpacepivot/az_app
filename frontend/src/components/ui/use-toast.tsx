'use client';

import React, { createContext, useContext, useState } from 'react';
import dynamic from 'next/dynamic';

export interface Toast {
  id: string;
  title?: string;
  description?: string;
  variant?: 'default' | 'destructive';
}

interface ToastContextType {
  toast: (props: Omit<Toast, 'id'>) => void;
  dismissToast: (id: string) => void;
  toasts: Toast[];
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

// Create a client-side only ToastContainer component
const ClientToastContainer = dynamic(
  () => Promise.resolve(() => {
    const { toasts, dismissToast } = useContext(ToastContext) || { toasts: [], dismissToast: () => {} };
    
    if (!toasts.length) return null;
    
    return (
      <div className="fixed bottom-0 right-0 z-50 p-4 space-y-4">
        {toasts.map((toast) => (
          <div 
            key={toast.id}
            className={`p-4 rounded-md shadow-md ${
              toast.variant === 'destructive' ? 'bg-red-500 text-white' : 'bg-white text-gray-900'
            }`}
          >
            {toast.title && <div className="font-semibold">{toast.title}</div>}
            {toast.description && <div>{toast.description}</div>}
            <button 
              onClick={() => dismissToast(toast.id)}
              className="absolute top-2 right-2 text-sm"
            >
              ×
            </button>
          </div>
        ))}
      </div>
    );
  }),
  { ssr: false } // This prevents the component from rendering on the server
);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const toast = (props: Omit<Toast, 'id'>) => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, ...props }]);
    
    // Auto dismiss after 5 seconds
    setTimeout(() => {
      dismissToast(id);
    }, 5000);
  };

  const dismissToast = (id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  };

  return (
    <ToastContext.Provider value={{ toast, dismissToast, toasts }}>
      {children}
      <ClientToastContainer />
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  
  return context;
} 