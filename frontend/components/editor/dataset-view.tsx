import { G_dataBridge, Item } from "@/lib/data/bridge";
import { SerializedEntry } from "@/lib/data/model/serial/entry";
import { AppStateDataset, pushAppState, pushAppUrl } from "@/lib/state";
import assert from "@/lib/utils/assert";
import { cn } from "@/lib/utils/utils";
import { Channel } from "@/lib/utils/ws/pubsub";
import { useEffect, useState } from "react";
import { BreadCrumb } from "../custom/breadcrumb";
import { PageSelectNum } from "../custom/pageselect";
import { Badge } from "../ui/badge";
import { ResizableHandle, ResizablePanel } from "../ui/resizable";
import { ScrollArea } from "../ui/scroll-area";
import { DialoguePreview } from "./dialogue-preview";
import { DialogueGraph, DialoguePath } from "./transversal";

interface DatasetViewProps {
    appState: AppStateDataset
}

type PageMetadata = {
    totalPage: number
    totalEntries: number
}

export type Route = string;

function computeBreadCrumbRoute(appState: AppStateDataset): Route {
    let route: Route = "dataset";
    if (appState.dataset !== undefined) {
        route += `/${appState.dataset}`;
    }
    if (appState.split !== undefined) {
        route += `/${appState.split}`;
    }
    return route;
}

function computeLeftChannel(appState: AppStateDataset): { meta: Channel | null, view: Channel } {
    let ch: Channel | null = null;
    let ch2: Channel = "index";
    if (appState.dataset !== undefined) {
        ch2 += `/${appState.dataset}`;
        if (appState.split !== undefined) {
            ch = `index/${appState.dataset}/${appState.split}/meta`;
            ch2 += `/${appState.split}`;
            if (appState.page !== undefined) {
                ch2 += `/i:${appState.page}`;
            }
        }
    }
    return { meta: ch, view: ch2 };
}

function computeRightChannel(appState: AppStateDataset): Channel | null {
    if (
        appState.dataset === undefined ||
        appState.split === undefined ||
        appState.entry === undefined
    ) {
        return null;
    }
    return `entry/${appState.dataset}/${appState.split}/${appState.entry}`;
}

function channel2Url(channel: string): string {
    const segments = channel.split("/");
    if (segments[0] === "index") {
        let url = "/editor/dataset/" + segments.slice(1, 3).join("/");
        if (segments.length > 3) {
            url += "/p/" + segments[3];
        }
        return url;
    } else if (segments[0] === "entry") {
        return "/editor/dataset/" + segments.slice(1, 3).join("/") + "/e/" + segments[3];
    }
    assert(false, "unhandled channel");
}

