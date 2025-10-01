class SemanticTreeNode:
    def __init__(self, value):
        self.value = value
        self.children = []
        self.parents = []

    def add_child(self, child_node):
        self.children.append(child_node)
        child_node.parents.append(self)

    def print_tree(self, level=0):
        print("   " * level + str(self.value))
        for child in self.children:
            child.print_tree(level + 1)


def build_semantic_graph(json_data, registry=None):
    if registry is None:
        registry = {}

    # Always use the lower form for themroles
    value = json_data['value'].lower().strip()

    # Use existing node if already created
    if value in registry:
        node = registry[value]
    else:
        node = SemanticTreeNode(value)
        registry[value] = node

    for child in json_data.get('children', []):
        child_node = build_semantic_graph(child, registry)
        node.add_child(child_node)

    return node

def build_value_node_map(root):
    value_to_node = {}
    visited = set()

    def dfs(node):
        if node in visited:
            return
        visited.add(node)
        value_to_node[node.value] = node
        for child in node.children:
            dfs(child)

    dfs(root)
    return value_to_node


def get_ancestors(node):
    ancestors = {} # {ancestor_node: distance}
    stack = [(node, 0)]
    visited = set()

    while stack:
        current, depth = stack.pop()
        for parent in current.parents:
            if parent not in visited:
                visited.add(parent)
                ancestors[parent] = depth + 1
                stack.append((parent, depth + 1))
    return ancestors


def find_closest_common_ancestor(node1, node2):
    if node1 == node2:
        return node1

    ancestors1 = get_ancestors(node1)
    ancestors2 = get_ancestors(node2)

    common = set(ancestors1.keys()) & set(ancestors2.keys())
    if not common:
        return None

    # Pick the common ancestor with the smallest combined distance
    closest = min(common, key=lambda n: ancestors1[n] + ancestors2[n])
    return closest