function getHost(): string {
    if (process.env.REACT_APP_WS_HOST !== undefined) {
        return process.env.REACT_APP_WS_HOST;
    } else {
        return window.location.host;
    }
}

function getWsProtocol(): string {
    if (location.protocol === "https:") {
        return "wss://";
    } else {
        return "ws://";
    }
}

export const host = getHost();
export const wsPtcl = getWsProtocol();