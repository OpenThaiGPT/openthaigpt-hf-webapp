import { Editor } from "@/components/editor/page";
import { Button, buttonVariants } from "@/components/ui/button";
import { G_dataBridge } from "@/lib/data/bridge";
import { appState, pushAppState, routePrefix } from "@/lib/state";
import { host, wsPtcl } from "@/lib/utils/host";
import { HotReloader } from "@/lib/utils/reload";
import { cn } from "@/lib/utils/utils";
import { TypedWebSocket } from "@/lib/utils/ws/connection";
import { createRoot } from "react-dom/client";

HotReloader.install(module, function () {
    window.location.reload();
});

const domNode = document.getElementById("root");
const root = createRoot(domNode);


function render() {
    console.log("Rendering with AppState", appState.current);
    const elem = (<div className="h-full flex flex-col">
        <div className="border-b">
            {/* tob bar */}
            <div className="flex h-16 items-center px-6">
                <div>KBTG x OpenThaiGPT Human Feedback Tooling</div>
                <div className="ml-auto flex items-center space-x-4">
                    <Button asChild
                        className={cn(
                            buttonVariants({ variant: "ghost" })
                        )}>
                        <a href={routePrefix + "/public/api/logout"}>Sign out</a>
                    </Button>
                </div>
            </div>
        </div>
        <div className="grow">
            <Editor appState={appState.current} />
        </div>
    </div>);
    // root.render((
    //     <React.StrictMode>
    //         {elem}
    //     </React.StrictMode>
    // ));
    root.render(elem);
}

appState.onChange = render;

// const wsMux = new WSMultiplexer();
// wsMux.connectVirtualConnection(G_data_bridge, "data-bridge");

TypedWebSocket.createConnection(G_dataBridge, wsPtcl + host + routePrefix + "/api/ws-connect/data-bridge");

if (appState.current.menu === null) {
    console.log(appState);
    pushAppState({ menu: "dataset" });
} else {
    render();
}
