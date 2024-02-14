class Future<T> {

    public resolved: boolean;
    public promise: Promise<T>;
    // @ts-ignore: This is safe, see https://stackoverflow.com/questions/42118900/when-is-the-body-of-a-promise-executed
    private _resolve: ((arg0: T) => void);

    constructor() {
        this.resolved = false;
        this.promise = new Promise((resolve) => {
            this._resolve = resolve;
        });
    }

    resolve(arg0: T) {
        if (this.resolved) {
            throw new Error("future resolved twice");
        }
        this.resolved = true;
        this._resolve(arg0);
    }
}

export default Future;