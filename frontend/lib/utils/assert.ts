function assert(expression: boolean, message: string): asserts expression {
    if (!expression) {
        // eslint-disable-next-line no-debugger
        debugger;
        throw new Error(message);
    }
}

export default assert;