import { decodeAppStateFromRouteSeg, pushAppState } from "@/lib/state";
import React from "react";
import { Route } from "../editor/dataset-view";
import { Button } from "../ui/button";

type RouteSegments = string[]

interface BreadCrumbProps {
    route: Route
}

function getRouteSegments(route: Route): RouteSegments {
    return route.split("/");
}

export function BreadCrumb({
    route
}: BreadCrumbProps) {
    const [fullRoute, setFullRoute] = React.useState(() => getRouteSegments(route));
    const [activeIdx, setActiveIdx] = React.useState(fullRoute.length - 1);

    React.useEffect(() => {
        const newFullRoute = getRouteSegments(route);
        if (activeIdx !== newFullRoute.length - 1) {
            setActiveIdx(newFullRoute.length - 1);
        }
        let shouldUpdateFullRoute = fullRoute.length < newFullRoute.length;
        for (let i = 0; i < newFullRoute.length && !shouldUpdateFullRoute; ++i) {
            if (fullRoute[i] !== newFullRoute[i]) {
                shouldUpdateFullRoute = true;
            }
        }
        if (shouldUpdateFullRoute) {
            setFullRoute(newFullRoute);
        }
    }, [route]);


    const breadcrumbs: React.JSX.Element[] = [];
    for (let i = 0; i < fullRoute.length; i++) {
        const idx = i;
        breadcrumbs.push(
            <Button
                key={i}
                variant={i == activeIdx ? "default" : "outline"}
                onClick={() => {
                    const route = fullRoute.slice(0, idx + 1);
                    pushAppState(decodeAppStateFromRouteSeg(route));
                }}
            >{fullRoute[i]}</Button>
        );
    }

    return (
        <div className="flex flex-row gap-2">
            {breadcrumbs}
        </div>
    );
}

// export function BreadCrumb({ propValue }) {
//     const [stateValue, setStateValue] = React.useState("");
//     const [counterValue, setCounterValue] = React.useState(0);

//     console.log("eiei");
//     React.useEffect(() => {
//         console.log("gum");
//         // This code is run when `propValue` changes
//         setStateValue(propValue);
//         setCounterValue(counterValue + 1);
//     }, [propValue]); // Only re-run the effect if `propValue` changes

//     return (
//         <div>
//             <p>Prop: {propValue}</p>
//             <p>State: {stateValue}</p>
//             <p>State: {counterValue}</p>
//         </div>
//     );
// }