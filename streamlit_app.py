import streamlit as st
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.ns import qn
from docx.oxml import OxmlElement # Still useful for some XML additions if needed, but carefully
import io
from datetime import datetime
import re
import zipfile
import logging
import html

# --- Setup Logging ---
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Constants ---
INDENT_FOR_IND_TAG_CM = 1.25 # Base indent for paragraphs marked with [ind]

# Indentation for list levels (these are for the *text* start)
MAIN_LIST_TEXT_START_CM = 1.0 # Where text should start for 1., •
SUB_LIST_TEXT_START_CM = 1.8 # Where text should start for (a), (i)

# Marker offsets (how far the marker is to the left of the text start)
# These are conceptual, the style will handle actual hanging indent
MARKER_OFFSET_CM = 0.6 # A common offset for bullet/number markers

# --- Utility Functions ---
def sanitize_input(text):
    """Sanitizes input to prevent injection or formatting issues."""
    if not isinstance(text, str):
        text = str(text)
    return html.escape(text).replace('\n', ' ').replace('\r', '')

# --- Cached Data Loading ---
@st.cache_data
def load_firm_details():
    """Loads and caches the law firm's details."""
    return {
        "name": "Ramsdens Solicitors LLP",
        "short_name": "Ramsdens",
        "person_responsible_name": "Paul Pinder",
        "person_responsible_title": "Senior Associate",
        "supervisor_name": "Nick Armitage",
        "supervisor_title": "Partner",
        "person_responsible_phone": "01484 821558",
        "person_responsible_mobile": "07923 250815",
        "person_responsible_email": "paul.pinder@ramsdens.co.uk",
        "assistant_name": "Reece Collier",
        "supervisor_contact_for_complaints": "Nick Armitage on 01484 507121",
        "bank_name": "Barclays Bank PLC",
        "bank_address": "17 Market Place, Huddersfield",
        "account_name": "Ramsdens Solicitors LLP Client Account",
        "sort_code": "20-43-12",
        "account_number": "03909026",
        "marketing_email": "dataprotection@ramsdens.co.uk",
        "marketing_address": "Ramsdens Solicitors LLP, Oakley House, 1 Hungerford Road, Edgerton, Huddersfield, HD3 3AL"
    }

@st.cache_data
def load_precedent_text():
    """Loads and caches the precedent text from a file."""
    try:
        with open("precedent.txt", "r", encoding="utf-8") as f:
            content = f.read().strip()
            logger.info("Successfully loaded precedent.txt")
            return content
    except FileNotFoundError:
        st.error("precedent.txt not found. Please ensure the file exists in the same directory.")
        logger.error("precedent.txt not found.")
        return ""
    except Exception as e:
        st.error(f"Error loading precedent.txt: {str(e)}")
        logger.error("Error loading precedent.txt: %s", str(e))
        return ""

# --- Placeholder & Run Formatting ---
def get_placeholder_map(app_inputs, firm_details):
    """Creates a dictionary of all placeholders and their values."""
    placeholders = {
        'qu1_dispute_nature': app_inputs.get('qu1_dispute_nature', ''),
        'qu2_initial_steps': app_inputs.get('qu2_initial_steps', ''),
        'qu3_timescales': app_inputs.get('qu3_timescales', ''),
        'qu4_initial_costs_estimate': app_inputs.get('qu4_initial_costs_estimate', 'XX,XXX'),
        'fee_table': app_inputs.get('fee_table', "Fee table not provided"),
        'our_ref': str(app_inputs.get('our_ref', '')),
        'your_ref': str(app_inputs.get('your_ref', '')),
        'letter_date': str(app_inputs.get('letter_date', '')),
        'client_name_input': str(app_inputs.get('client_name_input', '')),
        'client_address_line1': str(app_inputs.get('client_address_line1', '')),
        'client_address_line2_conditional': str(app_inputs.get('client_address_line2_conditional', '')),
        'client_postcode': str(app_inputs.get('client_postcode', '')),
        'name': str(app_inputs.get('name', '')),
        'matter_number': str(app_inputs.get('our_ref', '')),
    }
    firm_placeholders = {k: str(v) for k, v in firm_details.items()}
    placeholders.update(firm_placeholders)
    logger.debug("Placeholder map created: %s", placeholders)
    return placeholders

