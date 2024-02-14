import { routePrefix } from "@/lib/state";
import assert from "../assert";
import Future from "../future";
import { host, wsPtcl } from "../host";
import { APayload, FPayload, GWSConn, ITypedWebSocket, IWebSocketConnection, TypedWebSocket, WSConn } from "./connection";


type ClientOpenConnection = FPayload<"open"> & {
    channel: string,
}
type ServerAcceptOpenConnection = FPayload<"open"> & {
    channel: string,
    session: string,
}
type CloseConnection = APayload<"close"> & {
    session: string,
    code: number
}
type MulitplexedPayload<MSG> = APayload<"msg"> & {
    session: string,
    msg: MSG
}

type FetchRequest = ClientOpenConnection;
type FetchResponse = ServerAcceptOpenConnection;
type AsyncRequest<MSG> = CloseConnection | MulitplexedPayload<MSG>;
type AsyncResponse<MSG> = CloseConnection | MulitplexedPayload<MSG>;


export type WSMuxConn<REQ, RES> = WSConn<FetchRequest, FetchResponse, AsyncRequest<REQ>, AsyncResponse<RES>>;

// Generic WebSocket Connection
type GWSMuxConn = WSMuxConn<any, any>


export class TypedVirutalWebSocket<WSC extends GWSConn> implements ITypedWebSocket<WSC> {
    public readyState: number = WebSocket.CONNECTING;
    public session: string | null = null;
    // public closed: boolean = true;
    public pendingFetch: {
        [key in string]?: Future<WSC["fetch"]["response"]>
    } = {};
    private fetchCount = 0;

    constructor(
        public ws: ITypedWebSocket<WSMuxConn<
            WSC["fetch"]["request"] | WSC["async"]["request"],
            WSC["fetch"]["response"] | WSC["async"]["response"]
        >> | null) { }

    sendAsyncRequest(request: WSC["async"]["request"]) {
        assert(this.ws !== null && this.session !== null, "`ws` and `session` must not be null");
        this.ws.sendAsyncRequest({
            p: "A",
            session: this.session,
            type: "msg",
            msg: request,
        });
    }

    /**
     * fetch a request
     * @param request request to send
     * @returns promose that is resolve once the response of the request was received
     */
    fetch(request: WSC["fetch"]["request"]): Promise<WSC["fetch"]["response"]> {
        assert(request.id === undefined, "fetch id is assigned by `fetch`");
        request.id = `${this.fetchCount++}`;

        const future = new Future<WSC["fetch"]["response"]>();
        this.pendingFetch[request.type] = future;

        assert(this.ws !== null && this.session !== null,
            "`ws` and `session` must not be null");
        this.ws.sendAsyncRequest({
            p: "A",
            session: this.session,
            type: "msg",
            msg: request,
        });
        return future.promise;
    }

    close(code: number) {
        // TODO test this code path
        assert(this.ws !== null && this.session !== null, "session can't be null on close state");
        this.ws.sendAsyncRequest({
            p: "A",
            type: "close",
            session: this.session,
            code: code
        });
        this.readyState = WebSocket.CLOSED;
    }
}

type PendingVS = { req: FetchRequest, vs: TypedVirutalWebSocket<any>, hook: IWebSocketConnection<any> };

/**
 * `WSMultiplexer` is a layer which allows multiple `IWebSocketConnection`
 * to use the same `TypedWebSocket` by introducing channels.
 */
export class WSMultiplexer implements IWebSocketConnection<GWSMuxConn> {
    protected ws: ITypedWebSocket<GWSMuxConn> | null = null;
    private hooksNSockets: {
        [session in string]: {
            hook: IWebSocketConnection<GWSConn>
            vsocket: TypedVirutalWebSocket<any>
        }
    } = {};
    private pendingVSConnect: PendingVS[] = [];
    private connectionBackOff: number = 1000;
    private consoleTimer: boolean;
    constructor() {
        // establish new WebSocket connection
        this.ws = TypedWebSocket.createConnection(this, this.getUrl());

        console.time("ws-mux: open");
        this.consoleTimer = true;
    }

    private getUrl(): string {
        return wsPtcl + host + routePrefix + "/api/ws-connect";
    }

