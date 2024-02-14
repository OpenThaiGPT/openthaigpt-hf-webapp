import { DM_Abs, InstanceId } from "./abs";

export type CMP_T = "cmp";
export const CMP: CMP_T = "cmp";

export type DB_ResponseCmp = DM_Abs<CMP_T> & {
    a: InstanceId
    b: InstanceId
    cmp: ">" | "="
}