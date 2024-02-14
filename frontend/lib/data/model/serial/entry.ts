import { AnyPrompt, AnyUtterance } from "../any";
import { DB_ResponseCmp } from "../cmp";

export type SerializedEntry = {
    prompt: AnyPrompt
    utterance: AnyUtterance[]
    cmps: DB_ResponseCmp[]
}