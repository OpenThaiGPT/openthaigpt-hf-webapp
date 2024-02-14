import { AnySource } from "./source";

export type InstanceId = string;

export type DM_Abs<T> = {
    id?: InstanceId;
    cls: T;
    source: AnySource;
};

export type DM_AbsTask<T, T2> = DM_Abs<T> & {
    task: T2;
    author: "user" | "agent"
    // get_text: () => string;
};

export type DM_AbsPrompt<T2> = DM_AbsTask<"pmpt", T2> & {
    tags: string[];
};

export function id_is_prompt(id: InstanceId): boolean {
    return id.startsWith("p_");
}

export type DM_AbsUtterance<T2> = DM_AbsTask<"utt", T2> & {
    prev_id: InstanceId;
    // TODO: check if we need root_id
    // root_id?: InstanceId;
    // resolve_root: () => InstanceId | undefined;
};

