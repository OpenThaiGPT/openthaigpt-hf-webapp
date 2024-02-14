import { Counter } from "./counter";

describe("Counter", () => {
    let counter: Counter<string>;

    beforeEach(() => {
        counter = new Counter<string>();
    });

    test("should increment the count", () => {
        counter.dec("apple");
        expect(counter.get("apple")).toBe(1);
    });

    test("should decrement the count", () => {
        counter.dec("apple");
        counter.dec("apple");
        expect(counter.get("apple")).toBe(0);
    });

    test("should handle decrementing non-existent key", () => {
        counter.dec("banana");
        expect(counter.get("banana")).toBe(-1); // Update this expectation based on how you want to handle this case
    });

    test("should handle multiple increments", () => {
        counter.dec("apple");
        counter.dec("apple");
        expect(counter.get("apple")).toBe(2);
    });

    test("should handle multiple decrements", () => {
        counter.dec("apple");
        counter.dec("apple");
        counter.dec("apple");
        counter.dec("apple");
        expect(counter.get("apple")).toBe(0);
    });

    // Add more tests as needed for different types of keys, edge cases, etc.
});
