import json
import logging
DEBUG = False


def get_VN_entries(file_path: str, start_entry: int = None, end_entry: int = None) -> list:
    """
    Reads VerbNet JSON file and returns its entries list
    """
    with open(file_path, 'r') as f:
        data = json.load(f)

    if start_entry is not None and end_entry is not None:
        entries = data.get('VerbNet', [])[start_entry:end_entry]
    else:
        entries = data.get('VerbNet', [])

    if DEBUG:
        logging.info(
            f"Loaded {len(entries)} entries (including subclasses) from {file_path}")
    return entries


def get_frames(entries: list) -> list:
    """
    Extracts all frames from entries
    """
    frames = []
    for entry in entries:
        if (entry.get('frames')):
            frames.extend(entry['frames'])
        else:
            if DEBUG:
                logging.warning(
                    f"Entry {entry.get('class_id', '[no ID]')} has no frames.")
    if DEBUG:
        logging.info(f"Extracted {len(frames)} frames from entries")
    return frames


def get_example_text(frame: dict) -> list:
    """
    Extracts example text from a frame.
    """
    examples = frame.get('examples', [])
    return [example.get('example_text') for example in examples if example.get('example_text')]


def get_semantic_args(args: list) -> list:
    """
    Extract all args from semantic, including events
    return a list of tuples in form of (arg_type, arg_value)
    """
    arguments = []
    for arg in args:
        arg_type = arg.get('arg_type')
        arg_value = arg.get('value')
        arguments.append((arg_type, arg_value))
    return arguments


def get_semantic_args_without_event(args: tuple) -> list:
    arguments = []
    for arg in args:
        if arg[0] != 'Event':  # Ignore event arguments
            arguments.append((arg[0], arg[1]))
    return arguments


def get_event_tags(args: list) -> list:
    """
    Extracts the arguments with type 'Event'
    """
    event_tags = []
    for arg in args:
        if arg.get('arg_type') == 'Event':
            event_tags.append(arg.get('value'))
    return event_tags


def get_semantics(frame: dict) -> list:
    """
    convert semantic annotation in verbnet into a list of tuples in form of
    (arg_event, predicate, args, bool_value)
    """
    semantics = frame.get('semantics', {})
    semantic_list = []
    for semantic in semantics:
        predicate = semantic.get('predicate')
        args = semantic.get('args', [])
        bool_value = semantic.get('bool', None)
        arg_values = get_semantic_args(args)
        arg_event = get_event_tags(args)
        semantic_list.append((arg_event, predicate, arg_values, bool_value))
    return semantic_list


def get_themroles(entry: dict) -> list:
    themroles = entry.get('themroles')
    themrole_list = []
    for themrole in themroles:
        themrole_list.append(themrole.get('themrole'))
    return themrole_list


def get_arguments(frame: dict, themroles: list) -> list:
    """
    Extracts arguments from a frame (Only keep the themrole appear in Roles field)
    """
    semantics = frame.get('semantics', {})
    
    arguments = set()
    for semantic in semantics:
        args = semantic.get('args', [])
        arg_values = get_semantic_args(args)
        for arg_type, arg_value in arg_values:
            if arg_type == 'ThemRole':
                arguments.add((arg_type, arg_value))
            elif arg_value.removeprefix("?").lower() in themroles:
                arguments.add((arg_type, arg_value))
    return sorted(list(arguments))


def get_hidden_arguments(frame: dict) -> list:
    """
    Hidden argument is not listed in syntax, found it throguh all arguments in semantics.
    Carefully about duplicates if call directly
    """
    semantics = frame.get('semantics', {})
    hidden_arg_list = []
    for semantic in semantics:
        args = semantic.get('args', [])
        arg_values = get_semantic_args(args)
        for arg_type, arg_value in arg_values:
            if arg_value.startswith('?'):
                hidden_arg_list.append((arg_type, arg_value))
    # No need to worry about duplicates,
    # as we will remove duplicates in get_argument
    return hidden_arg_list


def get_event_index(frame: dict) -> dict:
    """
    Index event labels in the frame according to their order of appearance.
    """
    event_index = {}
    semantics = frame.get('semantics', [])
    index = 0
    for semantic in semantics:
        args = semantic.get('args', [])
        arg_event = get_event_tags(args)
        if not arg_event:
            continue
        is_single_event = len(arg_event) == 1
        is_new_event = arg_event[0] not in event_index
        if is_single_event and is_new_event:
            event_index[arg_event[0]] = index
            index += 1
    return event_index


def log_example_text(Examples: list):
    logging.info(f"\tExample Texts: {Examples[0]}")


def log_semantics(semantic_list: list):
    for arg_event, predicate, args, bool_value in semantic_list:
        args_str = ','.join(
            [f"{arg_type} {arg_value}" for arg_type, arg_value in args])

        if bool_value == "!":
            logging.info(f"\t  {arg_event} !{predicate}({args_str})")
        else:
            logging.info(f"\t  {arg_event} {predicate}({args_str})")


def log_argument(argument_list: list):
    """
    Displays the arguments in a readable format.
    """
    args_str = ', '.join([f"{arg_value}" for _, arg_value in argument_list])
    logging.info(f"\tArguments: {args_str}")
