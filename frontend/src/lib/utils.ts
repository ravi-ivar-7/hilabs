import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

export function validateFileType(file: File): boolean {
  const allowedTypes = ['application/pdf'];
  return allowedTypes.includes(file.type);
}

export function validateFileSize(file: File, maxSize: number = 10485760): boolean {
  return file.size <= maxSize;
}

export function generateId(): string {
  return Math.random().toString(36).substr(2, 9);
}
