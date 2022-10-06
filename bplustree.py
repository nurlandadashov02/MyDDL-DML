import json
import os
from collections import deque
from storageManager import StorageManager
from constants import *
from fileManager import FileReader

indeces = {}

def binarySearch(array, first, last, x):
    if last == -1:
        return (False, 0)
    if last == first:
        if array[first] < x:
            return (False, first + 1)
        elif array[first] > x:
            return (False, first)
    mid = first + (last - first) // 2
    if x == array[mid]:
        return (True, mid)
    elif x > array[mid]:
        return binarySearch(array, mid + 1, last, x)
    else:
        return binarySearch(array, first, mid, x)

class Node(object):
    """Base node object. It should be index node
    Each node stores keys and children.
    Attributes:
        parent
    """

    def __init__(self, parent=None):
        """Child nodes are stored in values. Parent nodes simply act as a medium to traverse the tree.
        :type parent: Node"""
        self.keys: list = []
        self.values: list[Node] = []
        self.parent: Node = parent

    def index(self, key):
        """Return the index where the key should be.
        :type key: str
        """
        for i, item in enumerate(self.keys):
            if key < item:
                return i

        return len(self.keys)

    def __getitem__(self, item):
        return self.values[self.index(item)]

    def __setitem__(self, key, value):
        i = self.index(key)
        self.keys[i:i] = [key]
        self.values.pop(i)
        self.values[i:i] = value

    def setKeyValues(self, keys, values):
        self.keys = keys
        self.values = values

    def split(self):
        """Splits the node into two and stores them as child nodes.
        extract a pivot from the child to be inserted into the keys of the parent.
        @:return key and two children
        """
        left = Node(self.parent)

        mid = len(self.keys) // 2

        left.keys = self.keys[:mid]
        left.values = self.values[:mid + 1]
        for child in left.values:
            child.parent = left

        key = self.keys[mid]
        self.keys = self.keys[mid + 1:]
        self.values = self.values[mid + 1:]

        return key, [left, self]

    def __delitem__(self, key):
        i = self.index(key)
        del self.values[i]
        if i < len(self.keys):
            del self.keys[i]
        else:
            del self.keys[i - 1]

    def fusion(self):
        index = self.parent.index(self.keys[0])
        # merge this node with the next node
        if index < len(self.parent.keys):
            next_node: Node = self.parent.values[index + 1]
            next_node.keys[0:0] = self.keys + [self.parent.keys[index]]
            for child in self.values:
                child.parent = next_node
            next_node.values[0:0] = self.values
        else:  # If self is the last node, merge with prev
            prev: Node = self.parent.values[-2]
            prev.keys += [self.parent.keys[-1]] + self.keys
            for child in self.values:
                child.parent = prev
            prev.values += self.values

    def borrow_key(self, minimum: int):
        index = self.parent.index(self.keys[0])
        if index < len(self.parent.keys):
            next_node: Node = self.parent.values[index + 1]
            if len(next_node.keys) > minimum:
                self.keys += [self.parent.keys[index]]

                borrow_node = next_node.values.pop(0)
                borrow_node.parent = self
                self.values += [borrow_node]
                self.parent.keys[index] = next_node.keys.pop(0)
                return True
        elif index != 0:
            prev: Node = self.parent.values[index - 1]
            if len(prev.keys) > minimum:
                self.keys[0:0] = [self.parent.keys[index - 1]]

                borrow_node = prev.values.pop()
                borrow_node.parent = self
                self.values[0:0] = [borrow_node]
                self.parent.keys[index - 1] = prev.keys.pop()
                return True

        return False


