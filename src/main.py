import logging
import json
from pathlib import Path
from vn2am.parser import get_VN_entries, \
    get_example_text, get_semantics, log_example_text, \
    log_semantics, get_arguments, log_argument, \
    get_event_index
from vn2am.converter import get_pre_post_conditions, format_filterd_2_pddl
from vn2am.dedup import dedup
from vn2am.utils import load_themroles

src_dir = Path(__file__).parent
INPUT_FILE_PATH = src_dir/"data"/"verbnet3.4.json"
TREE_PATH = src_dir/"data"/"vn_semanticrole_hierarchy.json"
UNFILTERED_STRIPS_PATH = src_dir.parent/"output"/"extracted_unfiltered_STRIPS.json"
FILTERED_STRIPS_PATH= src_dir.parent/"output"/"extracted_filtered_STRIPS.json"
EXAMPLE_TEXT_PATH = src_dir.parent/"output"/"extracted_example_texts.json"
LOG_FILE_PATH = src_dir.parent/"output"/"extracted_unfiltered_STRIPS.log"
PDDL_FILE_PATH = src_dir.parent/"output"/"extracted_PDDL.json"


def main(): 
    # Setup output directory
    output_dir = src_dir.parent/"output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Setup logging
    logging.basicConfig(
        filename=LOG_FILE_PATH,
        filemode='w',
        level=logging.INFO,
        format='%(message)s'
    )

    strips_model = []
    examples = []

    verbnet_entries = get_VN_entries(INPUT_FILE_PATH, start_entry=None, end_entry=None)

    # Loop through each entry and get the frames
    for entry in verbnet_entries:
        class_id = entry.get('class_id', 'null')
        frames = entry.get('frames', [])
        
        if class_id == 'null':
            continue
        logging.info(f"\nClass ID: {class_id}")

        strips_data = {
            'class_id': class_id,
            'frames': []
        }

        themroles = load_themroles(TREE_PATH)

        # In each frame, extract action model components based on annotation
        for i, frame in enumerate(frames):
            event_index = get_event_index(frame)
            argument = get_arguments(frame, themroles)
            example_text = get_example_text(frame)
            semantic = get_semantics(frame)
            precondition, postcondition = \
                get_pre_post_conditions(semantic, event_index)

            # Action model data structure
            frame_data = {
                'example_text'  : example_text,
                'arguments'     : argument,
                'preconditions' : precondition,
                'postconditions': postcondition,
            }
            strips_data['frames'].append(frame_data)

            # Plain text example texts
            example_texts = {
                'example_text': example_text
            }
            examples.append(example_texts)

            # Logging in readable format
            logging.info(f"\tFrame {i + 1}:")
            log_example_text(example_text)
            log_argument(argument)
            logging.info("\tPreconditions:")
            log_semantics(precondition)
            logging.info("\tPostconditions:")
            log_semantics(postcondition)
        
        strips_model.append(strips_data)    

    # Remove duplicated action models with same arguments, preconditions and effects
    deduped_strips_model = dedup(strips_model)

    # Format the output into pddl like syntax
    pddl_model = format_filterd_2_pddl(deduped_strips_model)
    
    # Write the output data to json file
    with open(UNFILTERED_STRIPS_PATH, 'w', encoding="utf-8") as f:
        json.dump(strips_model, f, indent=2)

    with open(FILTERED_STRIPS_PATH, 'w', encoding="utf-8") as f:
        json.dump(deduped_strips_model, f, indent=2)

    with open(EXAMPLE_TEXT_PATH, 'w', encoding="utf-8") as f:
        json.dump(examples, f, indent=2)
    
    with open(PDDL_FILE_PATH, 'w', encoding="utf-8") as f:
        json.dump(pddl_model, f, indent=2)


if __name__ == "__main__":
    main()