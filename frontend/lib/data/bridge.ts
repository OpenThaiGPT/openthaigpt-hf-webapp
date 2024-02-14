import assert from "../utils/assert";
import { FPayload, ITypedWebSocket, IWebSocketConnection, WSConn } from "../utils/ws/connection";
import { Channel, PubSub, SubscriptionAReq, SubscriptionARes } from "../utils/ws/pubsub";
import { DB_ResponseCmp } from "./model/cmp";


export type WhoAmIReq = FPayload<"whoami">
export type WhoAmIRes = FPayload<"whoami"> & {
    uname: string
}

export type AnnoRef = {
    dataset: string
    split: string
    entry: string
    idx: number
    cmpId: string | null
}
export type AssignedAnnoReq = FPayload<"assigned-anno"> & {
    ref: AnnoRef | null
}
export type AssignedAnnoRes = FPayload<"assigned-anno"> & {
    ref: AnnoRef
    count: number
    total: number
    a: string
    b: string
}
export type AnnoCmpReq = FPayload<"anno-cmp"> & {
    ref: AnnoRef
    cmp: DB_ResponseCmp
}
export type AnnoCmpRes = FPayload<"anno-cmp"> & {
    ok: boolean
}

type FetchReqPayload = WhoAmIReq | AssignedAnnoReq | AnnoCmpReq;
type FetchResPayload = WhoAmIRes | AssignedAnnoRes | AnnoCmpRes;
type AsyncReqPayload = SubscriptionAReq;
type AsyncResPayload = SubscriptionARes;

export type DBConn = WSConn<FetchReqPayload, FetchResPayload, AsyncReqPayload, AsyncResPayload>

export type Item = {
    id: string
    title: string | null
    caption: string | null
    description: string
    pending: boolean
    labels: string[]
    channel: string
}

export class DataBridge implements IWebSocketConnection<DBConn> {
    private ws: ITypedWebSocket<DBConn>;
    private ready: boolean = false;
    private onready: (() => Promise<void>)[] = [];
    private pubSub: PubSub<DBConn> = new PubSub();
    public uname: string;

    oncreate(ws: ITypedWebSocket<DBConn>) {
        this.ws = ws;
    }

    addOnReady(onready: () => Promise<void>) {
        if (this.ready) {
            onready();
        } else {
            this.onready.push(onready);
        }
    }

    onopen(_e: Event) {
        console.log("DB connected");
        this.pubSub.onconnect(this.ws);
        this.ws.fetch({ p: "F", type: "whoami" }).then((res) => {
            console.log("DB ready");
            assert(res.type === "whoami", "reponse must match request");
            this.uname = res.uname;
            const onready = this.onready;
            this.ready = true;
            this.onready = [];
            for (const cb of onready) {
                cb();
            }
        });
    }

    hookSetter(channel: Channel, setter: (data: any) => void): number {
        return this.pubSub.sub(channel, setter);
    }

    unhookSetter(hookId: number): void {
        this.pubSub.unsub(hookId);
    }

    async reqAssignedAnno(ref: AnnoRef | null) {
        const req: AssignedAnnoReq = {
            p: "F",
            type: "assigned-anno",
            ref,
        };
        return this.ws.fetch(req);
    }

    async annotate_cmp(ref: AnnoRef, cmp: DB_ResponseCmp) {
        const req: AnnoCmpReq = {
            p: "F",
            type: "anno-cmp",
            ref,
            cmp,
        };
        return this.ws.fetch(req);
    }

    async onresponse(r: AsyncResPayload) {
        if (this.pubSub.handleReponse(r)) {
            return;
        }
        console.log("DB response", r);
    }
    onclose(e: CloseEvent) {
        if (e.reason === "not logged in") {
            console.log("cannot connect, not logged in");
        }
        console.log("DB closed");
    }
}
export const G_dataBridge = new DataBridge();