class Leaf(Node):
    def __init__(self, parent=None, prev_node=None, next_node=None):
        """
        Create a new leaf in the leaf link
        :type prev_node: Leaf
        :type next_node: Leaf
        """
        super(Leaf, self).__init__(parent)
        self.next: Leaf = next_node
        if next_node is not None:
            next_node.prev = self
        self.prev: Leaf = prev_node
        if prev_node is not None:
            prev_node.next = self

    def __getitem__(self, item):
        return self.values[self.keys.index(item)]

    def __setitem__(self, key, value):
        i = self.index(key)
        if key not in self.keys:
            self.keys[i:i] = [key]
            self.values[i:i] = [value]
        else:
            self.values[i - 1] = value

    def split(self):
        left = Leaf(self.parent, self.prev, self)
        mid = len(self.keys) // 2

        left.keys = self.keys[:mid]
        left.values = self.values[:mid]

        self.keys: list = self.keys[mid:]
        self.values: list = self.values[mid:]

        # When the leaf node is split, set the parent key to the left-most key of the right child node.
        return self.keys[0], [left, self]

    def __delitem__(self, key):
        i = self.keys.index(key)
        del self.keys[i]
        del self.values[i]

    def fusion(self):
        if self.next is not None and self.next.parent == self.parent:
            self.next.keys[0:0] = self.keys
            self.next.values[0:0] = self.values
        else:
            self.prev.keys += self.keys
            self.prev.values += self.values

        if self.next is not None:
            self.next.prev = self.prev
        if self.prev is not None:
            self.prev.next = self.next

    def borrow_key(self, minimum: int):
        index = self.parent.index(self.keys[0])
        if index < len(self.parent.keys) and len(self.next.keys) > minimum:
            self.keys += [self.next.keys.pop(0)]
            self.values += [self.next.values.pop(0)]
            self.parent.keys[index] = self.next.keys[0]
            return True
        elif index != 0 and len(self.prev.keys) > minimum:
            self.keys[0:0] = [self.prev.keys.pop()]
            self.values[0:0] = [self.prev.values.pop()]
            self.parent.keys[index - 1] = self.keys[0]
            return True

        return False


