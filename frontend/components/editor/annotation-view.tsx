import { AppStateAnnotation } from "@/lib/state";

interface AnnotationViewProps {
    appState: AppStateAnnotation
}

export function AnnotationView({
    appState
}: AnnotationViewProps) {
    return <div>Hi</div>;
}