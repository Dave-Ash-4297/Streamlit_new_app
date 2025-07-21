import streamlit as st
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.enum.style import WD_STYLE_TYPE
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
INDENT_FOR_IND_TAG_CM = 1.25
SUB_LETTER_HANGING_OFFSET_CM = 0.7
SUB_LETTER_TEXT_INDENT_NO_IND_CM = 0.7
SUB_LETTER_TEXT_START_CM = 1.4
SUB_ROMAN_TEXT_INDENT_CM = 1.4
SUB_ROMAN_TEXT_START_CM = 2.1
NESTED_BULLET_INDENT_CM = INDENT_FOR_IND_TAG_CM + 0.5

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

# --- Document Generation Helpers ---
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

        logger.debug("Placeholder map in add_formatted_runs: %s", placeholder_map)

        processed_text = text_line
        for placeholder, value in placeholder_map.items():
            # Only handle {placeholder} syntax
            placeholder_pattern = f"{{{placeholder}}}"
            if placeholder_pattern in processed_text:
                logger.debug("Replacing placeholder '%s' with value '%s'", placeholder_pattern, value)
                processed_text = processed_text.replace(placeholder_pattern, str(value))
        
        if '{' in processed_text and '}' in processed_text:
            logger.warning("Unprocessed curly brace placeholders in text: %s", processed_text)
        
        # Handle formatting tags
        # Updated regex to match new custom list tags for bullet, letter, roman
        parts = re.split(r'(\[bd\]|\[/bd\]|\[italics\]|\[/italics\]|\[u\]|\[/u\]|\[underline\]|\[/underline\]|\[bp\]|\[/bp\]|\[l\]|\[/l\]|\[r\]|\[/r\])', processed_text)
        is_bold = is_italic = is_underline = False
        
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
            elif part in ["[bp]", "[/bp]", "[l]", "[/l]", "[r]", "[/r]"]: # These are handled by paragraph styling, not inline runs
                continue 
            else:
                run = paragraph.add_run(part)
                run.bold = is_bold
                run.italic = is_italic
                run.underline = is_underline
                run.font.name = 'Arial' # Standard font for content
                run.font.size = Pt(11)
        logger.debug("Processed formatted runs for text: %s", processed_text)
    except Exception as e:
        logger.error("Error in add_formatted_runs for text '%s': %s", text_line, str(e))
        raise

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
        logger.debug("Unknown track tag: %s", tag)
        return False
    expected_assignment, expected_track = expected
    result = claim_assigned == expected_assignment and selected_track == expected_track
    logger.debug("Track block %s rendering: %s (claim_assigned=%s, selected_track=%s)", tag, result, claim_assigned, selected_track)
    return result

def generate_initial_advice_doc(app_inputs):
    """Generates the Initial Advice Summary Word document."""
    try:
        logger.debug("App inputs in generate_initial_advice_doc: %s", app_inputs)

        if 'our_ref' not in app_inputs or not app_inputs['our_ref']:
            logger.error("Missing or empty our_ref in app_inputs")
            raise ValueError("Missing or empty our_ref in app_inputs")

        doc = Document()
        # Define a standard paragraph style
        obj_styles = doc.styles
        obj_charstyle = obj_styles.add_style('NormalPara', WD_STYLE_TYPE.PARAGRAPH)
        obj_font = obj_charstyle.font
        obj_font.size = Pt(11)
        obj_font.name = 'Arial' # Changed to Arial for consistency with run font

        p = doc.add_paragraph()
        p.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
        placeholder_map = get_placeholder_map(app_inputs, app_inputs['firm_details'])

        if 'matter_number' not in placeholder_map:
            logger.error("matter_number not found in placeholder_map")
            raise ValueError("matter_number not found in placeholder_map")

        add_formatted_runs(p, "Initial Advice Summary - Matter Number: {matter_number}", placeholder_map)
        p.paragraph_format.space_after = Pt(12)

        table = doc.add_table(rows=3, cols=2)
        table.style = 'Table Grid'
        table.autofit = True
        rows = [
            ("Date of Advice", app_inputs.get('initial_advice_date', '').strftime('%d/%m/%Y') if app_inputs.get('initial_advice_date') else ''),
            ("Method of Advice", app_inputs.get('initial_advice_method', '')),
            ("Advice Given", app_inputs.get('initial_advice_content', ''))
        ]
        for i, (label, value) in enumerate(rows):
            cells = table.rows[i].cells
            cells[0].text = label
            cells[1].text = value
            for cell in cells:
                cell.paragraphs[0].style.font.name = 'Arial'
                cell.paragraphs[0].style.font.size = Pt(11)
                cell.paragraphs[0].alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
        table.columns[0].width = Cm(4.5)
        table.columns[1].width = Cm(10.0)

        doc_io = io.BytesIO()
        doc.save(doc_io)
        doc_io.seek(0)
        logger.info("Initial Advice Summary document generated.")
        return doc_io
    except Exception as e:
        logger.error("Error generating Initial Advice Summary: %s", str(e))
        raise

