import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * shadcn/ui 의 표준 헬퍼. clsx 로 조건부 클래스를 합치고
 * tailwind-merge 로 Tailwind 클래스 충돌을 해소.
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
