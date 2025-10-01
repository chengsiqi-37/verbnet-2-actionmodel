from vn2am.semantic_tree import find_closest_common_ancestor
from pathlib import Path
import json


src_dir = Path(__file__).parent
semanticrole_hierarchy_dir = src_dir.parent/"data"/"vn_semanticrole_hierarchy.json"


def get_argument_without_type(frame: dict) -> list:
    """
    Extracts arguments from a frame, 
    each argument is a list with type and name.
    """
    argument = frame.get('arguments', -1)
    argument_list = []
    for arg in argument:
        argument_list.append(arg[1])
    return argument_list


def transform_hidden_arguments(argument_list: list) -> list:
    """
    Trims all hidden mark from the argument list.
    """
    transformed_list = []
    for arg in argument_list:
        arg = remove_themrole_mark(arg)
        transformed_list.append(arg)
    return transformed_list


def remove_themrole_mark(argument: str) -> str:
    """
    Remove the positional mark for themrole include '?' prefix, '_I' & '_J' suffix
    """
    new_arg = argument
    if argument.startswith('?'):
        new_arg = argument[1:]
    return new_arg.removesuffix("_I").removesuffix("_J").lower().strip()


def formatted_predicate(predicate: list) -> list:
    """
    formats a condition into the form of
      predicate(arg1, arg2, ...).
    """
    predicate_name = predicate[1]
    args = predicate[2]
    bool_value = predicate[3]

    # add themrole of args based on their type
    args_themrole = []
    for arg in args:
        if (arg[0] != 'Event' and arg[0] != 'Constant'):
            trimed_arg = remove_themrole_mark(arg[1])
            args_themrole.append(trimed_arg)
        else:
            args_themrole.append(arg[0])

    if bool_value == None:
        bool_value = ''
    elif bool_value == '!':
        bool_value = 'not'
    else:
        raise ValueError(f"Unexpected boolean value: {bool_value}")
    
    formatted_condition = (bool_value, predicate_name,
                           tuple(args_themrole))
    return formatted_condition


def read_pred_list(activity_pred, temporal_pred) -> list:
    filtered_list = activity_pred + temporal_pred

    duplicates = [
        item for item in filtered_list if filtered_list.count(item) > 1]
    if len(duplicates) > 0:
        print(
            f"number of duplicates found in filtered_list: {len(duplicates)}")
    return filtered_list


def fst_pred_count(predicate_dict: dict) -> tuple:
    """
    Classify predicate into three type 
    Different arguments under same predicate name only count once
    """
    fluent_pred = []
    static_pred = []
    temporal_pred = []
    special_cases = []
    dup_count = 0
    
    for predicate, value in predicate_dict.items():
        has_fluent = has_static = has_temporal = False

        # Verify all usage case of the predicate
        for pred in list(value['positive']) + list(value['negative']):
            event_count = sum(1 for arg in pred[2] if arg == 'Event')
            # Simple rules to determine fluent, static, temporal predicates
            if event_count == 1 and len(pred[2]) > 1:
                has_fluent = True
            if event_count == 0 and len(pred[2]) > 0:
                has_static = True
            if event_count == len(pred[2]):
                has_temporal = True
        
        # Check if different type found in the same predicate
        type_count = sum([has_fluent, has_static, has_temporal])
        if type_count != 1:
            current = (predicate, has_fluent, has_static, has_temporal)
            special_cases.append(current)
            dup_count += 1

        if has_fluent:
            fluent_pred.append(predicate)
        if has_static:
            static_pred.append(predicate)
        if has_temporal:
            temporal_pred.append(predicate)

    assert len(fluent_pred) + len(static_pred) + len(temporal_pred) - dup_count == len(predicate_dict)
    return fluent_pred, static_pred, temporal_pred, special_cases


def fst_pred_arg_count(predicate_dict: dict) -> tuple:
    fluent_pred = []
    static_pred = []
    temporal_pred = []
    
    for _, value in predicate_dict.items():
        for pred in list(value['positive']) + list(value['negative']):
            event_count = sum(1 for arg in pred[2] if arg == 'Event')
            if event_count == 1 and len(pred[2]) > 1:
                fluent_pred.append(pred)
            if event_count == 0 and len(pred[2]) > 0:
                static_pred.append(pred)
            if event_count == len(pred[2]):
                temporal_pred.append(pred)
    
    all_pred_args_count = sum(len(v['positive']) + len(v['negative']) for v in predicate_dict.values())
    assert len(fluent_pred) + len(static_pred) + len(temporal_pred) == all_pred_args_count
    return fluent_pred, static_pred, temporal_pred


def load_themroles(tree_path=semanticrole_hierarchy_dir):
    with open(tree_path, 'r', encoding='utf-8') as f:
        tree_data = json.load(f)
    
    # get all values in tree data
    themrole_tree_set = set()
    def traverse(node, themrole_set):
        themrole_set.add(node['value'].lower())
        for child in node.get('children', []):
            traverse(child, themrole_set)
        return themrole_set

    themrole_tree_set = traverse(tree_data, themrole_tree_set)
    return themrole_tree_set


def compare_predicate_args(args1, args2, value_to_node):
    themrole_set = load_themroles()
    if len(args1) != len(args2):
        return False
    for i, arg in enumerate(args1):
        if arg == args2[i]:
            continue
        if arg.lower() not in themrole_set or args2[i].lower() not in themrole_set:
            return False
        node_1 = value_to_node.get(arg)
        node_2 = value_to_node.get(args2[i])
        cla = find_closest_common_ancestor(node_1, node_2)
        if cla.value == 'participants':
            return False
    return True


def find_cond1_in_cond2(cond1, cond2, value_to_node):
    """
    if cond2 contains any predicate of cond1
    """
    bool_val, pred_name, args = cond1

    for other_bool, other_name, other_args in cond2:
        if other_bool != bool_val or other_name != pred_name:
            continue
        if compare_predicate_args(args, other_args, value_to_node):
            return True
    return False
    

def link_pre_to_post(preconditions, am_data, value_to_node):
    pre_links = {}
    for precond in preconditions:
        links = []
        for entry in am_data:
            verb = entry.get('class_id', 'null')
            frames = entry.get('frames', [])
            for i, frame in enumerate(frames):
                other_cond = frame.get("postconditions", [])
                if len(other_cond) == 0:
                    raise ValueError("Valid action model always have postcondition")
                found_link =  find_cond1_in_cond2(precond, other_cond, value_to_node)
                if found_link:
                    links.append(f'{verb}-{i}')
        precond_name = f"{'not' if precond[0] == 'not' else ''}{precond[1]}({','.join(precond[2])})"
        pre_links[precond_name] = links
    return pre_links


def link_post_to_pre(postconditions, am_data, value_to_node):
    post_links = {}
    for postcond in postconditions:
        link_count = []
        for entry in am_data:
            verb = entry.get('class_id', 'null')
            frames = entry.get('frames', [])
            for i, frame in enumerate(frames):
                other_cond = frame.get("preconditions", -1)
                if len(other_cond) == 0:
                    continue
                found_link =  find_cond1_in_cond2(postcond, other_cond, value_to_node)
                if found_link:
                    link_count.append(f'{verb}-{i}')
        postcond_name = f"{'!' if postcond[0] == '!' else ''}{postcond[1]}({','.join(postcond[2])})"
        post_links[postcond_name] = link_count
    return post_links