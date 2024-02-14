from typing import Dict

from otgpt_hft.data_model.abs import DM_AbsUtterance, InstanceId
from otgpt_hft.data_model.any import AnyUtterance
from otgpt_hft.data_model.cmp import DB_ResponseCmp
from otgpt_hft.data_model.dialogue.error import DataIntegrityError
from otgpt_hft.data_model.dialogue.node import DialogueNode
from otgpt_hft.data_model.serial.entry import SerializedEntry


class DialogueGraph:
    root: DialogueNode
    nodes: Dict[InstanceId, DialogueNode]

    def __init__(self, serial: SerializedEntry, inspect=False):
        self.root = DialogueNode(serial.prompt)
        self.nodes = {
            serial.prompt.id: self.root,
        }

        for utt in serial.utterance:
            # NOTE: this assumes the connection by adding nodes to the graph in order
            # if utt.prev_id not in self.nodes, then fix this graph resolution
            self.add_utt(utt)

        # TODO lazily load cmp for each user
        for cmp in serial.cmps:
            self.add_cmp(cmp)
            if inspect:
                try:
                    self.find_issues(inspect)
                except DataIntegrityError as e:
                    raise DataIntegrityError(
                        {
                            "msg": "found issue after adding cmp",
                            "cmp": cmp,
                            "issue": e.info,
                        }
                    )

    def add_utt(self, utt: AnyUtterance):
        self.nodes[utt.id] = DialogueNode(utt)
        assert (
            utt.prev_id in self.nodes
        ), f"utterance previous node {utt.prev_id} does not exist"
        prev_node = self.nodes[utt.prev_id]
        prev_node.add_next(utt.id)

    def add_cmp(self, cmp: DB_ResponseCmp):
        src_name = cmp.source.get_name()

        a_node = self.nodes[cmp.a]
        b_node = self.nodes[cmp.b]
        assert isinstance(a_node.unit, DM_AbsUtterance)
        assert isinstance(b_node.unit, DM_AbsUtterance)
        self.nodes[cmp.b]
        a_parent_id = a_node.unit.prev_id
        b_parent_id = b_node.unit.prev_id
        assert a_parent_id == b_parent_id

        parent_node = self.nodes[a_parent_id]
        cmp_data = parent_node.get_cmp(src_name)
        cmp_data.add_cmp_data(cmp)

    def find_issues(self, inspect: bool) -> bool:
        if inspect:
            for node_id, node in self.nodes.items():
                try:
                    node.find_issues(inspect)
                except DataIntegrityError as e:
                    raise DataIntegrityError(
                        {
                            "node": node_id,
                            "node_issue": e.info,
                        }
                    )
            return False
        else:
            return any(node.find_issues(inspect) for node in self.nodes.values())
