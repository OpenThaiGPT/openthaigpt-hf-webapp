import React, { useEffect } from "react";

import { AppState } from "@/lib/state";
import { HotReloader } from "@/lib/utils/reload";
import { CogIcon, DatabaseIcon, PenLineIcon } from "lucide-react";
import { VNav, VNavLinksProp } from "../custom/vnav";
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from "../ui/resizable";
import { Separator } from "../ui/separator";
import { TooltipProvider } from "../ui/tooltip";
import { AnnotationView } from "./annotation-view";
import { AssignedAnno } from "./assigned-anno-view";
import { DatasetView } from "./dataset-view";

HotReloader.install(module);

interface EditorProps {
    appState: AppState,
}

function computeSize(): { collapsedSize: number, size: number } {
    const screenWidth: number = window.innerWidth;
    const collapsedSizePx = 70;
    const sizePx = 160;

    return {
        collapsedSize: Math.ceil(collapsedSizePx / screenWidth * 100),
        size: Math.ceil(sizePx / screenWidth * 100),
    };
}

/**
 * Editor is a single page app of the Human Feedback Tool
 */
export function Editor({
    appState
}: EditorProps) {
    const [sidebarSize, setSidebarSize] = React.useState(computeSize);
    const [isCollapsed, setIsCollapsed] = React.useState(false);

    const sidebarGroup1Links: VNavLinksProp = [
        {
            title: "Dataset",
            icon: DatabaseIcon,
            state: appState.menu === "dataset" ? "selected" : "normal",
            clickState: {
                menu: "dataset",
            }
        },
    ];
    const sidebarGroup2Links: VNavLinksProp = [
        {
            title: "Assigned Anno",
            icon: CogIcon,
            state: appState.menu === "assigned-annotation" ? "selected" : "normal",
            clickState: {
                menu: "assigned-annotation",
            }
        },
        {
            title: "Annotation",
            icon: PenLineIcon,
            state: appState.menu === "annotation" ? "selected" : "disabled",
        },
    ];

    let panelContent: React.JSX.Element | null = null;
    switch (appState.menu) {
    case "dataset": {
        panelContent = (
            <DatasetView appState={appState} />
        );
        break;
    }
    case "assigned-annotation": {
        panelContent = (
            <AssignedAnno appState={appState} />
        );
        break;
    }
    case "annotation": {
        panelContent = (
            <AnnotationView appState={appState} />
        );
        break;
    }
    }

    useEffect(() => {
        let lastResizeTimestamp = 0;
        let debounceTimer: any;

        // Function to debounce resize events
        const debouncedUpdateSidebarSize = () => {
            const currentTime = Date.now();
            if (currentTime - lastResizeTimestamp >= 300) {
                // More than a certain amount of time has passed since the last resize event
                setSidebarSize(computeSize());
                lastResizeTimestamp = currentTime;
            } else {
                // Less than a certain amount of time has passed, debounce it
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => {
                    setSidebarSize(computeSize());
                    lastResizeTimestamp = Date.now();
                }, 1000 - (currentTime - lastResizeTimestamp));
            }
        };

        // Add event listener for resize when the component mounts
        window.addEventListener("resize", debouncedUpdateSidebarSize);

        // Remove event listener when the component unmounts
        return () => {
            window.removeEventListener("resize", debouncedUpdateSidebarSize);
        };
    }, []); // Empty dependency array ensures the effect runs only once on mount


    return (
        <TooltipProvider delayDuration={0}>
            <ResizablePanelGroup direction="horizontal">
                <ResizablePanel defaultSize={isCollapsed ? sidebarSize.collapsedSize : sidebarSize.size} minSize={sidebarSize.size} maxSize={sidebarSize.size} collapsible collapsedSize={sidebarSize.collapsedSize}
                    onCollapse={() => {
                        setIsCollapsed(true);
                    }}
                    onExpand={() => {
                        setIsCollapsed(false);
                    }}
                >
                    <VNav isCollapsed={isCollapsed} links={sidebarGroup1Links} />
                    <Separator />
                    <VNav isCollapsed={isCollapsed} links={sidebarGroup2Links} />
                </ResizablePanel>
                <ResizableHandle />
                {panelContent}
            </ResizablePanelGroup>
        </TooltipProvider>
    );
}
