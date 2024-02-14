export type Uname = string;

// export type AbsSource = Record<string, never>

export type OAnnoSource = {
    t: "oanno";
    name: string;
};

export type ModelSource = {
    t: "model";
    name: string;
};

export type UserSource = {
    t: "user";
    uname: Uname;
};

export type AnySource = OAnnoSource | UserSource | ModelSource;