def add_formatted_runs(paragraph, text_line, placeholder_map):
    """Adds text runs to a paragraph, processing inline formatting tags and placeholders."""
    try:
        if not isinstance(text_line, str):
            text_line = str(text_line)
            logger.warning("Converted non-string text_line to string: %s", text_line)

        processed_text = text_line
        for placeholder, value in placeholder_map.items():
            placeholder_pattern = f"{{{placeholder}}}"
            if placeholder_pattern in processed_text:
                processed_text = processed_text.replace(placeholder_pattern, str(value))
        
        if '{' in processed_text and '}' in processed_text:
            logger.warning("Unprocessed curly brace placeholders in text after replacement: %s", processed_text)
        
        parts = re.split(r'(\[bd\]|\[/bd\]|\[italics\]|\[/italics\]|\[u\]|\[/u\]|\[underline\]|\[/underline\])', processed_text)
        
        is_bold = False
        is_italic = False
        is_underline = False

        for part in parts:
            if not part:
                continue

            if part == "[bd]":
                is_bold = True
            elif part == "[/bd]":
                is_bold = False
            elif part == "[italics]":
                is_italic = True
            elif part == "[/italics]":
                is_italic = False
            elif part in ["[u]", "[underline]"]:
                is_underline = True
            elif part in ["[/u]", "[/underline]"]:
                is_underline = False
            else:
                run = paragraph.add_run(part)
                run.bold = is_bold
                run.italic = is_italic
                run.underline = is_underline
                run.font.name = 'Arial'
                run.font.size = Pt(11)
        logger.debug(f"Formatted runs added for: '{text_line}' -> '{processed_text}'")
    except Exception as e:
        logger.error(f"Error in add_formatted_runs for text '{text_line}': {str(e)}")
        raise

# --- Conditional Block Logic ---
def should_render_track_block(tag, claim_assigned, selected_track):
    """Determines if a court track block should be rendered based on the tag and inputs."""
    tag_map = {
        'a1': (True, "Small Claims Track"),
        'a2': (True, "Fast Track"),
        'a3': (True, "Intermediate Track"),
        'a4': (True, "Multi Track"),
        'u1': (False, "Small Claims Track"),
        'u2': (False, "Fast Track"),
        'u3': (False, "Intermediate Track"),
        'u4': (False, "Multi Track"),
    }
    expected = tag_map.get(tag)
    if not expected:
        logger.warning(f"Unknown track tag encountered: {tag}. Skipping rendering for safety.")
        return False
    
    expected_assignment, expected_track = expected
    result = (claim_assigned == expected_assignment) and (selected_track == expected_track)
    logger.debug(f"Track block '{tag}' rendering decision: {result} (claim_assigned={claim_assigned}, selected_track='{selected_track}')")
    return result

# --- Document Generation Functions ---
def generate_initial_advice_doc(app_inputs):
    """Generates the Initial Advice Summary Word document."""
    try:
        logger.debug("Generating Initial Advice Summary document.")

        if 'our_ref' not in app_inputs or not app_inputs['our_ref']:
            logger.error("Missing or empty 'our_ref' in app_inputs for Initial Advice Summary.")
            raise ValueError("Missing or empty 'our_ref' in app_inputs.")

        doc = Document()
        doc.styles['Normal'].font.name = 'Arial'
        doc.styles['Normal'].font.size = Pt(11)

        p = doc.add_paragraph()
        p.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
        placeholder_map = get_placeholder_map(app_inputs, app_inputs['firm_details'])
        add_formatted_runs(p, "Initial Advice Summary - Matter Number: {matter_number}", placeholder_map)
        p.paragraph_format.space_after = Pt(12)

        table = doc.add_table(rows=3, cols=2)
        table.style = 'Table Grid'
        table.autofit = True
        
        rows_data = [
            ("Date of Advice", app_inputs.get('initial_advice_date', '').strftime('%d/%m/%Y') if app_inputs.get('initial_advice_date') else ''),
            ("Method of Advice", app_inputs.get('initial_advice_method', '')),
            ("Advice Given", app_inputs.get('initial_advice_content', ''))
        ]
        for i, (label, value) in enumerate(rows_data):
            cells = table.rows[i].cells
            cells[0].text = label
            cells[1].text = value
            for cell in cells:
                for para_in_cell in cell.paragraphs:
                    for run_in_para in para_in_cell.runs:
                        run_in_para.font.name = 'Arial'
                        run_in_para.font.size = Pt(11)
                cell.paragraphs[0].alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
        
        table.columns[0].width = Cm(4.5)
        table.columns[1].width = Cm(10.0)

        doc_io = io.BytesIO()
        doc.save(doc_io)
        doc_io.seek(0)
        logger.info("Initial Advice Summary document successfully generated.")
        return doc_io
    except Exception as e:
        logger.error(f"Failed to generate Initial Advice Summary document: {str(e)}")
        raise

def generate_fee_table(hourly_rate, client_type):
    """Generates a fee table as a list of strings based on hourly rate and client type."""
    roles = [
        ("Partner", hourly_rate * 1.5),
        ("Senior Associate", hourly_rate),
        ("Associate", hourly_rate * 0.8),
        ("Trainee", hourly_rate * 0.5)
    ]
    table_content_lines = []
    for role, rate in roles:
        table_content_lines.append(f"{role}: £{rate:,.2f} per hour (excl. VAT)")
    if client_type == "Corporate":
        table_content_lines.append("Note: Corporate clients may be subject to additional administrative fees.")
    return table_content_lines

