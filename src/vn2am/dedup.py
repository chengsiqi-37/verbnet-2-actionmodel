import json
import copy
from pathlib import Path
from vn2am.utils import get_argument_without_type, transform_hidden_arguments, formatted_predicate

DEBUG = False
src_dir = Path(__file__).parent.parent
SEMANTIC_TREE_PATH = src_dir/'data'/'vn_semanticrole_hierarchy.json'

with open(SEMANTIC_TREE_PATH, 'r') as f:
    semantic_tree = json.load(f)

dup_count = 0

def merge_same_frame(frames: dict) -> tuple[int, list]:
    """
    Takes all frames (action models) in a class and filter duplicated models
    """
    # A dict to store unique frames
    unique_frames = {}
    
    for frame in frames:
        # Extract all arguments in this frame, ignore ? marks
        parameters_list = get_argument_without_type(frame)
        parameters_without_hidden_mark = \
            transform_hidden_arguments(parameters_list)
        if (DEBUG):
            print(f"Argument List: {parameters_without_hidden_mark}")

        # Split preconditions and postconditions
        # and format them into a string representation
        current_preconds = get_condition_texts(frame, 'preconditions')
        current_effects = get_condition_texts(frame, 'postconditions')

        # A valid action model must contain at least one effect
        if len(current_effects) == 0:
            print(f"No effects :{frame['example_text']}") if DEBUG else None
            if len(current_preconds) == 0:
                print(
                    f"No precond & No effects: {frame['example_text']}") if DEBUG else None
            continue

        current_frame = {
            'arguments': parameters_without_hidden_mark,
            'preconditions': current_preconds,
            'postconditions': current_effects
        }
        
        # Sort the arguments, preconditions, and postconditions
        # for comparison
        parameters_key = format_parameters_key(parameters_without_hidden_mark)
        preconds_key = format_tuple_key(current_preconds)
        effects_key = format_tuple_key(current_effects)

        # Use a unique identifier for each frame to avoid duplicates
        unique_identifier = (
            parameters_key,
            preconds_key,
            effects_key
        )

        # Count duplicates for measurement
        global dup_count
        if unique_identifier in unique_frames:
            dup_count += 1

        if unique_identifier not in unique_frames:
            unique_frames[unique_identifier] = current_frame

    # Print the unique frames
    for frame in unique_frames.values():
        if (DEBUG):
            print(f"Unique Frame: {frame}")

    return extract_unique_frames(unique_frames)


def extract_unique_frames(frame_dict):
    frame_list = []
    for key, value in frame_dict.items():
        frame_list.append(value)
    return frame_list


def get_condition_texts(frame: dict, name: str) -> list:
    conditions = frame.get(name, [])
    condition_text = []
    for cond in conditions:
        formatted_condition = formatted_predicate(cond)
        if (DEBUG):
            print(f"{name.capitalize()}: {formatted_condition}")
        condition_text.append(formatted_condition)
    return condition_text


def format_tuple_key(conditions: list[tuple]):
    """
    input condition format: bool_value, predicate_name, tuple(args_without_type)
    """
    cond_key = copy.deepcopy(conditions)
    for i, cond in enumerate(cond_key):
        cond = list(cond)  # Convert tuple to list
        cond[2] = [get_top_themrole(arg, semantic_tree) for arg in cond[2] if arg != "Event"]
        cond[2] = sorted(cond[2], key=lambda x: str(x)) # Sort args to ensure consistency
        cond[2] = tuple(cond[2])
        cond_key[i] = tuple(cond)  # Update the original list with the modified tuple
    return tuple(cond_key)


def format_parameters_key(arguments: list) -> list:
    """
    convert arguments into their top themrole and create a consistent parameters key
    """
    arguments = sorted(arguments, key=lambda x: str(x))
    arguments_key = []
    for arg in arguments:
        arg = get_top_themrole(arg, semantic_tree)
        arguments_key.append(arg)
    return tuple(arguments_key)


def get_top_themrole(themrole, entry):
    current_top_node = ""

    # Search the themrole from the root of themrole tree to find its top parent
    def dfs(themrole, entry, current_top_node):
        if entry['value'] == 'Affector':
            current_top_node = 'Affector'
        elif entry['value'] == 'Undergoer':
            current_top_node = 'Undergoer'
        elif entry['value'] == 'Property':
            current_top_node = 'Property'
        elif entry['value'] == 'Place':
            current_top_node = 'Place'
        
        if entry['value'].lower() == themrole:
            return current_top_node
        for child in entry.get('children', []):
            result = dfs(themrole, child, current_top_node)
            if result:
                return result
        return "Not-Exist"
    
    current_top_node = dfs(themrole, entry, "")
    return current_top_node if current_top_node else themrole


def merge_subclass_frames(entries: list) -> dict:
    """
    Merge frames from subclasses into its parent class
    merged class use the verb of parent class as the key
    """
    merged_entries = []  # dict to store merged entries
    class_frames = {}    # dict to store one class with all frames

    for entry in entries:
        class_id = entry.get('class_id', 'null')
        frames = entry.get('frames', [])
        # get the verb name before the first hyphen
        # All vn class have hyphen for indexing
        # subclasses always have same verb name as their parent class
        if '-' in class_id:
            class_verb = class_id.split('-')[0]
        # create a new entry for new class_verb,
        # or append frames to existing class_verb (merge subclass)
        if class_verb not in class_frames:
            class_frames[class_verb] = []
        class_frames[class_verb].extend(frames)

    # Build the final merged entries
    for class_id, frames in class_frames.items():
        compressed_entry = {
            'class_id': class_id,
            'frames': frames
        }
        merged_entries.append(compressed_entry)
    return merged_entries


def dedup(data):  
    unique_entries = []

    # how many action models extracted including duplicates
    raw_count = 0
    for entry in data:
        frames = entry.get('frames', [])
        for frame in frames:
            postconditions = frame.get('postconditions', [])
            if len(postconditions) > 0:
                raw_count += 1
    
    merged_entires = merge_subclass_frames(data)

    for entry in merged_entires:
        frames = entry.get('frames', [])
        class_id = entry.get('class_id', 'Unknown')
        unique_frames = merge_same_frame(frames)
        current_class = {
            "class_id" : class_id,
            "frames"   : unique_frames
        }
        unique_entries.append(current_class)

    # Test if the count of unique frames matches the raw count
    unique_frame_count = sum(len(entry.get('frames', [])) for entry in unique_entries)
    assert dup_count + unique_frame_count == raw_count, \
        f"Duplicate count {dup_count} + unique count {unique_frame_count} does not match total action models {raw_count}"

    return unique_entries