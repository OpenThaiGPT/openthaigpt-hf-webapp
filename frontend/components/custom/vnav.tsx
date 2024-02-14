import React from "react";

import { HotReloader } from "@/lib/utils/reload";
import { cn } from "@/lib/utils/utils";
import { LucideIcon } from "lucide-react";
import { Button, buttonVariants } from "../ui/button";
// import { Tooltip, TooltipContent, TooltipTrigger } from "@radix-ui/react-tooltip"
import { AppState, pushAppState } from "@/lib/state";
import { Tooltip, TooltipContent, TooltipTrigger } from "../ui/tooltip";

HotReloader.install(module);

export type VNavLinksProp = {
    title: string
    label?: string
    icon: LucideIcon
    state: "normal" | "selected" | "disabled"
    clickState?: AppState
}[]

interface VNavProps {
    isCollapsed: boolean
    links: VNavLinksProp
}

export function VNav({
    isCollapsed,
    links
}: VNavProps) {
    const items: React.JSX.Element[] = [];
    for (const link of links) {
        const onClick = (e) => {
            if (link.clickState !== undefined) {
                pushAppState(link.clickState);
            }
            e.preventDefault();
        };
        if (isCollapsed) {
            items.push(
                <Tooltip key={link.title}>
                    <TooltipTrigger disabled={link.state === "disabled"} className="disabled:opacity-50 disabled:pointer-events-none">
                        <a
                            className={cn(
                                buttonVariants({
                                    variant: link.state === "selected" ? "default" : "outline",
                                    size: "icon",
                                }),
                                "h-12 w-12",
                                link.state === "selected" &&
                                "dark:bg-muted dark:text-muted-foreground dark:hover:bg-muted dark:hover:text-white"
                            )}
                            onClick={onClick}
                        >
                            <link.icon className="h-4 w-4" />
                            <span className="sr-only">{link.title}</span>
                        </a>
                    </TooltipTrigger>
                    <TooltipContent side="right">
                        {link.title}
                        {link.label && (
                            <span className="ml-auto text-muted-foreground">
                                {link.label}
                            </span>
                        )}
                    </TooltipContent>
                </Tooltip>
            );
        } else {
            items.push(<Button
                key={link.title}
                variant={link.state === "selected" ? "default" : "outline"}
                disabled={link.state === "disabled"}
                className={cn(
                    link.state === "selected" &&
                    "dark:bg-muted dark:text-white dark:hover:bg-muted dark:hover:text-white",
                    "justify-start h-12 truncate",
                )}
                onClick={onClick}
                size="sm"
            >
                <link.icon className="mr-2 h-4 w-4" />
                {link.title}
                {link.label && (
                    <span
                        className={cn(
                            "ml-auto",
                            link.state === "selected" &&
                            "text-background dark:text-white"
                        )}
                    >
                        {link.label}
                    </span>
                )}
            </Button>);
        }
    }
    return (
        <div
            data-collapsed={isCollapsed}
            className="group flex flex-col gap-6 py-3 data-[collapsed=true]:py-3"
        >
            <nav className="grid gap-5 px-3 group-[[data-collapsed=true]]:justify-center group-[[data-collapsed=true]]:px-3">
                {items}
            </nav>
        </div>
    );
}