def generate_fee_table(hourly_rate, client_type):
    """Generates a fee table as a string based on hourly rate and client type."""
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
    return table_content_lines # Return as a list of lines

def preprocess_precedent(precedent_content, app_inputs):
    """Preprocesses the precedent text into logical document elements."""
    logical_elements = []
    lines = precedent_content.splitlines()
    i = 0
    current_block_type = None # 'conditional_client', 'conditional_track', 'general'
    current_block_tag = None # e.g., 'indiv', 'corp', 'a1', 'u1'
    current_paragraph_lines = []
    
    # Helper to add a completed paragraph block
    def add_current_paragraph_block():
        nonlocal current_paragraph_lines
        if current_paragraph_lines:
            logical_elements.append({
                'type': 'paragraph_block',
                'content_lines': list(current_paragraph_lines), # Use a copy
                'block_type': current_block_type,
                'block_tag': current_block_tag
            })
            current_paragraph_lines = []

    while i < len(lines):
        line = lines[i].strip()
        logger.debug("Preprocessing line %d: %s", i, line)

        # Handle block start/end tags for client type or court track
        if re.match(r'\[(indiv|corp|a[1-4]|u[1-4])\]', line):
            add_current_paragraph_block() # End previous block if any
            current_block_type = 'conditional_client' if line in ['[indiv]', '[corp]'] else 'conditional_track'
            current_block_tag = line[1:-1]
            logger.debug(f"Started new conditional block: {current_block_type}, tag: {current_block_tag}")
        elif re.match(r'\[/(indiv|corp|a[1-4]|u[1-4])\]', line):
            add_current_paragraph_block() # End the conditional block
            current_block_type = None
            current_block_tag = None
            logger.debug("Ended conditional block.")
        elif line == '[FEE_TABLE_PLACEHOLDER]':
            add_current_paragraph_block() # End current text block before inserting table
            logical_elements.append({
                'type': 'fee_table',
                'content': app_inputs['fee_table'], # This is already the processed list of lines
                'block_type': current_block_type, # Propagate conditional context
                'block_tag': current_block_tag
            })
            logger.debug("Inserted FEE_TABLE_PLACEHOLDER.")
        elif line == '[]': # Explicit blank line
            add_current_paragraph_block() # End current text block to ensure blank line is separate
            logical_elements.append({
                'type': 'blank_line',
                'block_type': current_block_type,
                'block_tag': current_block_tag
            })
            logger.debug("Inserted blank line marker.")
        elif line.startswith('[#]'):
            add_current_paragraph_block() # End previous paragraph block
            # Start a new numbered paragraph block
            current_paragraph_lines.append(line.replace('[#]', '', 1).strip()) # Remove [#] from line content
            logical_elements.append({
                'type': 'numbered_paragraph_block',
                'content_lines': list(current_paragraph_lines),
                'block_type': current_block_type,
                'block_tag': current_block_tag
            })
            current_paragraph_lines = [] # Reset for next block
        elif line.startswith('[u]'): # Heading
            add_current_paragraph_block()
            current_paragraph_lines.append(line.replace('[u]', '', 1).strip())
            logical_elements.append({
                'type': 'heading_block',
                'content_lines': list(current_paragraph_lines),
                'block_type': current_block_type,
                'block_tag': current_block_tag
            })
            current_paragraph_lines = []
        elif line.startswith('[bp]'): # Bullet point
            add_current_paragraph_block()
            current_paragraph_lines.append(line.replace('[bp]', '', 1).strip())
            logical_elements.append({
                'type': 'bullet_paragraph_block',
                'content_lines': list(current_paragraph_lines),
                'block_type': current_block_type,
                'block_tag': current_block_tag
            })
            current_paragraph_lines = []
        elif re.match(r'^\[([a-zA-Z])\]', line): # Lettered list item
            add_current_paragraph_block()
            current_paragraph_lines.append(line)
            logical_elements.append({
                'type': 'letter_list_item_block',
                'content_lines': list(current_paragraph_lines),
                'block_type': current_block_type,
                'block_tag': current_block_tag
            })
            current_paragraph_lines = []
        elif re.match(r'^\[(i{1,3}|iv|v|vi|vii)\]', line): # Roman list item
            add_current_paragraph_block()
            current_paragraph_lines.append(line)
            logical_elements.append({
                'type': 'roman_list_item_block',
                'content_lines': list(current_paragraph_lines),
                'block_type': current_block_type,
                'block_tag': current_block_tag
            })
            current_paragraph_lines = []
        elif not line.strip(): # Empty line (not explicit '[]')
            add_current_paragraph_block() # Treat as paragraph end for normal text
            logical_elements.append({
                'type': 'blank_line',
                'block_type': current_block_type,
                'block_tag': current_block_tag
            })
        else: # Regular content line
            current_paragraph_lines.append(line)
            # if this is the last line or the next line is a special tag, add the block
            if i == len(lines) - 1 or re.match(r'\[(indiv|corp|a[1-4]|u[1-4]|/\w+|FEE_TABLE_PLACEHOLDER|\[\]|\[#\]|\[u\]|\[bp\]|\[[a-zA-Z]\]|\[i{1,3}|iv|v|vi|vii\])', lines[i+1].strip()):
                 add_current_paragraph_block()


        i += 1

    add_current_paragraph_block() # Add any remaining paragraph lines

    logger.debug("Logical elements created: %s", logical_elements)
    return logical_elements

