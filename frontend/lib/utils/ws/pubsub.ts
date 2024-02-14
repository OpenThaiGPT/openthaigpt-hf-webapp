import assert from "../assert";
import { APayload, ITypedWebSocket, WSConn } from "./connection";

export type Channel = string;

export type SubscriptionAReq = APayload<"sub" | "unsub"> & {
    channel: Channel;
}; export type SubscriptionARes = APayload<"sub"> & {
    channel: Channel;
    data: any;
};

type Callback<T> = (data: T) => void


type PSConn = WSConn<any, any, SubscriptionAReq, SubscriptionARes>

export class PubSub<TVWS extends PSConn> {
    private id2Callback = new Map<number, [Channel, Callback<any>]>();
    private ch2Callbacks = new Map<Channel, Callback<any>[]>();
    private chCache = new Map<Channel, any>();
    private pendingSubReq: Channel[] | null = [];
    private vs: ITypedWebSocket<TVWS> | null = null;
    private idCounter: number = 0;

    onconnect(vs: ITypedWebSocket<TVWS>) {
        assert(this.pendingSubReq instanceof Array, "onconnect can only be called once");
        this.vs = vs;
        for (const channel of this.pendingSubReq) {
            this.vs.sendAsyncRequest({ p: "A", type: "sub", channel });
        }
        this.pendingSubReq = null;
    }

    sub(channel: Channel, callback: Callback<any>): number {
        this.id2Callback.set(this.idCounter, [channel, callback]);
        let callbacks = this.ch2Callbacks.get(channel);
        if (callbacks === undefined) {
            callbacks = [];
            this.ch2Callbacks.set(channel, callbacks);
            if (this.vs === null) {
                this.pendingSubReq.push(channel);
            } else {
                this.vs.sendAsyncRequest({ p: "A", type: "sub", channel });
            }
        } else {
            const data = this.chCache.get(channel);
            if (data !== undefined) {
                setImmediate(() => callback(data));
            }
        }
        callbacks.push(callback);
        return this.idCounter++;
    }

    unsub(subId: number): void {
        const [channel, callback] = this.id2Callback.get(subId);
        this.id2Callback.delete(subId);
        const callbacks = this.ch2Callbacks.get(channel);
        callbacks.splice(callbacks.indexOf(callback), 1);
        if (callbacks.length === 0) {
            this.ch2Callbacks.delete(channel);
            if (this.vs === null) {
                // NOTE: if this.vs is null, then we have not connected, yet.
                // TODO: properly handle disconnection, now we assuem that
                //       `this.vs` is `null` for before we establish a connection.
                //       `this.vs` should also be `null` when we disconnect, but we
                //       do not have `ondisconnect`.
                const idx = this.pendingSubReq.indexOf(channel);
                assert(idx !== -1, "a pending sub request must exist, since we have not established a connection, yet.");
                this.pendingSubReq.splice(idx, 1);
            } else {
                this.vs.sendAsyncRequest({ p: "A", type: "unsub", channel });
            }
        }
    }

    handleReponse(r: APayload<string>): boolean {
        if (r.type === "sub") {
            const res = r as SubscriptionARes;
            for (const cb of this.ch2Callbacks.get(res.channel) || []) {
                cb(res.data);
            }
            this.chCache.set(res.channel, res.data);
            return true;
        }
    }
}
