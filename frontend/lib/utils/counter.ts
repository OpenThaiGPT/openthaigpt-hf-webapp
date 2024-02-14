export class Counter<T> extends Map<T, number> {
    public inc(key: T): number {
        const count = this.get(key) || 0;
        this.set(key, count + 1);
        return count + 1;
    }

    public dec(key: T): number {
        const count = this.get(key) || 0;
        this.set(key, count - 1);
        return count - 1;
    }
}