    /**
     * Register a virtual socket with server
     * 
     * @param pendingVs pending virtual socket to connect
     */
    private registerVs(pendingVs: PendingVS) {
        assert(this.ws !== null, "ws must not be null when getting a open signal");
        pendingVs.vs.ws = this.ws;
        this.ws.fetch(pendingVs.req).then((opened) => {
            assert(opened.type === "open", "waited for fetch 'open' but did not get fetch for 'open'");
            pendingVs.vs.session = opened.session;
            this.hooksNSockets[opened.session] = {
                hook: pendingVs.hook,
                vsocket: pendingVs.vs,
            };
            pendingVs.vs.readyState = WebSocket.OPEN;
            pendingVs.hook.onopen({} as Event);
        });
    }

    /**
     * Connect a hook to multiplexer on a channel.
     * 
     * If connection is not active, the virtual web sockets are queued up for connection.
     * 
     * @param hook `IWebScoketConnection` to connect
     * @param channel channel name to connect to
     * @returns `TypedVirutalWebSocket`
     */
    connectVirtualConnection<WSC extends WSConn<any, any, any, any>>(
        hook: IWebSocketConnection<WSC>,
        channel: string
    ): TypedVirutalWebSocket<WSC> {
        const vs = new TypedVirutalWebSocket<WSC>(this.ws);

        const pendingVs: PendingVS = {
            req: { p: "F", type: "open", channel },
            hook, vs,
        };
        if (this.ws !== null && this.ws.readyState === WebSocket.OPEN) {
            // if WebSocket connection is ready, start registering the virutal socket
            this.registerVs(pendingVs);
        } else {
            // else queue up the virutal socket as pending connection
            this.pendingVSConnect.push(pendingVs);
        }
        hook.oncreate(vs);
        return vs;
    }
    oncreate(ws: ITypedWebSocket<GWSMuxConn>): void {
        this.ws = ws;
    }
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    onopen(e: Event) {
        assert(this.ws !== null, "ws must not be null when getting a open signal");
        console.timeEnd("ws-mux: open");
        this.consoleTimer = false;

        // connect any pending virtual socket connection
        for (const pendingVs of this.pendingVSConnect) {
            this.registerVs(pendingVs);
        }
        // clear pending VS connect
        this.pendingVSConnect.length = 0;
    }
    async onresponse(r: GWSMuxConn["fetch"]["response"] | GWSMuxConn["async"]["response"]): Promise<void> {
        const { hook, vsocket } = this.hooksNSockets[r.session];
        if (r.type === "close") {
            assert(r.p === "A", "expect msg to be Async");
            hook.onclose(new CloseEvent("close", { code: r.code }));
        } else if (r.type === "msg") {
            assert(r.p === "A", "MulitplexedPayload expect msg to be Async");
            if (r.msg.p === "F") {
                vsocket.pendingFetch[r.msg.type].resolve(r.msg);
            } else if (r.msg.p === "A") {
                hook.onresponse(r.msg);
            } else {
                assert(false, "message in MulitplexedPayload must be either fetch or async");
            }
        } else {
            assert(false, "unbound");
        }
    }
    onclose(event: CloseEvent) {
        if (this.consoleTimer) {
            console.timeEnd("ws-mux: open");
        }
        // TODO close all hooks
        this.ws = null;
        if (event.code === 1000) {
            // regular close
            console.log(`ws Disconnected: regular close: ${event.reason}`);
        } else if (event.code === 1006 || event.code === 1012) {
            console.log(`ws Disconnected: can't connect to sever ${event.reason}`);
            setTimeout(() => {
                console.time("ws-mux: open");
                this.consoleTimer = true;
                this.ws = TypedWebSocket.createConnection(this, this.getUrl());
                if (this.connectionBackOff < 5000) {
                    this.connectionBackOff *= 2;
                }
            }, this.connectionBackOff);
        } else if (event.code >= 4100 && event.code < 5000) {
            // close from user error
            console.log(`ws Disconnected: close from user error: ${event.reason}`);
        } else {
            // close from system error
            console.log(`ws Disconnected: close from system error: ${event.reason}`);
        }
    }
}