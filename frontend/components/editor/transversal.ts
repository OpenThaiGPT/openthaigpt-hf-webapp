import { InstanceId } from "@/lib/data/model/abs";
import { AnyDialogueUnit, AnyUtterance } from "@/lib/data/model/any";
import { DB_ResponseCmp } from "@/lib/data/model/cmp";
import { SerializedEntry } from "@/lib/data/model/serial/entry";
import assert from "@/lib/utils/assert";

export type DialoguePath = InstanceId[];

type CmpData = DB_ResponseCmp[];

type DialogueNode = {
    unit: AnyDialogueUnit
    next: InstanceId[]
    cmps: CmpData
};

export class DialogueGraph {
    root: DialogueNode;
    nodes: Record<InstanceId, DialogueNode>;

    constructor(public entry: SerializedEntry) {
        this.root = {
            unit: entry.prompt,
            next: [],
            cmps: [],
        };

        this.nodes = {};
        this.nodes[entry.prompt.id] = this.root;

        for (const response of entry.utterance) {
            const node: DialogueNode = {
                unit: response,
                next: [],
                cmps: [],
            };
            this.nodes[response.id] = node;
            this.nodes[response.prev_id].next.push(response.id);
        }

        for (const cmp of entry.cmps) {
            const a_prev_id = (this.nodes[cmp.a].unit as AnyUtterance).prev_id;
            const b_prev_id = (this.nodes[cmp.b].unit as AnyUtterance).prev_id;
            assert(a_prev_id === b_prev_id, "comparison must be done with utterances of the same parent (prev_id).");
            this.nodes[a_prev_id].cmps.push(cmp);
        }
    }

    walk(guidePath: DialoguePath | null): DialoguePath {
        const path: DialoguePath = [this.root.unit.id];
        let node = this.root;
        if (guidePath === null) {
            guidePath = [this.root.unit.id];
        }
        assert(guidePath.length === 0 || node === this.nodes[guidePath[0]], "guild must always start with root node");
        for (let i = 1; i < guidePath.length; ++i) {
            const nodeId = guidePath[1];
            let found = false;
            for (const elem of node.next) {
                if (elem === nodeId) {
                    found = true;
                }
            }
            if (!found) {
                break;
            }
            path.push(nodeId);
            node = this.nodes[nodeId];
        }
        while (node.next.length > 0) {
            const nodeId = node.next[0];
            path.push(nodeId);
            node = this.nodes[nodeId];
        }
        return path;
    }
}

// export function walkSerializedEntry(entry: SerializedEntry): DialoguePath {
//     const path = [entry.prompt.id];

//     return path;
// }