def preprocess_precedent(precedent_content, app_inputs):
    """
    Preprocesses the precedent text into a list of logical document elements.
    Each element is a dict containing its 'type', 'content_lines' (list of strings),
    and 'block_tag' (for conditional rendering).
    """
    logical_elements = []
    lines = precedent_content.splitlines()
    i = 0
    
    current_paragraph_lines = [] # Accumulates lines for a single logical paragraph/item
    current_block_tag = None # e.g., 'indiv', 'corp', 'a1', 'u1' for conditional sections

    def add_current_paragraph_block(block_type_to_assign='general_paragraph'):
        nonlocal current_paragraph_lines, current_block_tag
        if current_paragraph_lines:
            cleaned_lines_for_block = []
            for line_in_block in current_paragraph_lines:
                # Stripping [/p] if it exists, as spacing is handled by docx.paragraph_format.space_after
                line_in_block = line_in_block.replace('[/p]', '').strip() 
                cleaned_lines_for_block.append(line_in_block)

            logical_elements.append({
                'type': block_type_to_assign,
                'content_lines': cleaned_lines_for_block,
                'block_tag': current_block_tag
            })
            current_paragraph_lines = [] # Reset for next block

    while i < len(lines):
        line = lines[i] # Use original line for content, stripped_line for tag checking
        stripped_line = line.strip()

        logger.debug(f"Pre-processing line {i}: '{stripped_line}'")

        match_start_tag = re.match(r'\[(indiv|corp|a[1-4]|u[1-4])\]', stripped_line)
        match_end_tag = re.match(r'\[/(indiv|corp|a[1-4]|u[1-4])\]', stripped_line)
        
        if match_start_tag:
            add_current_paragraph_block()
            current_block_tag = match_start_tag.group(1)
            logger.debug(f"Detected START conditional block tag: {current_block_tag}")
        elif match_end_tag:
            add_current_paragraph_block()
            current_block_tag = None
            logger.debug(f"Detected END conditional block tag: {match_end_tag.group(1)}")
        elif stripped_line == '[FEE_TABLE_PLACEHOLDER]':
            add_current_paragraph_block()
            logical_elements.append({
                'type': 'fee_table',
                'content_lines': app_inputs['fee_table'],
                'block_tag': current_block_tag
            })
            logger.debug("Detected FEE_TABLE_PLACEHOLDER.")
        elif stripped_line == '[]':
            add_current_paragraph_block()
            logical_elements.append({
                'type': 'blank_line',
                'content_lines': [],
                'block_tag': current_block_tag
            })
            logger.debug("Detected explicit blank line '[]'.")
        elif stripped_line.startswith('[u]'):
            add_current_paragraph_block()
            logical_elements.append({
                'type': 'heading',
                'content_lines': [stripped_line.replace('[u]', '', 1).strip()],
                'block_tag': current_block_tag
            })
            logger.debug(f"Detected heading: '{stripped_line}'")
        elif stripped_line.startswith('[#]'):
            add_current_paragraph_block()
            logical_elements.append({
                'type': 'numbered_list_item',
                'content_lines': [stripped_line.replace('[#]', '', 1).lstrip()],
                'block_tag': current_block_tag
            })
            logger.debug(f"Detected numbered list item: '{stripped_line}'")
        elif re.match(r'^\[([a-zA-Z])\]', stripped_line):
            add_current_paragraph_block()
            logical_elements.append({
                'type': 'letter_list_item',
                'content_lines': [stripped_line], # Keep original tag for formatting
                'block_tag': current_block_tag
            })
            logger.debug(f"Detected lettered list item: '{stripped_line}'")
        elif re.match(r'^\[(i{1,3}|iv|v|vi|vii)\]', stripped_line):
            add_current_paragraph_block()
            logical_elements.append({
                'type': 'roman_list_item',
                'content_lines': [stripped_line], # Keep original tag for formatting
                'block_tag': current_block_tag
            })
            logger.debug(f"Detected roman list item: '{stripped_line}'")
        elif stripped_line.startswith('[bp]'):
            add_current_paragraph_block()
            logical_elements.append({
                'type': 'bullet_list_item',
                'content_lines': [stripped_line.replace('[bp]', '', 1).lstrip()],
                'block_tag': current_block_tag
            })
            logger.debug(f"Detected bullet list item: '{stripped_line}'")
        elif not stripped_line:
            add_current_paragraph_block()
            logger.debug("Detected empty line (natural paragraph break).")
        else:
            current_paragraph_lines.append(line)
            
        i += 1

    add_current_paragraph_block()

    logger.debug(f"Pre-processing complete. Total logical elements: {len(logical_elements)}")
    return logical_elements


