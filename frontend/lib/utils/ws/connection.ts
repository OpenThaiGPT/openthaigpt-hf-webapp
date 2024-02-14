import assert from "../assert";
import Future from "../future";

export type FPayload<T2 extends string> = {
    p: "F"
    id?: string
    type: T2
}
export type APayload<T2 extends string> = {
    p: "A"
    type: T2
}

interface IFPayload<T2 extends string> {
    p: "F"
    id?: string
    type: T2
}
interface IAPayload<T2 extends string> {
    p: "A"
    type: T2
}


export type FakeFPayload = FPayload<"fake">
export type FakeAPayload = APayload<"fake">

export type WSConn<FQ extends IFPayload<string>, FS extends IFPayload<string>, AQ extends IAPayload<string>, AS extends IAPayload<string>> = {
    fetch: {
        request: FQ,
        response: FS,
    },
    async: {
        request: AQ,
        response: AS,
    }
}

// General WebSocket Connect
export type GWSConn = WSConn<IFPayload<string>, IFPayload<string>, IAPayload<string>, IAPayload<string>>;

/**
 * TypedWebSocket is a wrapper for WebSocket
 * providing
 *  1. Typing information
 *  2. Distinction between
 *     * fetch requests (request-response managed by TypedWebSocket)
 *     * aysnc requests (raw WebSocket messages)
 */

export interface ITypedWebSocket<WSC extends GWSConn> {
    readonly readyState: number;
    sendAsyncRequest(request: WSC["async"]["request"]): void;
    fetch(request: WSC["fetch"]["request"]): Promise<WSC["fetch"]["response"]>;
}

export class TypedWebSocket<WSC extends GWSConn> extends WebSocket implements ITypedWebSocket<WSC> {
    private pendingFetch: {
        [key in string]?: Future<WSC["fetch"]["response"]>
    } = {};

    private fetchCount = 0;

    static createConnection<WSC extends GWSConn>(
        hook: IWebSocketConnection<WSC>,
        url: string
    ): TypedWebSocket<WSC> {
        const ws = new TypedWebSocket<WSC>(url);
        ws.onopen = hook.onopen.bind(hook);
        ws.onmessage = (e: MessageEvent<string>) => {
            if (e.data === "not logged in") {
                throw new Error("not logged in");
            }
            const res = JSON.parse(e.data);
            const fetchName = `${res.type}-${res.id}`;
            // handle ws response by multiplexing to other handler
            const fetchFuture = ws.pendingFetch[fetchName];
            if (fetchFuture === undefined) {
                hook.onresponse.bind(hook)(res);
            }
            else {
                delete ws.pendingFetch[fetchName];
                fetchFuture.resolve(res);
                console.timeEnd(fetchName);
            }
        };
        ws.onclose = hook.onclose.bind(hook);
        hook.oncreate(ws);
        return ws;
    }

    sendAsyncRequest(request: WSC["async"]["request"]) {
        this.send(JSON.stringify(request));
    }

    /**
     * fetch a request
     * @param request request to send
     * @returns promose that is resolve once the response of the request was received
     */
    fetch(request: WSC["fetch"]["request"]): Promise<WSC["fetch"]["response"]> {
        assert(request.id === undefined, "fetch id is assigned by `fetch`");
        request.id = `${this.fetchCount++}`;

        const fetchName = `${request.type}-${request.id}`;
        let future = this.pendingFetch[fetchName];
        console.time(fetchName);

        if (future === undefined) {
            future = new Future<WSC["fetch"]["response"]>();
            this.pendingFetch[fetchName] = future;
            this.send(JSON.stringify(request));
        }
        return future.promise;
    }
}

/**
 * `IWebSocketConnection` describe an interface which can connect with a `TypedWebSocket` or `TypedVirutalWebSocket`
 * 
 * see `connectWebSocket` for more details
 */
export interface IWebSocketConnection<WSC extends GWSConn> {
    oncreate: (ws: ITypedWebSocket<WSC>) => void;
    onopen: (e: Event) => void;
    onresponse: (r: WSC["async"]["response"]) => Promise<void>;
    onclose: (e: CloseEvent) => void;
}

// /**
//  * create a web socket connection and bind a hook to it
//  * 
//  * @param hook IWebSocketConnection to bind WebSocket connection to
//  * @param url WebSocket endpoint
//  * @returns typed WebSocket connection
//  */
// export function connectWebSocket<
//     WSC extends GWSConn,
// >(
//     hook: IWebSocketConnection<WSC>,
//     url: string
// ) {
//     const ws = new TypedWebSocket<WSC>(url);
//     ws.onopen = hook.onopen.bind(hook);
//     ws.onmessage = (e: MessageEvent<string>) => {
//         const res = JSON.parse(e.data);
//         // handle ws response by multiplexing to other handler
//         const fetchFuture = ws.pendingFetch[res.type];
//         if (fetchFuture === undefined) {
//             hook.onresponse.bind(hook)(res);
//         }
//         else {
//             delete ws.pendingFetch[res.id];
//             fetchFuture.resolve(res);
//         }
//     };
//     ws.onclose = hook.onclose.bind(hook);
//     return ws;
// }