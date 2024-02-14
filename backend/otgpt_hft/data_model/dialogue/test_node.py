from uuid import uuid4

from otgpt_hft.data_model.cmp import DB_ResponseCmp
from otgpt_hft.data_model.dialogue.node import DialogueNodeCmp
from otgpt_hft.data_model.source import UserSource

TEST_SOURCE = UserSource(uname="test-suit")


def test_dialogue_node_cmp():
    cmp = DialogueNodeCmp()

    cmp.add_node("a1")
    cmp.add_node("a2")
    cmp.add_node("a3")

    assert cmp.get_cmp("a1", "a2") == "-"
    assert cmp.get_cmp("a2", "a1") == "-"
    assert cmp.get_cmp("a1", "a3") == "-"
    assert cmp.get_cmp("a3", "a1") == "-"
    assert cmp.get_cmp("a2", "a3") == "-"
    assert cmp.get_cmp("a3", "a2") == "-"

    cmp.add_cmp_data(
        DB_ResponseCmp(id=str(uuid4()), a="a1", b="a2", cmp=">", source=TEST_SOURCE)
    )

    assert cmp.get_cmp("a1", "a2") == ">"
    assert cmp.get_cmp("a2", "a1") == "<"
    assert cmp.get_cmp("a1", "a3") == "-"
    assert cmp.get_cmp("a3", "a1") == "-"
    assert cmp.get_cmp("a2", "a3") == "-"
    assert cmp.get_cmp("a3", "a2") == "-"

    cmp.add_cmp_data(
        DB_ResponseCmp(id=str(uuid4()), a="a2", b="a3", cmp=">", source=TEST_SOURCE)
    )

    assert cmp.get_cmp("a1", "a2") == ">"
    assert cmp.get_cmp("a2", "a1") == "<"
    assert cmp.get_cmp("a1", "a3") == ">"
    assert cmp.get_cmp("a3", "a1") == "<"
    assert cmp.get_cmp("a2", "a3") == ">"
    assert cmp.get_cmp("a3", "a2") == "<"

    cmp.add_node("b1")
    cmp.add_node("b2")
    cmp.add_node("b3")

    assert cmp.get_cmp("b1", "b2") == "-"
    assert cmp.get_cmp("b1", "b3") == "-"
    assert cmp.get_cmp("b2", "b3") == "-"

    cmp.add_cmp_data(
        DB_ResponseCmp(id=str(uuid4()), a="b1", b="b2", cmp=">", source=TEST_SOURCE)
    )
    cmp.add_cmp_data(
        DB_ResponseCmp(id=str(uuid4()), a="b2", b="b3", cmp=">", source=TEST_SOURCE)
    )

    assert cmp.get_cmp("b1", "b2") == ">"
    assert cmp.get_cmp("b2", "b1") == "<"
    assert cmp.get_cmp("b1", "b3") == ">"
    assert cmp.get_cmp("b3", "b1") == "<"
    assert cmp.get_cmp("b2", "b3") == ">"
    assert cmp.get_cmp("b3", "b2") == "<"
    assert cmp.get_cmp("a1", "b3") == "-"
    assert cmp.get_cmp("b3", "a1") == "-"
    assert cmp.get_cmp("b1", "a3") == "-"
    assert cmp.get_cmp("a3", "b1") == "-"

    cmp.add_cmp_data(
        DB_ResponseCmp(id=str(uuid4()), a="a2", b="b2", cmp="=", source=TEST_SOURCE)
    )

    assert cmp.get_cmp("b1", "b3") == ">"
    assert cmp.get_cmp("b3", "b1") == "<"
    assert cmp.get_cmp("a1", "b3") == ">"
    assert cmp.get_cmp("b3", "a1") == "<"
    assert cmp.get_cmp("a1", "a3") == ">"
    assert cmp.get_cmp("a3", "a1") == "<"
    assert cmp.get_cmp("b1", "a3") == ">"
    assert cmp.get_cmp("a3", "b1") == "<"

    assert cmp.find_issues(inspect=True) == False


def test_dialogue_node_cmp_coverage_1():
    cmp = DialogueNodeCmp()

    assert cmp.compute_coverage(random_pair_wo_rel=False) == (0, 0, None)

    cmp.add_node("a1")

    assert cmp.compute_coverage(random_pair_wo_rel=False) == (0, 0, None)

    cmp.add_node("a2")

    assert cmp.compute_coverage(random_pair_wo_rel=False) == (0, 1, ("a1", "a2"))

    cmp.add_cmp_data(
        DB_ResponseCmp(id=str(uuid4()), a="a1", b="a2", cmp=">", source=TEST_SOURCE)
    )

    assert cmp.compute_coverage(random_pair_wo_rel=False) == (1, 1, None)

    cmp.add_node("a3")

    assert cmp.compute_coverage(random_pair_wo_rel=False) == (1, 3, ("a1", "a3"))

    cmp.add_cmp_data(
        DB_ResponseCmp(id=str(uuid4()), a="a1", b="a3", cmp=">", source=TEST_SOURCE)
    )

    assert cmp.compute_coverage(random_pair_wo_rel=False) == (2, 3, ("a2", "a3"))

    cmp.add_cmp_data(
        DB_ResponseCmp(id=str(uuid4()), a="a2", b="a3", cmp=">", source=TEST_SOURCE)
    )

    assert cmp.compute_coverage(random_pair_wo_rel=False) == (3, 3, None)

    assert cmp.find_issues(inspect=True) == False


