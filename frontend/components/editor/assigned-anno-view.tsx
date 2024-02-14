import { AssignedAnnoRes, G_dataBridge } from "@/lib/data/bridge";
import { get_utt } from "@/lib/data/model/any";
import { SerializedEntry } from "@/lib/data/model/serial/entry";
import assert from "@/lib/utils/assert";
import { cn } from "@/lib/utils/utils";
import { useEffect, useState } from "react";
import { Button } from "../ui/button";
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from "../ui/resizable";
import { DialoguePreview } from "./dialogue-preview";
import { DialogueGraph, DialoguePath } from "./transversal";

const pleaseWait = <div className="p-3">Loading</div>;

interface AssignedAnnoProps {
    appState: { menu: "assigned-annotation" }
}

// function flattenAnnoRef(annoRef: AnnoRef) {
//     return `${annoRef.dataset}/${annoRef.split}/${annoRef.entry}/i:${annoRef.idx}`;
// }

/*
1. UI send request to get latest position & data
2. Render UI
3. User interact (changing position)
4. Get data for new poistion
5. Back to step 2
*/


export function AssignedAnno(_: AssignedAnnoProps) {
    const [response, setResponse] = useState<AssignedAnnoRes>(null);
    const [entryChannel, setEntryChannel] = useState(null);
    const [dialogueGraph, setDialogueGraph] = useState<DialogueGraph>(null);
    const [dialoguePath, setDialoguePath] = useState<DialoguePath>(null);

    const reload = () => {
        G_dataBridge.reqAssignedAnno(null).then((res) => {
            assert(res.type === "assigned-anno", "response must match request");
            setResponse(res);
            setEntryChannel(`entry/${res.ref.dataset}/${res.ref.split}/${res.ref.entry}`);
        });
    };

    useEffect(() => {
        G_dataBridge.addOnReady(async () => { reload(); });
    }, []);

    useEffect(() => {
        if (entryChannel !== null) {
            const hookId = G_dataBridge.hookSetter(entryChannel, (se: SerializedEntry) => {
                const dialogueGraph = new DialogueGraph(se);
                setDialogueGraph(dialogueGraph);
                // NOTE: currently hard-coded to only displaying root node
                // TODO: add support for annotating data beyond root node
                setDialoguePath([dialogueGraph.root.unit.id]);
            });
            return () => {
                G_dataBridge.unhookSetter(hookId);
                setDialogueGraph(null);
                setDialoguePath(null);
            };
        }
    }, [entryChannel]);

    let topLeftPanel = pleaseWait;
    let topRightPanel = pleaseWait;
    let bottomLeftPanel = pleaseWait;
    let bottomRightPanel = pleaseWait;

    if (response !== null) {
        const coverage = `${(response.count / response.total * 100).toFixed(1)}`;
        topRightPanel = <div className="flex flex-col justify-evenly gap-2 h-full">
            <div className="text-center">
                Coverage: {coverage}%
            </div>
            <div className="flex justify-evenly">
                <Button
                    variant="outline"
                    className={cn(
                        // link.state === "selected" &&
                        "dark:bg-muted dark:text-white dark:hover:bg-muted dark:hover:text-white",
                        "justify-start h-12 truncate",
                    )}
                    onClick={async () => {
                        const res = await G_dataBridge.annotate_cmp(response.ref, {
                            id: response.ref.cmpId,
                            cls: "cmp",
                            a: response.a,
                            b: response.b,
                            cmp: ">",
                            source: {
                                t: "user",
                                uname: G_dataBridge.uname,
                            },
                        });
                        console.log("res", res);
                        reload();
                    }}
                >
                    Prefer A
                </Button>
                <Button
                    variant="outline"
                    className={cn(
                        // link.state === "selected" &&
                        "dark:bg-muted dark:text-white dark:hover:bg-muted dark:hover:text-white",
                        "justify-start h-12 truncate",
                    )}
                    onClick={async () => {
                        const res = await G_dataBridge.annotate_cmp(response.ref, {
                            id: response.ref.cmpId,
                            cls: "cmp",
                            a: response.a,
                            b: response.b,
                            cmp: "=",
                            source: {
                                t: "user",
                                uname: G_dataBridge.uname,
                            },
                        });
                        console.log("res", res);
                        reload();
                    }}
                >
                    Equal
                </Button>
                <Button
                    variant="outline"
                    className={cn(
                        // link.state === "selected" &&
                        "dark:bg-muted dark:text-white dark:hover:bg-muted dark:hover:text-white",
                        "justify-start h-12 truncate",
                    )}
                    onClick={async () => {
                        const res = await G_dataBridge.annotate_cmp(response.ref, {
                            id: response.ref.cmpId,
                            cls: "cmp",
                            a: response.b,
                            b: response.a,
                            cmp: ">",
                            source: {
                                t: "user",
                                uname: G_dataBridge.uname,
                            },
                        });
                        console.log("res", res);
                        reload();
                    }}
                >
                    Prefer B
                </Button>
            </div>
        </div >;

        if (dialogueGraph !== null && dialoguePath !== null && dialogueGraph.nodes[response.a] !== undefined && dialogueGraph.nodes[response.b] !== undefined) {
            topLeftPanel = <DialoguePreview dialogueGraph={dialogueGraph} dialoguePath={dialoguePath} />;

            bottomLeftPanel = <div className="p-2">
                Agent: A<br />
                <div className="text-sm text-muted-foreground">
                    {get_utt(dialogueGraph.nodes[response.a].unit)}
                </div>
            </div>;
            bottomRightPanel = <div className="p-2">
                Agent: B<br />
                <div className="text-sm text-muted-foreground">
                    {get_utt(dialogueGraph.nodes[response.b].unit)}
                </div>
            </div>;
        }
    }


    return (<>
        <ResizablePanel defaultSize={80}>
            <ResizablePanelGroup direction="vertical">
                <ResizablePanel defaultSize={60}>
                    <ResizablePanelGroup direction="horizontal">
                        <ResizablePanel defaultSize={60} className="p-2">
                            {topLeftPanel}
                        </ResizablePanel>
                        <ResizableHandle />
                        <ResizablePanel defaultSize={40}>
                            {topRightPanel}
                        </ResizablePanel>
                    </ResizablePanelGroup>
                </ResizablePanel>
                <ResizableHandle />
                <ResizablePanel defaultSize={40}>
                    <ResizablePanelGroup direction="horizontal">
                        <ResizablePanel defaultSize={50}>
                            {bottomLeftPanel}
                        </ResizablePanel>
                        <ResizableHandle />
                        <ResizablePanel defaultSize={50}>
                            {bottomRightPanel}
                        </ResizablePanel>
                    </ResizablePanelGroup>
                </ResizablePanel>
            </ResizablePanelGroup>
        </ResizablePanel>
    </>);
}