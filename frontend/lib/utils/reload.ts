export class HotReloader {
    private static instance: HotReloader = new HotReloader();
    public static install(module: NodeModule, hook: null | (() => void) = null): void {
        if (module.hot) {
            if (hook !== null) {
                // console.log("Hot reloader hooked");
                HotReloader.instance.hook = hook;
            }
            module.hot.accept(function () {
                if (HotReloader.instance.hook === null) {
                    console.log("Cannot hot-reload, hook is `null`");
                    return;
                }
                HotReloader.instance.hook();
            });
        }

    }

    private hook: null | (() => void);
    constructor() { }
}
