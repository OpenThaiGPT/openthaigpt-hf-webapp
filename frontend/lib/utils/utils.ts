import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

export function shallowArrayEqual(arr1: T[], arr2: T[]): boolean {
    // Check if the arrays have the same length
    if (arr1.length !== arr2.length) {
        return false;
    }

    // Iterate through the arrays and compare corresponding elements
    for (let i = 0; i < arr1.length; i++) {
        if (arr1[i] !== arr2[i]) {
            return false; // Return false as soon as a mismatch is found
        }
    }

    // If the loop completes without finding any mismatches, return true
    return true;
}