def process_precedent_text(precedent_content, app_inputs, placeholder_map):
    """Processes the precedent text and returns a Document object."""
    try:
        doc = Document()
        doc.styles['Normal'].font.name = 'HelveticaNeueLT Pro 45 Lt'
        doc.styles['Normal'].font.size = Pt(11)

        # Custom paragraph styles for lists
        styles = doc.styles
        # Numbered List Style
        if 'NumberedList' not in styles:
            num_style = styles.add_style('NumberedList', WD_STYLE_TYPE.PARAGRAPH)
            num_style.base_style = styles['Normal']
            num_format = num_style.paragraph_format
            num_format.left_indent = Cm(0.7)
            num_format.first_line_indent = Cm(-0.7)
            num_format.tab_stops.add_tab_stop(Cm(0.7))
            num_format.space_after = Pt(6) # Smaller space after for list items
        
        # Letter List Style (e.g., (a), (b))
        if 'LetterList' not in styles:
            letter_style = styles.add_style('LetterList', WD_STYLE_TYPE.PARAGRAPH)
            letter_style.base_style = styles['Normal']
            letter_format = letter_style.paragraph_format
            letter_format.left_indent = Cm(SUB_LETTER_TEXT_START_CM)
            letter_format.first_line_indent = Cm(SUB_LETTER_TEXT_INDENT_NO_IND_CM - SUB_LETTER_TEXT_START_CM) # Negative for hanging indent
            letter_format.tab_stops.add_tab_stop(Cm(SUB_LETTER_TEXT_START_CM))
            letter_format.space_after = Pt(6)

        # Roman List Style (e.g., (i), (ii))
        if 'RomanList' not in styles:
            roman_style = styles.add_style('RomanList', WD_STYLE_TYPE.PARAGRAPH)
            roman_style.base_style = styles['Normal']
            roman_format = roman_style.paragraph_format
            roman_format.left_indent = Cm(SUB_ROMAN_TEXT_START_CM)
            roman_format.first_line_indent = Cm(SUB_ROMAN_TEXT_INDENT_CM - SUB_ROMAN_TEXT_START_CM) # Negative for hanging indent
            roman_format.tab_stops.add_tab_stop(Cm(SUB_ROMAN_TEXT_START_CM))
            roman_format.space_after = Pt(6)


        logical_elements = preprocess_precedent(precedent_content, app_inputs)
        
        # Track current conditional block state
        in_indiv_block = False
        in_corp_block = False
        active_track_block_tag = None

        for element in logical_elements:
            # Check conditional rendering for current element
            render_this_element = True
            if element['block_type'] == 'conditional_client':
                if element['block_tag'] == 'indiv' and app_inputs['client_type'] != 'Individual':
                    render_this_element = False
                elif element['block_tag'] == 'corp' and app_inputs['client_type'] != 'Corporate':
                    render_this_element = False
            elif element['block_type'] == 'conditional_track':
                if not should_render_track_block(element['block_tag'], app_inputs['claim_assigned'], app_inputs['selected_track']):
                    render_this_element = False
            
            if not render_this_element:
                logger.debug(f"Skipping element due to conditional logic: {element['type']}, tag: {element['block_tag']}")
                continue
            
            # Process element based on its type
            if element['type'] == 'blank_line':
                # Add an empty paragraph to create a blank line
                p = doc.add_paragraph()
                p.paragraph_format.space_after = Pt(12) # Ensure space after blank line
                continue
            elif element['type'] == 'fee_table':
                for line in element['content']: # Iterate over lines from generate_fee_table
                    p = doc.add_paragraph()
                    add_formatted_runs(p, line, placeholder_map)
                    p.paragraph_format.space_after = Pt(6) # Small space between fee table lines
                p.paragraph_format.space_after = Pt(12) # Larger space after the whole table
                continue
            
            # For all paragraph-based blocks
            for line_content in element['content_lines']:
                p = doc.add_paragraph()
                pf = p.paragraph_format
                pf.alignment = WD_PARAGRAPH_ALIGNMENT.JUSTIFY
                pf.tab_stops.clear_all() # Clear existing tab stops to avoid interference

                is_indented = '[ind]' in line_content
                cleaned_line_content = line_content.replace('[ind]', '').strip()
                
                # Apply base indentation if [ind] is present
                if is_indented:
                    pf.left_indent = Cm(INDENT_FOR_IND_TAG_CM)

                # Process different block types
                if element['type'] == 'numbered_paragraph_block':
                    p.style = 'NumberedList'
                    add_formatted_runs(p, cleaned_line_content, placeholder_map)
                elif element['type'] == 'heading_block':
                    p.style = 'Heading 2'
                    pf.space_before = Pt(12)
                    pf.space_after = Pt(6)
                    add_formatted_runs(p, cleaned_line_content, placeholder_map)
                elif element['type'] == 'bullet_paragraph_block':
                    p.style = 'List Bullet'
                    # Bullet indentation needs to consider if it's also [ind]
                    if is_indented:
                        pf.left_indent = Cm(NESTED_BULLET_INDENT_CM)
                    else:
                         pf.left_indent = Cm(0.7) # Standard bullet indent
                    add_formatted_runs(p, cleaned_line_content, placeholder_map)
                    pf.space_after = Pt(6) # Smaller space after bullet points
                elif element['type'] == 'letter_list_item_block':
                    p.style = 'LetterList'
                    match = re.match(r'^\[([a-zA-Z])\]\s*(.*)', cleaned_line_content)
                    if match:
                        letter, rest = match.groups()
                        text_to_add = f"({letter.lower()})\t{rest.lstrip()}"
                        add_formatted_runs(p, text_to_add, placeholder_map)
                elif element['type'] == 'roman_list_item_block':
                    p.style = 'RomanList'
                    match = re.match(r'^\[(i{1,3}|iv|v|vi|vii)\]\s*(.*)', cleaned_line_content)
                    if match:
                        roman, rest = match.groups()
                        text_to_add = f"({roman.lower()})\t{rest.lstrip()}"
                        add_formatted_runs(p, text_to_add, placeholder_map)
                else: # General paragraph block or content that wasn't special cased
                    # Handle [/p] tag for explicit paragraph end with space after
                    has_end_paragraph = '[/p]' in cleaned_line_content
                    if has_end_paragraph:
                        cleaned_line_content = cleaned_line_content.replace('[/p]', '').rstrip()
                        pf.space_after = Pt(12)
                    add_formatted_runs(p, cleaned_line_content, placeholder_map)
                    # Default space after for regular paragraphs if not explicitly set by [/p]
                    if not has_end_paragraph and pf.space_after == Pt(0):
                         pf.space_after = Pt(6) # Smaller default space after for continuous text

        # Final check for last paragraph spacing
        if doc.paragraphs:
            if doc.paragraphs[-1].paragraph_format.space_after == Pt(0):
                doc.paragraphs[-1].paragraph_format.space_after = Pt(6)

        return doc
    except Exception as e:
        logger.error("Error processing precedent text: %s", str(e))
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
            f"{lower_cost_estimate:,.2f} to £{upper_cost_estimate:,.2f} plus VAT "
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

    # generate_fee_table now returns a list of strings
    fee_table_lines = generate_fee_table(hourly_rate, client_type)

    app_inputs = {
        'qu1_dispute_nature': sanitize_input(qu1_dispute_nature),
        'qu2_initial_steps': sanitize_input(qu2_initial_steps),
        'qu3_timescales': sanitize_input(qu3_timescales),
        'qu4_initial_costs_estimate': sanitize_input(costs_text),
        'fee_table': fee_table_lines, # Pass the list of lines
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

    # Validate app_inputs
    required_inputs = ['qu1_dispute_nature', 'qu2_initial_steps', 'qu3_timescales', 'qu4_initial_costs_estimate', 'our_ref', 'client_name_input']
    for key in required_inputs:
        if not app_inputs.get(key):
            st.error(f"Missing or empty input for {key}")
            logger.error("Missing or empty input for %s", key)
            raise ValueError(f"Missing or empty input for {key}")

    placeholder_map = get_placeholder_map(app_inputs, firm_details)

    try:
        doc = process_precedent_text(precedent_content, app_inputs, placeholder_map)
        logger.info("Client Care Letter document processed successfully.")
    except Exception as e:
        st.error(f"Error processing precedent text: {str(e)}")
        logger.error("Error processing precedent text: %s", str(e))
        # This re-raise will stop the app and show detailed error in console for debugging
        raise 

    client_care_doc_io = io.BytesIO()
    doc.save(client_care_doc_io)
    client_care_doc_io.seek(0)
    logger.info("Client Care Letter document generated.")

    advice_doc_io = generate_initial_advice_doc(app_inputs)

    zip_io = io.BytesIO()
    with zipfile.ZipFile(zip_io, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.writestr(f"Client_Care_Letter_{client_name_input.replace(' ', '_')}.docx", client_care_doc_io.getvalue())
        zipf.writestr(f"Initial_Advice_Summary_{client_name_input.replace(' ', '_')}.docx", advice_doc_io.getvalue())
    zip_io.seek(0)

    st.success("Documents Generated Successfully!")
    st.download_button(
        label="Download All Documents as ZIP",
        data=zip_io,
        file_name=f"Client_Documents_{client_name_input.replace(' ', '_')}.zip",
        mime="application/zip"
    )
