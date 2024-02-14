# OpenThaiGPT Human Feedback tooling (HFT)

## Data organization

HFT primarily stores annotation data in JSONL files.

Files are structured as `data/datasets/<DATASET_NAME>/<SPLIT>/chunk_<IDX>.jsonl`.
Each JSONL file/chunk contains N (500) entries of `SerializedEntry`.


## Data Channels

* Index
    * `index`
        * List all datasets
    * `index/<dataset>`
        * List all splits in dataset
    * `index/<dataset>/<split>`
        * List entries of first page in split
        * equivalent to `index/<dataset>/<split>/i:1`
    * `index/<dataset>/<split>/i:<N>`
        * List entries of N-th page in split
* Entry
    * `entry/<dataset>/<split>/<entry_id>`:
        * Annotation entry
        * WILL have diff/delta pubsub