def process_precedent_text(precedent_content, app_inputs, placeholder_map):
    """
    Processes the parsed precedent text elements and adds them to a Word document.
    """
    try:
        doc = Document()
        # Set default font for 'Normal' style
        doc.styles['Normal'].font.name = 'Arial'
        doc.styles['Normal'].font.size = Pt(11)
        doc.styles['Normal'].paragraph_format.space_after = Pt(12) # Default space for normal paragraphs

        # Create/Get numbering definitions for lists
        # python-docx doesn't expose numbering_part for direct xml manipulation easily.
        # Instead, we define styles and let docx generate the underlying numbering.
        # For true continuity and complex lists, external template might be better,
        # but for simple incrementing lists, custom styles can work if linked to basic numbering properties.

        # Ensure a default numbering for each list type
        # For simplicity and to avoid the `numbering_part` error, we will define
        # specific styles for each list type and manually set `numId` and `ilvl`
        # if the style itself doesn't automatically trigger a new list.

        styles = doc.styles

        # Helper to set basic paragraph and font properties for a list style
        def setup_list_style(style_name, base_style_name='Normal'):
            if style_name not in styles:
                new_style = styles.add_style(style_name, WD_STYLE_TYPE.PARAGRAPH)
                new_style.base_style = styles[base_style_name]
                new_style.paragraph_format.space_after = Pt(6) # Smaller space for list items
            return styles[style_name]


        # Define the styles
        numbered_style = setup_list_style('NumberedListCustom')
        letter_style = setup_list_style('LetterListCustom')
        roman_style = setup_list_style('RomanListCustom')
        bullet_style = setup_list_style('BulletListCustom')

        # This is where we need to ensure numbering is properly set up.
        # Python-docx does not provide a high-level API for creating new numbering definitions
        # dynamically beyond basic built-in styles or using templates.
        # The common workaround for custom numbering is to modify the XML directly,
        # but the `numbering_part` error indicates limitations.
        #
        # A more stable approach without a template requires:
        # 1. Manually adding abstractNum and num elements if they don't exist.
        # 2. Setting the pPr/numPr/numId and pPr/numPr/ilvl on each paragraph.
        #
        # Let's create a *single* abstract numbering definition and reuse its ID for all list types,
        # but use different ilvl (level) and numFmt (format) for each. This is a common strategy.
        
        # --- Create a shared abstract numbering definition if not already present ---
        # This part requires careful XML manipulation or using docx.api._document._RelationshipPart
        # The previous error "AttributeError: 'Document' object has no attribute 'numbering_part'"
        # indicated that directly accessing doc.part.document.numbering_part.element is problematic.
        # The correct way to get to the numbering part's XML root is often through the document part.
        
        document_part = doc.part
        if not hasattr(document_part, 'numbering_part'): # Check if it's there, should be for new doc
            # If for some reason it's missing (unlikely for a new docx.Document()), then create it
            from docx.opc.part import PartFactory
            from docx.opc.package import Package
            from docx.parts.numbering import NumberingPart
            # This is complex and usually handled by docx.__init__
            logger.error("Document does not have a numbering_part. This is unexpected for a new document.")
            # For robustness, we could try to add it, but it implies a deeper issue.
            # Sticking to standard API or a template is best.
            raise Exception("Document's numbering part not found, cannot apply custom lists.")


        # Get the numbering XML element
        numbering_elm = doc.part.numbering_part.element
        
        # Find or create abstractNum for our custom lists
        # Use a unique ID that won't clash.
        abstract_num_id = 100 # Arbitrary starting ID
        num_id_counter = 1 # Global counter for numbering instances

        # Define levels within the abstract numbering
        # Level 0 for [#] - decimal
        # Level 1 for [a] - lowerLetter
        # Level 2 for [i] - lowerRoman
        # Level 3 for [bp] - bullet
        
        # Check if our abstract numbering definition already exists to avoid duplication
        # This is simplified; a real check would iterate existing abstractNums
        if not numbering_elm.xpath(f'w:abstractNum[@w:abstractNumId="{abstract_num_id}"]', namespaces=numbering_elm.nsmap):
            new_abstract_num = OxmlElement('w:abstractNum', nsmap=numbering_elm.nsmap)
            new_abstract_num.set(qn('w:abstractNumId'), str(abstract_num_id))
            new_abstract_num.set(qn('w:nsid'), '{0:08X}'.format(abstract_num_id)) # unique NSID

            # Define Level 0 (for [#] - numbered)
            lvl0 = OxmlElement('w:lvl', nsmap=numbering_elm.nsmap)
            lvl0.set(qn('w:ilvl'), '0')
            lvl0.append(OxmlElement('w:numFmt', nsmap=numbering_elm.nsmap, val='decimal'))
            lvl0.append(OxmlElement('w:lvlText', nsmap=numbering_elm.nsmap, val='%1.'))
            lvl0.append(OxmlElement('w:lvlJc', nsmap=numbering_elm.nsmap, val='left'))
            
            pPr0 = OxmlElement('w:pPr', nsmap=numbering_elm.nsmap)
            ind0 = OxmlElement('w:ind', nsmap=numbering_elm.nsmap, left=str(Cm(MAIN_LIST_TEXT_START_CM).twips), hanging=str(Cm(MARKER_OFFSET_CM).twips))
            pPr0.append(ind0)
            lvl0.append(pPr0)
            new_abstract_num.append(lvl0)

            # Define Level 1 (for [a] - lowerLetter)
            lvl1 = OxmlElement('w:lvl', nsmap=numbering_elm.nsmap)
            lvl1.set(qn('w:ilvl'), '1')
            lvl1.append(OxmlElement('w:numFmt', nsmap=numbering_elm.nsmap, val='lowerLetter'))
            lvl1.append(OxmlElement('w:lvlText', nsmap=numbering_elm.nsmap, val='(%1)')) # Use %1 for current level
            lvl1.append(OxmlElement('w:lvlJc', nsmap=numbering_elm.nsmap, val='left'))
            pPr1 = OxmlElement('w:pPr', nsmap=numbering_elm.nsmap)
            ind1 = OxmlElement('w:ind', nsmap=numbering_elm.nsmap, left=str(Cm(SUB_LIST_TEXT_START_CM).twips), hanging=str(Cm(MARKER_OFFSET_CM).twips))
            pPr1.append(ind1)
            lvl1.append(pPr1)
            new_abstract_num.append(lvl1)

            # Define Level 2 (for [i] - lowerRoman)
            lvl2 = OxmlElement('w:lvl', nsmap=numbering_elm.nsmap)
            lvl2.set(qn('w:ilvl'), '2')
            lvl2.append(OxmlElement('w:numFmt', nsmap=numbering_elm.nsmap, val='lowerRoman'))
            lvl2.append(OxmlElement('w:lvlText', nsmap=numbering_elm.nsmap, val='(%1)')) # Use %1 for current level
            lvl2.append(OxmlElement('w:lvlJc', nsmap=numbering_elm.nsmap, val='left'))
            pPr2 = OxmlElement('w:pPr', nsmap=numbering_elm.nsmap)
            ind2 = OxmlElement('w:ind', nsmap=numbering_elm.nsmap, left=str(Cm(SUB_LIST_TEXT_START_CM + 0.8).twips), hanging=str(Cm(MARKER_OFFSET_CM).twips)) # Deeper indent for roman
            pPr2.append(ind2)
            lvl2.append(pPr2)
            new_abstract_num.append(lvl2)

            # Define Level 3 (for [bp] - bullet)
            lvl3 = OxmlElement('w:lvl', nsmap=numbering_elm.nsmap)
            lvl3.set(qn('w:ilvl'), '3')
            lvl3.append(OxmlElement('w:numFmt', nsmap=numbering_elm.nsmap, val='bullet'))
            lvl3.append(OxmlElement('w:lvlText', nsmap=numbering_elm.nsmap, val='•'))
            lvl3.append(OxmlElement('w:lvlJc', nsmap=numbering_elm.nsmap, val='left'))
            pPr3 = OxmlElement('w:pPr', nsmap=numbering_elm.nsmap)
            ind3 = OxmlElement('w:ind', nsmap=numbering_elm.nsmap, left=str(Cm(MAIN_LIST_TEXT_START_CM).twips), hanging=str(Cm(MARKER_OFFSET_CM).twips))
            pPr3.append(ind3)
            lvl3.append(pPr3)
            new_abstract_num.append(lvl3)


            numbering_elm.append(new_abstract_num)

        # Create the actual numbering instance if it doesn't exist
        # This links to the abstract definition.
        num_instance_id = 1 # A simple, stable ID for the numbering instance
        if not numbering_elm.xpath(f'w:num[@w:numId="{num_instance_id}"]', namespaces=numbering_elm.nsmap):
            new_num = OxmlElement('w:num', nsmap=numbering_elm.nsmap)
            new_num.set(qn('w:numId'), str(num_instance_id))
            abstract_num_id_ref = OxmlElement('w:abstractNumId', nsmap=numbering_elm.nsmap)
            abstract_num_id_ref.set(qn('w:val'), str(abstract_num_id))
            new_num.append(abstract_num_id_ref)
            numbering_elm.append(new_num)
        
        # --- End Numbering Setup ---

        logical_elements = preprocess_precedent(precedent_content, app_inputs)
        
        for element in logical_elements:
            logger.debug(f"Rendering element: Type={element['type']}, Tag={element['block_tag']}, Content={element['content_lines']}")

            render_this_element = True
            if element['block_tag']:
                if element['block_tag'] in ['indiv', 'corp']:
                    if (element['block_tag'] == 'indiv' and app_inputs['client_type'] != 'Individual') or \
                       (element['block_tag'] == 'corp' and app_inputs['client_type'] != 'Corporate'):
                        render_this_element = False
                elif element['block_tag'] in ['a1', 'a2', 'a3', 'a4', 'u1', 'u2', 'u3', 'u4']:
                    if not should_render_track_block(element['block_tag'], app_inputs['claim_assigned'], app_inputs['selected_track']):
                        render_this_element = False
            
            if not render_this_element:
                logger.debug(f"Skipping element: Type={element['type']}, Tag={element['block_tag']} due to conditional logic.")
                continue

            # --- Add content to document based on element type ---
            if element['type'] == 'blank_line':
                p = doc.add_paragraph()
                p.paragraph_format.space_after = Pt(12)
            
            elif element['type'] == 'fee_table':
                for fee_line in element['content_lines']:
                    p = doc.add_paragraph()
                    pf = p.paragraph_format
                    pf.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
                    add_formatted_runs(p, fee_line, placeholder_map)
                    pf.space_after = Pt(6)
                if doc.paragraphs:
                    doc.paragraphs[-1].paragraph_format.space_after = Pt(12)
            
            elif element['type'] == 'heading':
                p = doc.add_paragraph()
                p.style = 'Heading 2'
                add_formatted_runs(p, element['content_lines'][0], placeholder_map)
                p.paragraph_format.space_before = Pt(12)
                p.paragraph_format.space_after = Pt(6)

            elif element['type'] == 'numbered_list_item':
                p = doc.add_paragraph(style='NumberedListCustom') # Apply custom style
                p.paragraph_format.set_attribute(qn('w:numId'), str(num_instance_id)) # Link to numbering instance
                p.paragraph_format.set_attribute(qn('w:ilvl'), '0') # Set level 0 for this type

                pf = p.paragraph_format
                pf.alignment = WD_PARAGRAPH_ALIGNMENT.JUSTIFY
                
                text_content = element['content_lines'][0]
                is_indented = '[ind]' in text_content
                cleaned_text = text_content.replace('[ind]', '').strip()

                if is_indented:
                    # Apply additional indent for [ind] on top of list style's indent
                    pf.left_indent = Cm(MAIN_LIST_TEXT_START_CM + INDENT_FOR_IND_TAG_CM)
                    pf.first_line_indent = Cm(-MAIN_LIST_FIRST_LINE_OFFSET_CM) # Keep hanging
                    pf.tab_stops.add_tab_stop(Cm(MAIN_LIST_TEXT_START_CM + INDENT_FOR_IND_TAG_CM))

                add_formatted_runs(p, cleaned_text, placeholder_map)

            elif element['type'] == 'letter_list_item':
                p = doc.add_paragraph(style='LetterListCustom')
                p.paragraph_format.set_attribute(qn('w:numId'), str(num_instance_id))
                p.paragraph_format.set_attribute(qn('w:ilvl'), '1') # Level 1 for letters

                pf = p.paragraph_format
                pf.alignment = WD_PARAGRAPH_ALIGNMENT.JUSTIFY

                text_content = element['content_lines'][0]
                is_indented = '[ind]' in text_content
                cleaned_content_stripped_tag = re.sub(r'^\[([a-zA-Z])\]\s*', '', text_content).strip()

                if is_indented:
                    pf.left_indent = Cm(SUB_LIST_TEXT_START_CM + INDENT_FOR_IND_TAG_CM)
                    pf.first_line_indent = Cm(-SUB_LIST_FIRST_LINE_OFFSET_CM)
                    pf.tab_stops.add_tab_stop(Cm(SUB_LIST_TEXT_START_CM + INDENT_FOR_IND_TAG_CM))
                
                add_formatted_runs(p, cleaned_content_stripped_tag, placeholder_map)

            elif element['type'] == 'roman_list_item':
                p = doc.add_paragraph(style='RomanListCustom')
                p.paragraph_format.set_attribute(qn('w:numId'), str(num_instance_id))
                p.paragraph_format.set_attribute(qn('w:ilvl'), '2') # Level 2 for roman

                pf = p.paragraph_format
                pf.alignment = WD_PARAGRAPH_ALIGNMENT.JUSTIFY

                text_content = element['content_lines'][0]
                is_indented = '[ind]' in text_content
                cleaned_content_stripped_tag = re.sub(r'^\[(i{1,3}|iv|v|vi|vii)\]\s*', '', text_content).strip()

                if is_indented:
                    # Adjust if deeper indent is intended for roman + [ind]
                    pf.left_indent = Cm(SUB_LIST_TEXT_START_CM + INDENT_FOR_IND_TAG_CM + 0.8) # Arbitrary extra indent for deeper level
                    pf.first_line_indent = Cm(-SUB_LIST_FIRST_LINE_OFFSET_CM)
                    pf.tab_stops.add_tab_stop(Cm(SUB_LIST_TEXT_START_CM + INDENT_FOR_IND_TAG_CM + 0.8))

                add_formatted_runs(p, cleaned_content_stripped_tag, placeholder_map)
            
            elif element['type'] == 'bullet_list_item':
                p = doc.add_paragraph(style='BulletListCustom')
                p.paragraph_format.set_attribute(qn('w:numId'), str(num_instance_id))
                p.paragraph_format.set_attribute(qn('w:ilvl'), '3') # Level 3 for bullet

                pf = p.paragraph_format
                pf.alignment = WD_PARAGRAPH_ALIGNMENT.JUSTIFY

                text_content = element['content_lines'][0]
                is_indented = '[ind]' in text_content
                cleaned_content = text_content.replace('[ind]', '').strip()

                if is_indented:
                    pf.left_indent = Cm(MAIN_LIST_TEXT_START_CM + INDENT_FOR_IND_TAG_CM)
                    pf.first_line_indent = Cm(-MAIN_LIST_FIRST_LINE_OFFSET_CM)
                    pf.tab_stops.add_tab_stop(Cm(MAIN_LIST_TEXT_START_CM + INDENT_FOR_IND_TAG_CM))

                add_formatted_runs(p, cleaned_content, placeholder_map)

            elif element['type'] == 'general_paragraph':
                p = doc.add_paragraph()
                pf = p.paragraph_format
                pf.alignment = WD_PARAGRAPH_ALIGNMENT.JUSTIFY
                
                has_ind_tag = any('[ind]' in line for line in element['content_lines'])
                combined_text_content = " ".join([line.replace('[ind]', '').strip() for line in element['content_lines']])
                
                if has_ind_tag:
                    pf.left_indent = Cm(INDENT_FOR_IND_TAG_CM)

                add_formatted_runs(p, combined_text_content, placeholder_map)
                pf.space_after = Pt(12)

        if doc.paragraphs and doc.paragraphs[-1].paragraph_format.space_after == Pt(0):
            doc.paragraphs[-1].paragraph_format.space_after = Pt(6)

        logger.info("Client Care Letter document content processed into Word document.")
        return doc
    except Exception as e:
        logger.error(f"Error processing precedent text into Word document: {str(e)}")
        raise

