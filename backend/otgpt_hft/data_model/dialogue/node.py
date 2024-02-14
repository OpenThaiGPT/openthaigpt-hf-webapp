from __future__ import annotations

import random
from typing import Dict, List, Literal, Optional, Set, Tuple

from otgpt_hft.data_model.cmp import DB_ResponseCmp
from otgpt_hft.data_model.dialogue.error import DataIntegrityError

from ..abs import InstanceId
from ..any import AnyDialogueUnit
from ..source import SourceName

ClusterId = str

FullCompareOp = Literal[">", "=", "<", "-"]

# pairs_w_rel_count, total_pairs, pairs_wo_rel
CoverageData = Tuple[int, int, Optional[Tuple[InstanceId, InstanceId]]]


class InstanceCluster:
    def __init__(self, init_ins: InstanceId):
        self.c_id = "c" + init_ins
        # before: prefer more than this cluster
        self.before: Set[ClusterId] = set()
        # in cluster: all instances in this cluster is prefered equally
        self.cluster: Set[InstanceId] = {init_ins}
        # after: prefer less than this cluster
        self.after: Set[ClusterId] = set()

    def has_conflict(self) -> bool:
        return len(self.before.intersection(self.after)) > 0


class DialogueNodeCmp:
    """Dialogue Node Comparison Data

    Stores comparison data for a single node from a single source.
    """

    def __init__(self, init_nodes: Optional[List[InstanceId]] = None) -> None:
        self.ins_cluster: Dict[ClusterId, InstanceCluster] = {}
        self.node_to_cluster: Dict[InstanceId, ClusterId] = {}
        self.nodes: List[InstanceId] = []

        if init_nodes:
            for n in init_nodes:
                self.add_node(n)

        self.coverage_cache: Optional[CoverageData] = None
        self.raw_cmp_data: List[DB_ResponseCmp] = []

    def find_issues(self, inspect: bool) -> bool:
        all_cluster_id: Set[ClusterId] = set()
        for node, cluster_id in self.node_to_cluster.items():
            # [1.1] all nodes exist in the cluster they are referencing
            cluster = self.ins_cluster[cluster_id]
            if node not in cluster.cluster:
                if inspect:
                    raise DataIntegrityError(
                        {
                            "msg": f'node "{node}" refernces to cluster "{cluster_id}", but node does not exist in cluster',
                            "node_id": node,
                            "cluster_id": cluster_id,
                            "cluster": cluster,
                        }
                    )
                return True

            # [2.1] keep track of all cluster being referenced
            all_cluster_id.add(cluster_id)

        # [2.2] check set of all clusters being tracked by `ins_cluster` is consistent with reference from nodes
        all_cluster_id_2 = set(self.ins_cluster.keys())
        if all_cluster_id != all_cluster_id_2:
            if inspect:
                raise DataIntegrityError(
                    {
                        "msg": f"clusters referenced by nodes do not match clusters being tracking",
                        "clusters_referenced": all_cluster_id,
                        "clusters_tracked": all_cluster_id_2,
                    }
                )
            return True

        for cluster_id, cluster in self.ins_cluster.items():
            # [1.2] all nodes in cluster are referencing the cluster
            for node_id in cluster.cluster:
                if self.node_to_cluster[node_id] != cluster_id:
                    if inspect:
                        raise DataIntegrityError(
                            {
                                "msg": f"cluster {cluster_id} contains node {node_id} which does not reference to this cluster",
                                "cluster_id": cluster_id,
                                "node_id": node_id,
                                "node_ref_to_cluster": self.node_to_cluster[node_id],
                            }
                        )
                    return True

            # [4] check before after cluster matches
            for o_c_id in cluster.after:
                o_cluster = self.ins_cluster[o_c_id]
                if cluster_id not in o_cluster.before:
                    if inspect:
                        raise DataIntegrityError(
                            {
                                "msg": f"cluster {cluster_id} has another cluster {o_c_id} as after, but not the other way around (before)",
                                "cluster_id": cluster_id,
                                "other_cluster_id": o_c_id,
                            }
                        )
                    return True
            for o_c_id in cluster.before:
                o_cluster = self.ins_cluster[o_c_id]
                if cluster_id not in o_cluster.after:
                    if inspect:
                        raise DataIntegrityError(
                            {
                                "msg": f"cluster {cluster_id} has another cluster {o_c_id} as before, but not the other way around (after)",
                                "cluster_id": cluster_id,
                                "other_cluster_id": o_c_id,
                            }
                        )
                    return True

        # [3] check data does not have conflict
        for cluster_id, cluster in self.ins_cluster.items():
            if cluster.has_conflict():
                if inspect:
                    raise DataIntegrityError(
                        {
                            "msg": f"cluster {cluster_id} has conflict",
                            "cluster_id": cluster_id,
                            "cluster": cluster,
                        }
                    )
                return True

        return False

    def get_cmp(self, node_a: InstanceId, node_b: InstanceId) -> FullCompareOp:
        a_c_id = self.node_to_cluster[node_a]
        b_c_id = self.node_to_cluster[node_b]

        a_cluster = self.ins_cluster[a_c_id]

        if a_c_id == b_c_id:
            return "="
        if b_c_id in a_cluster.after:
            return ">"
        if b_c_id in a_cluster.before:
            return "<"
        return "-"

    def add_node(self, node: InstanceId):
        cluster = InstanceCluster(node)
        self.ins_cluster[cluster.c_id] = cluster
        self.node_to_cluster[node] = cluster.c_id
        self.nodes.append(node)
        self.coverage_cache = None

    # def connect_node(self, node_a: InstanceId, node_b: InstanceId, cmp_op: CompareOp):
    #     if cmp_op == ">":
    #         self.connect_cluster(
    #             self.node_to_cluster[node_a], self.node_to_cluster[node_b]
    #         )
    #     else:
    #         assert cmp_op == "="
    #         self.merge_cluster(
    #             self.node_to_cluster[node_a], self.node_to_cluster[node_b]
    #         )

    def get_cmp_data(self) -> List[DB_ResponseCmp]:
        return self.raw_cmp_data.copy()

    def add_cmp_data(self, cmp: DB_ResponseCmp):
        self.raw_cmp_data.append(cmp)
        if cmp.cmp == ">":
            self.connect_cluster(
                self.node_to_cluster[cmp.a], self.node_to_cluster[cmp.b]
            )
        else:
            assert cmp.cmp == "="
            self.merge_cluster(self.node_to_cluster[cmp.a], self.node_to_cluster[cmp.b])

    def compute_coverage(self, random_pair_wo_rel: bool = True) -> CoverageData:
        if self.coverage_cache is None:
            total_pairs = 0
            pairs_w_rel_count = 0
            pairs_wo_rel: List[Tuple[InstanceId, InstanceId]] = []
            for a_idx, node_a in enumerate(self.nodes):
                for node_b in self.nodes[a_idx + 1 :]:
                    total_pairs += 1
                    if self.get_cmp(node_a, node_b) == "-":
                        pairs_wo_rel.append((node_a, node_b))
                    else:
                        pairs_w_rel_count += 1

            if len(pairs_wo_rel):
                if random_pair_wo_rel:
                    pair_wo_rel = random.choice(pairs_wo_rel)
                else:
                    pair_wo_rel = pairs_wo_rel[0]
            else:
                pair_wo_rel = None

            self.coverage_cache = pairs_w_rel_count, total_pairs, pair_wo_rel

        return self.coverage_cache

    def connect_cluster(self, a_c_id: ClusterId, b_c_id: ClusterId):
        # a_cluster prefered over b_cluster
        a_cluster = self.ins_cluster[a_c_id]
        b_cluster = self.ins_cluster[b_c_id]

        # add "a cluster" and all clusters before "a cluster" to be "before" all clusters after "b cluster"
        for c_id in b_cluster.after:
            cluster = self.ins_cluster[c_id]
            cluster.before.add(a_c_id)
            cluster.before.update(a_cluster.before)

        # add "b cluster" and all clusters after "b cluster" to be "after" all clusters before "a cluster"
        for c_id in a_cluster.before:
            cluster = self.ins_cluster[c_id]
            cluster.after.add(b_c_id)
            cluster.after.update(b_cluster.after)

        # add "a cluster" and all clusters before "a cluster" to be "before" "b cluster"
        b_cluster.before.add(a_c_id)
        b_cluster.before.update(a_cluster.before)

        # add "b cluster" and all clusters after "b cluster" to be "after" "a cluster"
        a_cluster.after.add(b_c_id)
        a_cluster.after.update(b_cluster.after)

        self.coverage_cache = None

    def merge_cluster(self, a_c_id: ClusterId, b_c_id: ClusterId):
        # a_cluster equally prefered to b_cluster
        # we will merge b_cluster into a_cluster
        a_cluster = self.ins_cluster[a_c_id]
        b_cluster = self.ins_cluster[b_c_id]

        for ins_id in b_cluster.cluster:  # move nodes in b_cluster into a_cluster
            self.node_to_cluster[ins_id] = a_c_id
        a_cluster.cluster.update(b_cluster.cluster)
        del self.ins_cluster[b_c_id]

        for c_id in b_cluster.after:
            cluster = self.ins_cluster[c_id]
            cluster.before.remove(b_c_id)
            cluster.before.add(a_c_id)
            cluster.before.update(a_cluster.before)

        for c_id in b_cluster.before:
            cluster = self.ins_cluster[c_id]
            cluster.after.remove(b_c_id)
            cluster.after.add(a_c_id)
            cluster.after.update(a_cluster.after)

        for c_id in a_cluster.after:
            cluster = self.ins_cluster[c_id]
            cluster.before.update(b_cluster.before)

        for c_id in a_cluster.before:
            cluster = self.ins_cluster[c_id]
            cluster.after.update(b_cluster.after)

        a_cluster.after.update(b_cluster.after)
        a_cluster.before.update(b_cluster.before)

        self.coverage_cache = None


class DialogueNode:
    unit: AnyDialogueUnit
    _next: List[InstanceId]
    _cmps: Dict[SourceName, DialogueNodeCmp]

    def __init__(self, unit: AnyDialogueUnit) -> None:
        self.unit = unit
        self._next = []
        self._cmps = {}

    def add_next(self, utt_id: InstanceId):
        self._next.append(utt_id)
        for cmp_data in self._cmps.values():
            cmp_data.add_node(utt_id)

    def get_cmp(self, source: SourceName):
        if source in self._cmps:
            cmp_data = self._cmps[source]
        else:
            cmp_data = self._cmps[source] = DialogueNodeCmp(self._next)
        return cmp_data

    def find_issues(self, inspect: bool) -> bool:
        if inspect:
            for src, cmp in self._cmps.items():
                try:
                    cmp.find_issues(inspect)
                except DataIntegrityError as e:
                    raise DataIntegrityError(
                        {
                            "src": src,
                            "cmp_issue": e.info,
                        }
                    )
            return False
        else:
            return any(cmp.find_issues(inspect) for cmp in self._cmps.values())