export function DatasetView({
    appState,
}: DatasetViewProps) {
    const [route, setRoute] = useState(() => computeBreadCrumbRoute(appState));
    const pageIdx = appState.menu === "dataset" ? appState.page || 1 : 1;
    // const [pageIdx, setPageIdx] = useState(1);
    const [pageMetadata, setPageMetadata] = useState<PageMetadata>(null);
    const [leftChannel, setLeftChannel] = useState(() => computeLeftChannel(appState));
    const [rightChannel, setRightChannel] = useState(() => computeRightChannel(appState));
    // items to show on left side
    const [leftItems, setLeftItems] = useState<Item[]>(null);
    const [dialogueGraph, setDialogueGraph] = useState<DialogueGraph>(null);
    const [dialoguePath, setDialoguePath] = useState<DialoguePath>(null);

    function setPageIdx(newPageIdx: number) {
        assert(appState.menu === "dataset", "Set page index must only be called when `menu` is 'dataset'.");
        pushAppState({
            ...appState,
            page: newPageIdx,
        });
    }

    useEffect(() => {
        setRoute(computeBreadCrumbRoute(appState));
        setLeftChannel(computeLeftChannel(appState));
        if (appState.menu === "dataset") {
            setPageIdx(appState.page || 1);
        }
        const nextRightChannel = computeRightChannel(appState);
        if (nextRightChannel !== null) {
            setRightChannel(nextRightChannel);
        }
    }, [appState]);

    useEffect(() => {
        let hookId: number | null = null;
        if (leftChannel.meta !== null) {
            hookId = G_dataBridge.hookSetter(leftChannel.meta, setPageMetadata);
        }
        const hookId2 = G_dataBridge.hookSetter(leftChannel.view, setLeftItems);
        return () => {
            if (hookId !== null) {
                G_dataBridge.unhookSetter(hookId);
            }
            G_dataBridge.unhookSetter(hookId2);
            setPageMetadata(null);
            setLeftItems(null);
        };
    }, [leftChannel]);


    useEffect(() => {
        if (rightChannel !== null) {
            const hookId = G_dataBridge.hookSetter(rightChannel, (se: SerializedEntry) => {
                const dialogueGraph = new DialogueGraph(se);
                setDialogueGraph(dialogueGraph);
                setDialoguePath(dialogueGraph.walk(null));
            });
            return () => {
                G_dataBridge.unhookSetter(hookId);
                setDialogueGraph(null);
                setDialoguePath(null);
            };
        }
    }, [rightChannel]);

    const compact = appState.menu === "dataset" && appState.split !== undefined;

    const selectedId = dialogueGraph?.root.unit.id;

    const elems: React.JSX.Element[] = [];
    if (leftItems !== null) {
        for (const item of leftItems) {
            elems.push(<button
                key={item.id}
                className={cn(
                    "flex flex-col items-start rounded-lg border text-left text-sm transition-all hover:bg-accent",
                    selectedId === item.id && "bg-muted",
                    compact ? "gap-1 p-1" : "gap-2 p-3",
                )}
                onClick={() => {
                    console.log("clicked!!");
                    pushAppUrl(channel2Url(item.channel));
                }
                }
            >
                <div className="flex w-full flex-col gap-1">
                    <div className="flex items-center">
                        <div className="flex items-center gap-2">
                            <div className="font-semibold">
                                {item.title}
                            </div>
                            {!item.pending && <span className="flex h-2 w-2 rounded-full bg-blue-600" />}
                        </div>
                        {/* <div
                            className={cn(
                                "ml-auto text-xs",
                                selectedId === item.id
                                ? "text-foreground"
                                : "text-muted-foreground"
                                )}
                                >
                                Top right text
                            </div> */}
                    </div>
                    <div className="text-xs font-medium">
                        {item.caption}
                    </div>
                </div>
                <div className="line-clamp-2 text-xs text-muted-foreground">
                    {item.description.substring(0, 300)}
                </div>
                {item.labels.length ? (
                    <div className="flex items-center gap-2">
                        {item.labels.map((label) => (
                            <Badge key={label} variant={getBadgeVariantFromLabel(label)}>
                                {label}
                            </Badge>
                        ))}
                    </div>
                ) : null}
            </button>);
        }
    } else {
        elems.push(<span key="loading">loading</span>);
    }

    const leftPanel = (<ScrollArea className="h-100">
        <div className="flex flex-col gap-4 p-4">
            <BreadCrumb route={route} />
            <div className={cn(
                "flex flex-col",
                compact ? "gap-2" : "gap-4"
            )}>
                {elems}
            </div>
            <PageSelectNum page={pageIdx} total={pageMetadata?.totalPage} setPage={setPageIdx} />
        </div>
    </ScrollArea>);

    let rightElem: JSX.Element;
    if (dialoguePath) {
        rightElem = <DialoguePreview dialogueGraph={dialogueGraph} dialoguePath={dialoguePath} />;
    } else {
        rightElem = <div key={"placeholder"} className="p-4">
            <span>Select dialogue to show preview</span>
        </div>;

    }

    const rightPanel = (<ScrollArea className="h-100">
        {/* <div className="flex flex-col gap-4 p-4"> */}
        {/* <div className="flex flex-row-reverse gap-2">
                <Button>Prev</Button>
                <Button>Next</Button>
            </div> */}
        <div className="flex flex-col gap-4 p-4">
            {rightElem}
        </div>
        {/* </div> */}
    </ScrollArea>);

    return (<>
        <ResizablePanel defaultSize={40}>
            {leftPanel}
        </ResizablePanel>
        <ResizableHandle />
        <ResizablePanel defaultSize={40}>
            {rightPanel}
        </ResizablePanel>
    </>);
}

function getBadgeVariantFromLabel(
    label: string
): React.ComponentProps<typeof Badge>["variant"] {
    if (["work"].includes(label.toLowerCase())) {
        return "default";
    }

    if (["personal"].includes(label.toLowerCase())) {
        return "outline";
    }

    return "secondary";
}