import { DM_ExamPrompt, DM_ExamUtterance } from "./exam";
import { DM_GeneralPrompt, DM_GeneralUtterance } from "./general";

export type AnyPrompt = DM_GeneralPrompt | DM_ExamPrompt;
export type AnyUtterance = DM_GeneralUtterance | DM_ExamUtterance;

export type AnyDialogueUnit = AnyPrompt | AnyUtterance;

export function get_utt(anyUtt: AnyDialogueUnit): string {
    if (anyUtt.cls === "pmpt") {
        if (anyUtt.task === "general") {
            return anyUtt.utt;
        } else if (anyUtt.task === "exam") {
            return anyUtt.question;
        }
    } else if (anyUtt.cls === "utt") {
        if (anyUtt.task === "general") {
            return anyUtt.utt;
        } else if (anyUtt.task === "exam") {
            return anyUtt.answer;
        }
    }
}