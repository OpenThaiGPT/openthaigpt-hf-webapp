import { DM_AbsPrompt, DM_AbsUtterance } from "./abs";

export type GENERAL_TASK_T = "general";
export const GENERAL_TASK: GENERAL_TASK_T = "general";

type GeneralUtterance = {
    utt: string
}

export type DM_GeneralPrompt = DM_AbsPrompt<GENERAL_TASK_T> & GeneralUtterance

export type DM_GeneralUtterance = DM_AbsUtterance<GENERAL_TASK_T> & GeneralUtterance
