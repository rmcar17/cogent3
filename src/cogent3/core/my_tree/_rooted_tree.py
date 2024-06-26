from collections.abc import Iterable
from typing import Self

from ._abstract_tree import AbstractTreeNode


class RootedTreeNode(AbstractTreeNode):
    def __init__(
        self, name: str, children: Iterable[Self], parent: Self | None
    ) -> None:
        self.name = name
        self.children = list(children)
        self.parent = parent
