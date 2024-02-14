import assert from "./utils/assert";

export const routePrefix = process.env.ROUTE_PREFIX;
export const pagePrefix = routePrefix + process.env.PAGE_PREFIX;
export const pagePrefixWoTrailingSlash = pagePrefix.slice(0, pagePrefix.length - 1);
assert(pagePrefix.endsWith("/"), "PAGE_PREFIX must end with '/'");


export type AppStateDataset = {
    menu: "dataset",
    dataset?: string,
    split?: string,
    page?: number,
    entry?: string,
}

export type AppStateAnnotation = {
    menu: "annotation",
    dataset: string,
    split: string,
    entry: string,
    leaf?: string,
}

export type AppStateAssignedAnno = {
    menu: "assigned-annotation",
}

export type AppState = { menu: "" } | AppStateDataset | AppStateAssignedAnno | AppStateAnnotation;

function encodeAppState(state: AppState): string {
    let path: string = "/editor";
    if (state.menu === "dataset") {
        path += "/dataset";
        if (state.dataset !== undefined) {
            path += `/${state.dataset}`;
        }
        if (state.split !== undefined) {
            path += `/${state.split}`;
        }
        if (state.entry !== undefined) {
            path += `/${state.entry}`;
        }
    } else if (state.menu === "annotation") {
        path += `/annotation/${state.dataset}/${state.split}/${state.entry}`;
        if (state.leaf !== undefined) {
            path += `/${state.leaf}`;
        }
    } else if (state.menu === "assigned-annotation") {
        path += "/assigned-annotation";
    }
    return pagePrefixWoTrailingSlash + path;
}

function decodeAppStateFromRawUrl(rawUrl: string): AppState {
    assert(rawUrl.startsWith(pagePrefix), "expect raw url to begin with route prefix");
    const url = rawUrl.slice(pagePrefix.length - 1);
    const pathSegments = url.split("/").filter(segment => segment.length > 0);
    if (pathSegments.length === 0 || pathSegments[0] !== "editor") {
        throw Error("unknown url");
    }
    // NOTE: slice(1) to remove first segment which is always "editor"
    return decodeAppStateFromRouteSeg(pathSegments.slice(1));
}

export function decodeAppStateFromRouteSeg(routeSeg: string[]): AppState {
    if (routeSeg.length > 0) {
        switch (routeSeg[0]) {
        case "dataset": {
            const state: AppState = { menu: "dataset" };
            if (routeSeg[1] !== undefined) {
                state.dataset = routeSeg[1];
            }
            if (routeSeg[2] !== undefined) {
                state.split = routeSeg[2];
            }

            if (routeSeg[3] === "p" && routeSeg[4] !== undefined) {
                state.page = parseInt(routeSeg[4].slice(2));
            }
            else if (routeSeg[3] === "e" && routeSeg[4] !== undefined) {
                state.entry = routeSeg[4];
            }

            return state;
        }
        case "assigned-annotation": {
            return { menu: "assigned-annotation" };
        }
        default:
            throw Error("unknown route");
        }
    }
    return {
        menu: "",
    };
}

console.log("initial pathname", window.location.pathname);

export const appState: {
    current: AppState
    onChange: () => void | null
} = {
    current: decodeAppStateFromRawUrl(window.location.pathname),
    onChange: null
};
/**
 * check if new state has changed from current state
 * @param newState check newState is different
 * @returns dis state changed
 */
function didStateChange(newState: AppState): boolean {
    for (const field of Object.keys(appState.current)) {
        if (appState.current[field] !== newState[field]) {
            return true;
        }
    }
    for (const field of Object.keys(newState)) {
        if (appState.current[field] !== newState[field]) {
            return true;
        }
    }
    return false;
}

function handleAppStateChange(newState: AppState) {
    appState.current = newState;
    if (appState.onChange === null) {
        console.log("'popstate' event: Cannot pass AppState, onChange is `null`");
    } else {
        appState.onChange();
    }
}

window.addEventListener("popstate", (event) => {
    let newState = event.state;
    if (newState === null) {
        newState = decodeAppStateFromRawUrl(window.location.pathname);
    }
    console.log("pop state", newState);
    if (!didStateChange(newState)) {
        console.log("same state, no update.");
        return;
    }
    handleAppStateChange(newState);
});

export function pushAppRawUrl(rawUrl: string) {
    if (rawUrl === window.location.pathname) {
        console.log("same url, no update.");
        return;
    }
    const newState = decodeAppStateFromRawUrl(rawUrl);
    console.log("push route rawUrl", rawUrl);
    history.pushState(newState, "", rawUrl);
    handleAppStateChange(newState);
}

export function pushAppUrl(url: string) {
    assert(url.startsWith("/"), "url must be absolute");
    pushAppRawUrl(pagePrefixWoTrailingSlash + url);
}

export function pushAppState(newState: AppState) {
    if (!didStateChange(newState)) {
        console.log("same state, no update.");
        return;
    }
    console.log("push state", newState);
    history.pushState(newState, "", encodeAppState(newState));
    handleAppStateChange(newState);
}