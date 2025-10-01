from vn2am.parser import get_semantic_args_without_event
from pathlib import Path

src_dir = Path(__file__).parent
activity_predicates_path = src_dir.parent/"data"/"activity_predicates.txt"
temperoal_predicates_path = src_dir.parent/"data"/"temporal_predicates.txt"

def load_predicate_file(file_path: str) -> list:
    with open(file_path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

ACTIVITY_PREDICATES = load_predicate_file(activity_predicates_path)
TEMPEROAL_PREDICATES = load_predicate_file(temperoal_predicates_path)


def is_activity_predicate(predicate):
    """
    return true if the predicate is a activity predicate.
    """
    return predicate.lower() in ACTIVITY_PREDICATES


def is_predicate_filtered(predicate):
    """
    return true if the predicate is either a activity predicate or a temperoal predicate
    """
    return predicate.lower() in ACTIVITY_PREDICATES or predicate.lower() in TEMPEROAL_PREDICATES


def get_all_condition_with_activity(semantic_list: list, event_index: dict, activity_event_tag: str) -> tuple:
    """
    Extract preconditions and postconditions with a activity predicate event tag
    """
    preconditions = []
    postconditions = []
    appeared_items = {}
    flag = False
    is_precondition_empty = True
    activity_event_index = event_index.get(activity_event_tag, None)

    if activity_event_index is None:
        raise ValueError(
            f"activity event tag '{activity_event_tag}' not found in event index.")
    # For all predicate with event tags before the activity event,
    # add them to preconditions.
    for arg_event, predicate, args, bool_value in semantic_list:
        if len(arg_event) > 1:
            # predicate without event tags or more than 1 event tag, skip it
            continue

        if is_predicate_filtered(predicate):
            continue

        if not arg_event:
            preconditions.append((arg_event, predicate, args, bool_value))
            continue

        if arg_event[0] == 'E':
            preconditions.append((arg_event, predicate, args, bool_value))
            continue

        arg_event_index = event_index.get(arg_event[0], None)
        if arg_event_index is None:
            # Event tag not found in event index, anontation error, skip it
            continue

        if arg_event_index < activity_event_index:
            preconditions.append((arg_event, predicate, args, bool_value))
            is_precondition_empty = False
        elif arg_event_index >= activity_event_index:
            # Tracking the same preidcate with different bool_value in postconditions
            key_args = get_semantic_args_without_event(args)
            key = (predicate, tuple(key_args))
            
            if key in appeared_items:
                previous_item = appeared_items[key]
                previous_bool_value = previous_item[-1]
                if bool_value != previous_bool_value:
                    if previous_item in postconditions:
                        postconditions.remove(previous_item)
                        preconditions.append(previous_item)
                        flag = True
                    postconditions.append(
                        (arg_event, predicate, args, bool_value))
            else:
                # Track the first appearance and add to postconditions
                appeared_items[key] = (arg_event, predicate, args, bool_value)
                postconditions.append((arg_event, predicate, args, bool_value))

    return preconditions, postconditions, flag, is_precondition_empty


def get_all_condition(semantic_list: list) -> tuple:
    """
    Tracks all appeared predicates, args, and bool_values.
    Initially adds all items to postconditions and keeps track of appeared ones.
    When a new one appears with a different bool_value, moves the previous one from postconditions to preconditions.
    """
    preconditions = []
    postconditions = []
    appeared_items = {}
    flag = False
    for arg_event, predicate, args, bool_value in semantic_list:
        if len(arg_event) > 1: # predicate involves multiple event tags
            continue
        
        if not arg_event or arg_event[0] == 'E': 
            # predicate do not have event tag or with tag 'E' (always true)
            preconditions.append((arg_event, predicate, args, bool_value))
            continue

        if is_predicate_filtered(predicate):
            continue
        
        # Tracking the same preidcate with different bool_value
        # Use predicate and non-event args as a unique key
        key_args = get_semantic_args_without_event(args)
        key = (predicate, tuple(key_args))

        if key in appeared_items:
            previous_item = appeared_items[key]
            previous_bool_value = previous_item[-1]
            # If the same predicate and args appear again with a different bool_value, handle accordingly
            if bool_value != previous_bool_value:
                if previous_item in postconditions:
                    postconditions.remove(previous_item)
                    preconditions.append(previous_item)
                    flag = True
                postconditions.append((arg_event, predicate, args, bool_value))
        else:
            # Track the first appearance and add to postconditions
            appeared_items[key] = (arg_event, predicate, args, bool_value)
            postconditions.append((arg_event, predicate, args, bool_value))

    return preconditions, postconditions, flag


def is_single_event(semantic_list: list) -> list:
    """
    Determines if the semantic list contains a single event.
    """
    event_tracker = set()
    single_event = {'E', 'e1'}
    for arg_event, predicate, args, bool_value in semantic_list:
        event_tracker.update(arg_event)
    if event_tracker == single_event or len(event_tracker) == 1:
        return True
    return False


def get_activity_event_tag(semantic_list: list) -> str:
    """
    find the event tag for first activty predicate
    """
    event_tag = None
    for arg_event, predicate, _, _ in semantic_list:
        if (is_activity_predicate(predicate)) and len(arg_event) == 1:
            event_tag = arg_event[0]
            break
    return event_tag


def get_pre_post_conditions(semantic_list: list, event_index: dict) -> tuple:
    """
    Extracts preconditions and postconditions from a list of semantics.
    """
    activity_event_tag = get_activity_event_tag(semantic_list)
    is_single = len(event_index) == 1

    if is_single or activity_event_tag is None:
        preconditions, postconditions, flag = get_all_condition(
            semantic_list)
        is_precondition_empty = True
    else:
        preconditions, postconditions, flag, precondition_flag = get_all_condition_with_activity(
            semantic_list, event_index, activity_event_tag)
        is_precondition_empty = precondition_flag

    # semantic list without activity predicate always has a empty preconditions
    # here checks when whether contradiction happens if there exists other 
    # non-activity preconditions
    if not is_precondition_empty and flag:
        print("Warning: Precondition is not empty, but there are contradictions in postconditions.")

    return preconditions, postconditions


def format_filterd_2_pddl(data):
    pddl_model = []
    for entry in data:
        name = entry.get('class_id')
        frames = entry.get("frames", [])
        for frame in frames:
            arguments = frame.get("arguments", [])
            preconditions = frame.get("preconditions", [])
            postconditions = frame.get("postconditions", [])

            pddl_data = {
                ':action': name,
                ':parameters': arguments,
                ':preconditions': format_cond(preconditions),
                ':effect': format_cond(postconditions)
            }

            pddl_model.append(pddl_data)
    return pddl_model


def format_cond(conditions):
    cond_list = []
    if not conditions:
        return []
    for cond in conditions:
        sign, keyword, args  = cond
        if sign == "not":
            if args[0] == 'Event':
                output = ["not", f"{keyword}", args[1:]]
            else:
                output = ["not", f"{keyword}", args]
        else:
            
            if args[0] == 'Event':
                output = [f"{keyword}", args[1:]]
            else:
                output = [f"{keyword}", args]
        cond_list.append(output)
    return ["and", cond_list]


def format_parameters(arguments):
    return [para for _, para in arguments]