def test_dialogue_node_cmp_coverage_2():
    cmp = DialogueNodeCmp()

    cmp.add_node("a1")
    cmp.add_node("a2")
    cmp.add_node("a3")

    cmp.add_cmp_data(
        DB_ResponseCmp(id=str(uuid4()), a="a1", b="a2", cmp=">", source=TEST_SOURCE)
    )

    assert cmp.compute_coverage(random_pair_wo_rel=False) == (1, 3, ("a1", "a3"))

    cmp.add_cmp_data(
        DB_ResponseCmp(id=str(uuid4()), a="a1", b="a3", cmp="=", source=TEST_SOURCE)
    )

    assert cmp.compute_coverage(random_pair_wo_rel=False) == (3, 3, None)

    assert cmp.find_issues(inspect=True) == False


def test_dialogue_node_cmp_coverage_3():
    cmp = DialogueNodeCmp()

    cmp.add_node("a1")
    cmp.add_node("a2")
    cmp.add_node("a3")

    cmp.add_cmp_data(
        DB_ResponseCmp(id=str(uuid4()), a="a1", b="a2", cmp=">", source=TEST_SOURCE)
    )

    assert cmp.compute_coverage(random_pair_wo_rel=False) == (1, 3, ("a1", "a3"))

    cmp.add_cmp_data(
        DB_ResponseCmp(id=str(uuid4()), a="a3", b="a1", cmp=">", source=TEST_SOURCE)
    )

    assert cmp.compute_coverage(random_pair_wo_rel=False) == (3, 3, None)

    assert cmp.find_issues(inspect=True) == False


def test_dialogue_node_cmp_conflict_1():
    cmp = DialogueNodeCmp()

    cmp.add_node("a1")
    cmp.add_node("a2")
    cmp.add_node("a3")

    cmp.add_cmp_data(
        DB_ResponseCmp(id=str(uuid4()), a="a1", b="a2", cmp=">", source=TEST_SOURCE)
    )
    cmp.add_cmp_data(
        DB_ResponseCmp(id=str(uuid4()), a="a2", b="a3", cmp=">", source=TEST_SOURCE)
    )
    assert cmp.find_issues(inspect=True) == False
    cmp.add_cmp_data(
        DB_ResponseCmp(id=str(uuid4()), a="a3", b="a1", cmp=">", source=TEST_SOURCE)
    )
    assert cmp.compute_coverage(random_pair_wo_rel=False) == (3, 3, None)
    assert cmp.find_issues(inspect=False) == True


def test_dialogue_node_cmp_conflict_2():
    cmp = DialogueNodeCmp()

    cmp.add_node("a1")
    cmp.add_node("a2")
    cmp.add_node("a3")

    cmp.add_cmp_data(
        DB_ResponseCmp(id=str(uuid4()), a="a1", b="a2", cmp=">", source=TEST_SOURCE)
    )
    cmp.add_cmp_data(
        DB_ResponseCmp(id=str(uuid4()), a="a2", b="a3", cmp=">", source=TEST_SOURCE)
    )
    assert cmp.find_issues(inspect=True) == False
    cmp.add_cmp_data(
        DB_ResponseCmp(id=str(uuid4()), a="a1", b="a3", cmp="=", source=TEST_SOURCE)
    )
    assert cmp.compute_coverage(random_pair_wo_rel=False) == (3, 3, None)
    assert cmp.find_issues(inspect=False) == True


def test_dialogue_node_cmp_conflict_3():
    cmp = DialogueNodeCmp()

    cmp.add_node("a1")

    cmp.add_cmp_data(
        DB_ResponseCmp(id=str(uuid4()), a="a1", b="a1", cmp=">", source=TEST_SOURCE)
    )
    assert cmp.find_issues(inspect=False) == True


def test_dialogue_node_cmp_conflict_3():
    cmp = DialogueNodeCmp()

    cmp.add_node("a1")

    cmp.add_cmp_data(
        DB_ResponseCmp(id=str(uuid4()), a="a1", b="a1", cmp=">", source=TEST_SOURCE)
    )
    assert cmp.find_issues(inspect=False) == True
