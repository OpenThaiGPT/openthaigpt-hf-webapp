import { get_utt } from "@/lib/data/model/any";
import { cn } from "@/lib/utils/utils";
import { DialogueGraph, DialoguePath } from "./transversal";

interface DialoguePreviewProps {
    dialogueGraph: DialogueGraph
    dialoguePath: DialoguePath
}

export function DialoguePreview({
    dialogueGraph,
    dialoguePath
}: DialoguePreviewProps) {
    const elems: JSX.Element[] = [];
    for (const id of dialoguePath) {
        const node = dialogueGraph.nodes[id];
        elems.push(<div key={id} className={cn(
            "flex",
            node.unit.author === "user" ? "flex-row" : "flex-row-reverse"
        )}>
            <button
                className="flex flex-col items-start gap-2 rounded-lg border p-3 text-left text-sm transition-all hover:bg-accent"
            // onClick={() =>
            //     setMail({
            //         ...mail,
            //         selected: item.id,
            //     })
            // }
            >
                <div className="flex w-full flex-col gap-1 font-semibold">
                    {node.unit.author}
                </div>
                <div className="line-clamp-2 text-xs text-muted-foreground">
                    {get_utt(node.unit)}
                </div>
            </button>
        </div>);
    }
    return <>{elems}</>;
}