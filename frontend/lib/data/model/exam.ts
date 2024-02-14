import { DM_AbsPrompt, DM_AbsUtterance } from "./abs";

export type EXAM_TASK_T = "exam";
export const EXAM_TASK: EXAM_TASK_T = "exam";

export type DM_ExamPrompt = DM_AbsPrompt<EXAM_TASK_T> & {
    question: string
}

export type DM_ExamUtterance = DM_AbsUtterance<EXAM_TASK_T> & {
    cot: string
    answer: string
}