# --- Streamlit App UI ---
st.set_page_config(layout="wide", page_title="Ramsdens Client Care Letter Generator")

# --- Custom CSS ---
st.markdown("""
<style>
    .stApp {
        background-color: #1E1E1E;
        color: #FFFFFF;
    }
    .stButton>button {
        background-color: #0078D4;
        color: white;
        border-radius: 5px;
        padding: 10px 20px;
        border: 1px solid #005A9E;
        font-size: 16px;
    }
    .stButton>button:hover {
        background-color: #005A9E;
    }
    h1, h2, h3 {
        color: #FFFFFF;
    }
    .stTextInput, .stTextArea, .stDateInput, .stSelectbox, .stNumberInput {
        border-radius: 5px;
        border: 1px solid #888;
    }
    .stForm {
        background-color: #2D2D2D;
        padding: 2em;
        border-radius: 10px;
        border: 1px solid #444;
        box-shadow: 0 4px 8px rgba(0,0,0,0.4);
    }
    div[data-baseweb="input"] > input, 
    div[data-baseweb="textarea"] > textarea {
        background-color: #333333;
        color: #FFFFFF;
    }
    div[data-baseweb="select"] > div {
        background-color: #333333;
        color: #FFFFFF;
    }
    .stRadio > label {
        color: #FFFFFF !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("Ramsdens Client Care Letter Generator")

firm_details = load_firm_details()
precedent_content = load_precedent_text()

if not precedent_content:
    st.error("Precedent text could not be loaded. Please check 'precedent.txt' file.")
    st.stop()

with st.form("input_form"):
    st.header("1. Letter & Client Details")
    col1, col2 = st.columns(2)
    with col1:
        our_ref = st.text_input("Our Reference", "PDP/10011/001")
        your_ref = st.text_input("Your Reference (if any)", "REF")
        letter_date = st.date_input("Letter Date", datetime.today())
    with col2:
        client_name_input = st.text_input("Client Full Name / Company Name", "Mr. John Smith")
        client_address_line1 = st.text_input("Client Address Line 1", "123 Example Street")
        client_address_line2 = st.text_input("Client Address Line 2", "SomeTown")
        client_postcode = st.text_input("Client Postcode", "EX4 MPL")
        client_type = st.radio("Client Type", ("Individual", "Corporate"), horizontal=True)

    st.markdown("---")
    st.header("2. Initial Advice & Case Details")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Initial Advice")
        initial_advice_content = st.text_area("Initial Advice Given", "Advised on the merits of the claim and potential next steps.", height=100)
        initial_advice_method = st.selectbox("Method of Initial Advice", ["Phone Call", "In Person", "Teams Call"])
        initial_advice_date = st.date_input("Date of Initial Advice", datetime.today())
    with col2:
        st.subheader("Case Track")
        claim_assigned_input = st.radio("Is the claim already assigned to a court track?", ("Yes", "No"), horizontal=True)
        track_options = ["Small Claims Track", "Fast Track", "Intermediate Track", "Multi Track"]
        selected_track = st.selectbox("Which court track applies or is anticipated?", track_options)

    st.markdown("---")
    st.header("3. Dynamic Content for Letter")
    qu1_dispute_nature = st.text_area('**Dispute Nature:** We are instructed in relation to...', "a contractual matter where you wish to bring a claim against your landlord", height=75, help='Define the core of the dispute.')
    qu2_initial_steps = st.text_area('**Initial Work:** Per our recent discussions, we agreed to...', "review the documentation you have provided and advise you on the merits of your case and set out the next steps", height=150, help='Set out the initial work you agreed to do.')
    qu3_timescales = st.text_area("**Estimated Timescales:**", "We estimate that to complete the initial advice for you we will take approximately two to four weeks to complete. Obviously, where other parties are involved this will depend on the complexity of the matter and the responsiveness of other parties. We will keep you updated on progress.", height=100)
    
    st.subheader("Estimated Initial Costs")
    hourly_rate = st.number_input("Your Hourly Rate (£)", value=295, min_value=0, step=10)
    cost_step = hourly_rate / 2 if hourly_rate > 0 else 50

    cost_type_is_range = st.toggle("Use a cost range", value=True)

    if cost_type_is_range:
        default_lower = 2 * hourly_rate
        default_upper = 3 * hourly_rate
        col1, col2 = st.columns(2)
        with col1:
            lower_cost_estimate = st.number_input("Lower estimate (£)", value=float(default_lower), step=float(cost_step))
        with col2:
            upper_cost_estimate = st.number_input("Upper estimate (£)", value=float(default_upper), step=float(cost_step))
    else:
        default_fixed = (2 * hourly_rate + 3 * hourly_rate) / 2
        fixed_cost_estimate = st.number_input("Fixed cost estimate (£)", value=float(default_fixed), step=float(cost_step))

    submitted = st.form_submit_button("Generate Documents")

if submitted:
    vat_rate = 0.20

    if 'lower_cost_estimate' in locals() and 'upper_cost_estimate' in locals():
        lower_cost_vat = lower_cost_estimate * vat_rate
        upper_cost_vat = upper_cost_estimate * vat_rate
        lower_cost_total = lower_cost_estimate + lower_cost_vat
        upper_cost_total = upper_cost_estimate + upper_cost_vat
        costs_text = (
            f"£{lower_cost_estimate:,.2f} to £{upper_cost_estimate:,.2f} plus VAT "
            f"(currently standing at 20% but subject to change by the government) "
            f"which at the current rate would be £{lower_cost_total:,.2f} to £{upper_cost_total:,.2f} with VAT included."
        )
    elif 'fixed_cost_estimate' in locals():
        fixed_cost_vat = fixed_cost_estimate * vat_rate
        fixed_cost_total = fixed_cost_estimate + fixed_cost_vat
        costs_text = (
            f"a fixed fee of £{fixed_cost_estimate:,.2f} plus VAT "
            f"(currently standing at 20% but subject to change by the government) "
            f"which at the current rate would be £{fixed_cost_total:,.2f} with VAT included."
        )
    else:
        costs_text = "[COSTING INFORMATION TO BE CONFIRMED]"

    fee_table_lines = generate_fee_table(hourly_rate, client_type)

    app_inputs = {
        'qu1_dispute_nature': sanitize_input(qu1_dispute_nature),
        'qu2_initial_steps': sanitize_input(qu2_initial_steps),
        'qu3_timescales': sanitize_input(qu3_timescales),
        'qu4_initial_costs_estimate': sanitize_input(costs_text),
        'fee_table': fee_table_lines,
        'client_type': client_type,
        'claim_assigned': claim_assigned_input == "Yes",
        'selected_track': selected_track,
        'our_ref': sanitize_input(our_ref),
        'your_ref': sanitize_input(your_ref),
        'letter_date': letter_date.strftime('%d %B %Y'),
        'client_name_input': sanitize_input(client_name_input),
        'client_address_line1': sanitize_input(client_address_line1),
        'client_address_line2_conditional': sanitize_input(client_address_line2) if client_address_line2 else "",
        'client_postcode': sanitize_input(client_postcode),
        'name': sanitize_input(firm_details["person_responsible_name"]),
        'initial_advice_content': sanitize_input(initial_advice_content),
        'initial_advice_method': initial_advice_method,
        'initial_advice_date': initial_advice_date,
        'firm_details': {k: sanitize_input(v) for k, v in firm_details.items()}
    }

    required_inputs = ['qu1_dispute_nature', 'qu2_initial_steps', 'qu3_timescales', 'qu4_initial_costs_estimate', 'our_ref', 'client_name_input']
    for key in required_inputs:
        if not app_inputs.get(key):
            st.error(f"Missing or empty input for '{key}'. Please fill in all required fields.")
            logger.error(f"Validation failed: Missing or empty input for '{key}'.")
            st.stop()

    placeholder_map = get_placeholder_map(app_inputs, firm_details)

    try:
        doc = process_precedent_text(precedent_content, app_inputs, placeholder_map)
        logger.info("Client Care Letter document successfully assembled.")
    except Exception as e:
        st.error(f"An error occurred while building the Client Care Letter: {str(e)}")
        logger.exception("Error during Client Care Letter generation:")
        st.stop()

    client_care_doc_io = io.BytesIO()
    doc.save(client_care_doc_io)
    client_care_doc_io.seek(0)
    logger.info("Client Care Letter saved to BytesIO.")

    try:
        advice_doc_io = generate_initial_advice_doc(app_inputs)
        logger.info("Initial Advice Summary document successfully generated.")
    except Exception as e:
        st.warning(f"Failed to generate Initial Advice Summary document: {str(e)}")
        logger.exception("Error during Initial Advice Summary generation:")
        advice_doc_io = None

    client_name_safe = client_name_input.replace(' ', '_').replace('.', '')

    zip_io = io.BytesIO()
    with zipfile.ZipFile(zip_io, 'w', zipfile.ZIP_DEFLATED) as zipf:
        if client_care_doc_io:
            zipf.writestr(f"Client_Care_Letter_{client_name_safe}.docx", client_care_doc_io.getvalue())
        if advice_doc_io:
            zipf.writestr(f"Initial_Advice_Summary_{client_name_safe}.docx", advice_doc_io.getvalue())
    zip_io.seek(0)

    if client_care_doc_io or advice_doc_io:
        st.success("Documents Generated Successfully!")
        st.download_button(
            label="Download All Documents as ZIP",
            data=zip_io,
            file_name=f"Client_Documents_{client_name_safe}.zip",
            mime="application/zip"
        )
    else:
        st.error("No documents could be generated. Please check inputs and logs for errors.")
