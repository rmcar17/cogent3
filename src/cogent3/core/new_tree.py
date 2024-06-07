from abc import ABC, abstractmethod
from typing import Iterator, Optional, Union, overload
from typing_extensions import Self

# TODO: check usage of parent/_parent


class AbstractTreeNode(ABC):
    @property
    @abstractmethod
    def name(self) -> Optional[str]: ...

    @property
    @abstractmethod
    def parent(self) -> Optional[Self]: ...

    @parent.setter
    @abstractmethod
    def parent(
        self, new_parent: Optional[Self]
    ) -> None: ...  # TODO: remember to clean refs

    @property
    @abstractmethod
    def children(self) -> list[Self]: ...

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}("{self.get_newick()}")'

    def __str__(self) -> str:
        """Gets newick string representation of the tree.

        Returns
        -------
        str
            Newick formatted string.
        """
        return self.get_newick()

    def __lt__(self, other: Self) -> bool:
        """Compare two nodes by name.

        Parameters
        ----------
        other :
            Another tree node.

        Returns
        -------
            True if this node's name is ordered before the other node's name.
        """
        if self.name is None or other.name is None:  # TODO: check how to handle
            raise ValueError("One of the compared names is None.")
        return self.name < other.name

    def __gt__(self, other: Self) -> bool:
        """Compare two nodes by name.

        Parameters
        ----------
        other :
            Another tree node.

        Returns
        -------
            True if this node's name is ordered after the other node's name.
        """
        if self.name is None or other.name is None:  # TODO: check how to handle
            raise ValueError("One of the compared names is None.")
        return self.name > other.name

    def compare_name(self, other: Self) -> bool:
        """True is the two TreeNodes have the same name, False otherwise.

        Parameters
        ----------
        other :
            Another tree node.
        Returns
        -------
            True if this node's name is the same as the other node's name.
        """
        return self is other or self.name == other.name

    def compare_by_names(self, other: Self) -> bool:
        """True if the two trees are on the same set of names, False otherwise.

        Parameters
        ----------
        other :
            Another tree node.

        Returns
        -------
            True if the two trees are on the same set of names, False otherwise.
        """
        # TODO: should I get the "root" of the trees first?
        if self is other:
            return True
        self_names = self.get_node_names()
        other_names = other.get_node_names()
        if len(self_names) != len(other_names):
            return False
        self_names = [v for v in self_names if v is not None]
        self_names.sort()
        other_names = [v for v in other_names if v is not None]
        other_names.sort()
        return self_names == other_names

    @overload
    def __getitem__(self, index: int) -> Self: ...

    @overload
    def __getitem__(self, index: slice) -> list[Self]: ...

    def __getitem__(self, index: Union[slice, int]) -> Union[list[Self], Self]:
        """Retrieve node at index or nodes at slice from children.

        Parameters
        ----------
        index :
            index or slice to retrieve

        Returns
        -------
            Selected children.
        """
        return self.children[index]

    def __delitem__(self, index: Union[slice, int]) -> None:
        """Delete node at index or nodes at slice from children.

        Parameters
        ----------
        index :
            index or slice to remove
        """
        curr = self.children[index]
        if isinstance(curr, list):
            for c in curr:
                c.parent = None
        else:
            curr.parent = None
        del self.children[index]

    def __iter__(
        self,
    ) -> Iterator[Self]:  # TODO: for unrooted should this be neighbours?
        """Iterator over the children of the node."""
        return iter(self.children)

    def __len__(self) -> int:  # TODO: for unrooted should this be neighbours?
        """The number of children."""
        return len(self.children)

    def index_in_parent(self) -> int:
        """Index of this node in its parent."""
        if self.parent is None:
            raise ValueError("Parent does not exist.")
        return self.parent.children.index(self)

    def is_tip(self) -> bool:
        """True if the current node is a tip (no children), False otherwise."""
        return len(self.children) == 0

    def is_root(self) -> bool:
        """True if the current node is a root (no parent)."""
        return self.parent is None

    def ancestors(self) -> list[Self]:
        """Returns all ancestors back to the root.

        Does not include the current node.
        """
        result = []
        curr = self.parent
        while curr is not None:
            result.append(curr)
            curr = curr.parent
        return result

    def root(self) -> Self:
        """Returns the root of the tree for the tree node.

        Returns
        -------
            The root of the tree for the tree node.
        """
        curr = self
        while curr.parent is not None:
            curr = curr.parent
        return curr

    def siblings(self) -> list[Self]:
        """Gets all siblings of the current node.

        All children of the same parent as self. Doesn't include self.

        Returns
        -------
            All siblings of the current node.
        """
        if self.parent is None:
            return []
        result = self.parent.children[:]
        result.remove(self)
        return result

    def iter_tips(self, include_self: bool = False) -> Iterator[Self]:
        """Iterates over tips descended from self.

        In the case self is a tip - if include_self is True, [self].
        Otherwise [].

        Parameters
        ----------
        include_self :
            Whether to include self is it is a tip, by default False


        Yields
        ------
            Iterator over tips.
        """
        # Handle case for include self when no children
        if not self.children:
            if include_self:
                yield self
            return None

        # Use stack to find tips
        stack = [self]
        while stack:
            curr = stack.pop()
            if curr.children:
                stack.extend(
                    curr.children[::-1]
                )  # TODO: why does the original code bother reversing?
            else:
                yield curr

    def tips(self, include_self=False) -> list[Self]:
        """Returns tips descended from self.

        In the case self is a tip - if include_self is True, [self].
        Otherwise [].

        Parameters
        ----------
        include_self :
            Whether to include self is it is a tip, by default False

        Returns
        -------
            list of tip nodes.
        """
        return list(self.iter_tips(include_self=include_self))

    def tip_children(self) -> list[Self]:
        """Returns direct children of self that are tips."""
        return [node for node in self.children if node.is_tip()]

    def non_tip_children(self) -> list[Self]:
        """Returns direct children in self that have descendants."""
        return [node for node in self.children if not node.is_tip()]
