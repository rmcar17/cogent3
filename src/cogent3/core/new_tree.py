from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, overload

if TYPE_CHECKING:
    from collections.abc import Iterator

    from typing_extensions import Self

# TODO: check usage of parent/_parent


class AbstractTreeNode(ABC):
    @property
    @abstractmethod
    def name(self) -> str | None: ...

    @property
    @abstractmethod
    def parent(self) -> Self | None: ...

    @parent.setter
    @abstractmethod
    def parent(
        self, new_parent: Self | None
    ) -> None: ...  # TODO: remember to clean refs

    @property
    @abstractmethod
    def children(self) -> list[Self]: ...

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}("#{self.get_newick()}")'

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
            msg = "One of the compared names is None."
            raise ValueError(msg)
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
            msg = "One of the compared names is None."
            raise ValueError(msg)
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

    def __getitem__(self, index: slice | int) -> list[Self] | Self:
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

    def __delitem__(self, index: slice | int) -> None:
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
            msg = "Parent does not exist."
            raise ValueError(msg)
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
        # TODO: include_self keyword only? boolean trap
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
        # TODO: include_self keyword only? boolean trap
        return list(self.iter_tips(include_self=include_self))

    def tip_children(self) -> list[Self]:
        """Returns direct children of self that are tips."""
        return [node for node in self.children if node.is_tip()]

    def non_tip_children(self) -> list[Self]:
        """Returns direct children in self that have descendants."""
        return [node for node in self.children if not node.is_tip()]

    def last_common_ancestor(self, other: Self) -> Self | None:
        """Finds the last common ancestor of nodes self and other.

        The nodes must be in the same tree.

        Parameters
        ----------
        other :
            A TreeNode to find the last common ancestor with.

        Returns
        -------
            The last common ancestor of self and other.
        """
        # TODO: this makes sense mainly in a rooted context, or does Gavin want it
        # to handle an orientation of an unrooted tree?
        my_lineage = {id(node) for node in (self, *self.ancestors())}
        curr = other
        while curr is not None:
            if id(curr) in my_lineage:
                return curr
            curr = curr.parent
        return None

    lca = last_common_ancestor  # for convenience

    def separation(self, other: Self) -> int | None:
        """Returns the number of edges separating self and other.

        Parameters
        ----------
        other :
            The node to count the edges from this to.

        Returns
        -------
            The number of edges between self and other.
            None if they are not connected.
        """
        # TODO: if the nodes don't belong to the same tree,
        # should it throw an error instead?

        # handle trivial case
        if self is other:
            return 0

        my_ancestors = {map(id, (self, *self.ancestors()))}
        other_curr = other
        count = 0
        while other_curr is not None:
            if id(other) in my_ancestors:
                # found the lca!
                # find distance from self node to lca
                curr = self
                while not (curr is None or curr is other):
                    count += 1
                    curr = curr.parent
                # TODO: raise error in the curr is None state?
                return count
            # have not yet found lca
            count += 1
            other_curr = other_curr.parent

        return None

    def get_newick(
        self,
        with_distances: bool = False,
        semicolon: bool = True,
        escape_name: bool = True,
        with_node_names: bool = False,
    ) -> str:
        """Return the newick string of node and its descendents

        Parameters
        ----------
        with_distances, optional
            include value of node length attribute if present.
        semicolon, optional
            end tree string with a semicolon
        escape_name, optional
            if any of these characters []'"(),
            nodes name, wrap the name in single quotes
        with_node_names, optional
            includes internal node names (except 'root')

        Returns
        -------
            The newick formatted string.
        """
        # TODO: args keyword only? boolean trap
        result = ["("]
        nodes_stack = [[self, len(self.children)]]
        node_count = 1

        while nodes_stack:
            node_count += 1
            # check the top node, any children left unvisited?
            top = nodes_stack[-1]
            top_node, num_unvisited_children = top
            if num_unvisited_children:  # has any child unvisited
                top[1] -= 1  # decrease the # of children unvisited
                # - for order
                next_child = top_node.children[-num_unvisited_children]
                # pre-visit
                if next_child.children:
                    result.append("(")
                nodes_stack.append([next_child, len(next_child.children)])
            else:  # no unvisited children
                nodes_stack.pop()
                # post-visit
                if top_node.children:
                    result[-1] = ")"

                if top_node.name_loaded or with_node_names:
                    if top_node.name is None or with_node_names and top_node.is_root():
                        name = ""
                    else:
                        name = str(top_node.name)
                        if escape_name and not (
                            name.startswith("'") and name.endswith("'")
                        ):
                            if re.search("""[]['"(),:;_]""", name):
                                name = "'%s'" % name.replace("'", "''")
                            else:
                                name = name.replace(" ", "_")
                    result.append(name)

                if (
                    with_distances
                    and (length := getattr(top_node, "length", None)) is not None
                ):
                    result[-1] = f"{result[-1]}:{length}"

                result.append(",")

        len_result = len(result)
        if len_result == 2:  # single node no name
            return ";" if semicolon else ""

        if len_result == 3:  # single node with name
            return f"{result[1]};" if semicolon else result[1]

        if semicolon:
            result[-1] = ";"
        else:
            result.pop(-1)
        return "".join(result)