class BPlusTree(object):
    """B+ tree object, consisting of nodes.
    Nodes will automatically be split into two once it is full. When a split occurs, a key will
    'float' upwards and be inserted into the parent node to act as a pivot.
    Attributes:
        maximum (int): The maximum number of keys each node can hold.
    """
    root: Node

    def __init__(self, type, maximum=4):
        self.root = Leaf()
        self.maximum: int = maximum if maximum > 2 else 2
        self.minimum: int = self.maximum // 2
        self.type = type
        self.loadTree()

    def find(self, key) -> Leaf:
        """ find the leaf
        Returns:
            Leaf: the leaf which should have the key
        """
        node = self.root
        # Traverse tree until leaf node is reached.
        while type(node) is not Leaf:
            node = node[key]

        return node

    def __getitem__(self, item):
        return self.find(item)[item]

    def query(self, key):
        """Returns a value for a given key, and None if the key does not exist."""
        leaf = self.find(key)
        return leaf[key] if key in leaf.keys else None

    def search(self, key):
        node = self.root
        while True:
            found, index = binarySearch(node.keys, 0, len(node.keys) - 1, key)

            if type(node) is not Leaf:
                pointer = node.values[index if not found else index + 1]
                if pointer:
                    node = pointer
                    continue
            else:
                return (found, index, node)

    def __setitem__(self, key, value, leaf=None):
        """Inserts a key-value pair after traversing to a leaf node. If the leaf node is full, split
              the leaf node into two.
              """
        if leaf is None:
            leaf = self.find(key)
        leaf[key] = value
        if len(leaf.keys) > self.maximum:
            self.insert_index(*leaf.split())

    def insert(self, key, value):
        """
        Returns:
            (bool,Leaf): the leaf where the key is inserted. return False if already has same key
        """
        leaf = self.find(key)
        if key in leaf.keys:
            return False, leaf
        else:
            self.__setitem__(key, value, leaf)
            return True, leaf

    def insert_index(self, key, values):
        """For a parent and child node,
                    Insert the values from the child into the values of the parent."""
        parent = values[1].parent
        if parent is None:
            values[0].parent = values[1].parent = self.root = Node()
            self.root.keys = [key]
            self.root.values = values
            return

        parent[key] = values
        # If the node is full, split the  node into two.
        if len(parent.keys) > self.maximum:
            self.insert_index(*parent.split())
        # Once a leaf node is split, it consists of a internal node and two leaf nodes.
        # These need to be re-inserted back into the tree.

    def deleteKey(self, type, key):
        value = self.query(key)
        if value:
            [fileName, pageIndex, recordIndex] = value
            reader = FileReader(os.path.join("data", type, fileName))
            reader.deleteRecord(pageIndex, recordIndex)
            StorageManager.updateEmptyPages(type, value)
            self.delete(key)
            return True
        else:
            return False


    def delete(self, key, node: Node = None):
        if node is None:
            node = self.find(key)
        del node[key]

        if len(node.keys) < self.minimum:
            if node == self.root:
                if len(self.root.keys) == 0 and len(self.root.values) > 0:
                    self.root = self.root.values[0]
                    self.root.parent = None
                return

            elif not node.borrow_key(self.minimum):
                node.fusion()
                self.delete(key, node.parent)

    def show(self, node=None, file=None, _prefix="", _last=True):
        """Prints the keys at each level."""
        if node is None:
            node = self.root
        print(_prefix, "`- " if _last else "|- ", node.keys, sep="", file=file)
        _prefix += "   " if _last else "|  "

        if type(node) is Node:
            # Recursively print the key of child nodes (if these exist).
            for i, child in enumerate(node.values):
                _last = (i == len(node.values) - 1)
                self.show(child, file, _prefix, _last)

    def leftmost_leaf(self) -> Leaf:
        node = self.root
        while type(node) is not Leaf:
            node = node.values[0]
        return node

    def saveTree(self):
        tree_dict = self.serializeTree(self.root)
        os.makedirs("index", exist_ok=True)
        with open(os.path.join("index", f"{self.type}.json"), 'w') as f:
            json.dump(tree_dict, f)


    def serializeTree(self, node):
        tree_dict = {
            "isLeaf": type(node) is Leaf,
            "keys": node.keys,
            "values": []
        }

        for value in node.values:
            if type(value) is Node or type(value) is Leaf:
                tree_dict["values"].append(self.serializeTree(value))
            else:
                tree_dict["values"].append(value)

        return tree_dict

    def deserializeTree(self, tree_dict):
        if tree_dict["isLeaf"]:
            leaf = Leaf()
            leaf.setKeyValues(tree_dict["keys"], tree_dict["values"])
            return leaf
        else:
            node = Node()
            node.setKeyValues(tree_dict["keys"], [self.deserializeTree(value) for value in tree_dict["values"]])
            return node

    def loadTree(self):
        if os.path.exists(os.path.join("index", f"{self.type}.json")):
            with open(os.path.join("index", f"{self.type}.json"), 'r') as f:
                tree_dict = json.load(f)
                self.root = self.deserializeTree(tree_dict)
                self.connectTree()

    def connectTree(self):
        queue = deque()
        queue.append(self.root)

        leaves = []
        while len(queue) > 0:
            levelSize = len(queue)
            for _ in range(levelSize):
                node = queue.popleft()
                for pointer in node.values:
                    if type(pointer) is Node or type(pointer) is Leaf:
                        pointer.parent = node
                        queue.append(pointer)

                    if type(pointer) is Leaf:
                        leaves.append(pointer)

        for i in range(len(leaves) - 1):
            leaves[i].next = leaves[i + 1]
            leaves[i + 1].prev = leaves[i]

    def getAllRecords(self):
        node = self.root
        records = []

        if type(node) is not Leaf:
            while type(node) is not Leaf:
                node = node.values[0]
            while node:
                for pointer in node.values:
                    records.append(pointer)
                node = node.next
        else:
            records = node.values

        records_ascending = []
        for record in records:
            [fileName, pageIndex, recordIndex] = record
            fileReader = FileReader(os.path.join("data", self.type, fileName))
            page = fileReader.readPage(pageIndex)
            record = page[PAGE_HEADER + recordIndex * RECORD_SIZE : PAGE_HEADER + (recordIndex+1) * RECORD_SIZE]
            records_ascending.append(" ".join(record.split()))
        
        return records_ascending

    def filter(self, type, key, value, sign):
        found, index, node = self.search(value)
        records = []
        if sign == '>':
            if found:
                index = index + 1
            while index < len(node.keys):
                records.append(node.values[index])
                index = index + 1
            while node.next:
                for pointer in node.next.values:
                    records.append(pointer)
                node = node.next
               
        elif sign == '<':
            index = index - 1
            while index >= 0:
                records.append(node.values[index])
                index = index - 1
            while node.prev:
                for pointer in node.prev.values:
                    records.append(pointer)
                node = node.prev
            records = records[::-1]
        else:
            if found:
                records.append(node.values[index])    
            else:
                return []     
        
        records_ascending = []
        for record in records:
            [fileName, pageIndex, recordIndex] = record
            fileReader = FileReader(os.path.join("data", self.type, fileName))
            page = fileReader.readPage(pageIndex)
            record = page[PAGE_HEADER + recordIndex * RECORD_SIZE : PAGE_HEADER + (recordIndex + 1) * RECORD_SIZE]
            records_ascending.append(" ".join(record.split()))

        return records_ascending