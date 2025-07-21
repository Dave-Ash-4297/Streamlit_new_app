import streamlit as st
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
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
        # Ensure text_line is a string
        if not isinstance(text_line, str):
            text_line = str(text_line)
            logger.warning("Converted non-string text_line to string: %s", text_line)

        # Log the placeholder_map for debugging
        logger.debug("Placeholder map in add_formatted_runs: %s", placeholder_map)

        # Replace placeholders with their values (support both {placeholder} and [placeholder])
        processed_text = text_line
        for placeholder, value in placeholder_map.items():
            # Handle {placeholder} syntax
            placeholder_pattern = f"{{{placeholder}}}"
            if placeholder_pattern in processed_text:
                logger.debug("Replacing placeholder '%s' with value '%s'", placeholder_pattern, value)
                processed_text = processed_text.replace(placeholder_pattern, str(value))
            # Handle [placeholder] syntax
            placeholder_pattern_alt = f"[{placeholder}]"
            if placeholder_pattern_alt in processed_text:
                logger.debug("Replacing placeholder '%s' with value '%s'", placeholder_pattern_alt, value)
                processed_text = processed_text.replace(placeholder_pattern_alt, str(value))
        
        # Check for unprocessed placeholders
        if (('{' in processed_text and '}' in processed_text) or 
            ('[' in processed_text and ']' in processed_text)):
            logger.warning("Unprocessed placeholders in text: %s", processed_text)
        
        # Handle formatting tags
        parts = re.split(r'(\[bd\]|\[/bd\]|\[italics\]|\[/italics\]|\[u\]|\[/u\]|\[underline\]|\[/underline\])', processed_text)
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
            else:
                run = paragraph.add_run(part)
                run.bold = is_bold
                run.italic = is_italic
                run.underline = is_underline
                run.font.name = 'Arial'
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
        # Log app_inputs for debugging
        logger.debug("App inputs in generate_initial_advice_doc: %s", app_inputs)

        # Validate required inputs
        if 'our_ref' not in app_inputs or not app_inputs['our_ref']:
            logger.error("Missing or empty our_ref in app_inputs")
            raise ValueError("Missing or empty our_ref in app_inputs")

        doc = Document()
        style = doc.styles['Normal']
        style.font.name = 'HelveticaNeueLT Pro 45 Lt'
        style.font.size = Pt(11)

        p = doc.add_paragraph()
        p.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
        placeholder_map = get_placeholder_map(app_inputs, app_inputs['firm_details'])

        # Verify matter_number exists in placeholder_map
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
    table_content = ""
    for role, rate in roles:
        table_content += f"[#]{role}: £{rate:,.2f} per hour (excl. VAT)[/p]\n"
    if client_type == "Corporate":
        table_content += "[#]Note: Corporate clients may be subject to additional administrative fees.[/p]"
    return table_content

def preprocess_precedent(precedent_content, app_inputs):
    """Preprocesses the precedent text into logical document elements."""
    logical_elements = []
    lines = precedent_content.splitlines()
    i = 0
    current_block = None
    block_lines = []
    block_version = None
    block_number = None

    while i < len(lines):
        line = lines[i].strip()
        logger.debug("Preprocessing line %d: %s", i, line)

        if line in ['[indiv]', '[corp]']:
            if current_block and block_lines:
                logical_elements.append({
                    'type': 'paragraph_block',
                    'content_lines': block_lines,
                    'version': block_version,
                    'paragraph_display_number_text': block_number
                })
            current_block = line[1:-1]
            block_lines = []
            block_version = None
            block_number = None
            i += 1
            continue
        elif line in ['[/indiv]', '[/corp]']:
            if current_block and block_lines:
                logical_elements.append({
                    'type': 'paragraph_block',
                    'content_lines': block_lines,
                    'version': block_version,
                    'paragraph_display_number_text': block_number
                })
            current_block = None
            block_lines = []
            block_version = None
            block_number = None
            i += 1
            continue
        elif re.match(r'\[(a[1-4]|u[1-4])\]', line):
            if block_lines:
                logical_elements.append({
                    'type': 'paragraph_block',
                    'content_lines': block_lines,
                    'version': block_version,
                    'paragraph_display_number_text': block_number
                })
                block_lines = []
            block_version = line[1:-1]
            block_number = None
            i += 1
            continue
        elif re.match(r'\[/(a[1-4]|u[1-4])\]', line):
            if block_lines:
                logical_elements.append({
                    'type': 'paragraph_block',
                    'content_lines': block_lines,
                    'version': block_version,
                    'paragraph_display_number_text': block_number
                })
            block_version = None
            block_lines = []
            block_number = None
            i += 1
            continue

        if line.startswith('[#]'):
            if block_lines:
                logical_elements.append({
                    'type': 'paragraph_block',
                    'content_lines': block_lines,
                    'version': block_version,
                    'paragraph_display_number_text': block_number
                })
                block_lines = []
            block_number = '[#]'
            block_lines.append(line)
        elif line == '[]' or not line:
            if block_lines:
                logical_elements.append({
                    'type': 'paragraph_block',
                    'content_lines': block_lines,
                    'version': block_version,
                    'paragraph_display_number_text': block_number
                })
                block_lines = []
                block_number = None
            logical_elements.append({'type': 'raw_line', 'content': line})
        elif line == '[FEE_TABLE_PLACEHOLDER]':
            block_lines.append(f"[{app_inputs['fee_table']}]")
        else:
            block_lines.append(line)

        i += 1

    if block_lines:
        logical_elements.append({
            'type': 'paragraph_block',
            'content_lines': block_lines,
            'version': block_version,
            'paragraph_display_number_text': block_number
        })

    logger.debug("Logical elements created: %s", logical_elements)
    return logical_elements

def process_precedent_text(precedent_content, app_inputs, placeholder_map):
    """Processes the precedent text and returns a Document object."""
    try:
        doc = Document()
        doc.styles['Normal'].font.name = 'HelveticaNeueLT Pro 45 Lt'
        doc.styles['Normal'].font.size = Pt(11)

        logical_elements = preprocess_precedent(precedent_content, app_inputs)
        in_indiv_block = in_corp_block = False
        active_track_block = None

        for element in logical_elements:
            if element['type'] == 'raw_line':
                if element['content'] == '[]' or not element['content']:
                    if doc.paragraphs:
                        doc.paragraphs[-1].paragraph_format.space_after = Pt(12)
                    continue
                p = doc.add_paragraph()
                add_formatted_runs(p, element['content'], placeholder_map)
                continue

            block_lines = element['content_lines']
            block_versioning = element['version']
            is_numbered_block = element['paragraph_display_number_text'] == '[#]'

            if block_versioning in ['indiv', 'corp']:
                if block_versioning == 'indiv':
                    in_indiv_block = app_inputs['client_type'] == 'Individual'
                elif block_versioning == 'corp':
                    in_corp_block = app_inputs['client_type'] == 'Corporate'
                continue

            if block_versioning in ['a1', 'a2', 'a3', 'a4', 'u1', 'u2', 'u3', 'u4']:
                active_track_block = block_versioning if should_render_track_block(block_versioning, app_inputs['claim_assigned'], app_inputs['selected_track']) else None
                continue

            if (in_indiv_block and app_inputs['client_type'] != 'Individual') or \
               (in_corp_block and app_inputs['client_type'] != 'Corporate'):
                continue

            if active_track_block and not should_render_track_block(active_track_block, app_inputs['claim_assigned'], app_inputs['selected_track']):
                continue

            first_content_line = True
            for line in block_lines:
                if not line.strip():
                    if doc.paragraphs:
                        doc.paragraphs[-1].paragraph_format.space_after = Pt(12)
                    continue

                text_content = line
                p = doc.add_paragraph()
                pf = p.paragraph_format
                pf.alignment = WD_PARAGRAPH_ALIGNMENT.JUSTIFY
                pf.tab_stops.clear_all()

                is_indented = '[ind]' in text_content
                if is_indented:
                    text_content = text_content.replace('[ind]', '').lstrip()

                has_end_paragraph = '[/p]' in text_content
                if has_end_paragraph:
                    text_content = text_content.replace('[/p]', '').rstrip()
                    pf.space_after = Pt(12)

                if is_numbered_block and first_content_line:
                    p.style = 'List Number'
                    pf.left_indent = Cm(0.7)
                    pf.first_line_indent = Cm(-0.7)
                    pf.tab_stops.add_tab_stop(Cm(0.7))
                    text_content = text_content.replace('[#]', '', 1).lstrip()
                    first_content_line = False
                elif text_content.startswith('[u]'):
                    text_content = text_content.replace('[u]', '', 1).lstrip()
                    p.style = 'Heading 2'
                    pf.space_before = Pt(12)
                    pf.space_after = Pt(6)
                elif text_content.startswith('[bp]'):
                    text_content = text_content.replace('[bp]', '', 1).lstrip()
                    p.style = 'List Bullet'
                    base_indent = INDENT_FOR_IND_TAG_CM if is_indented else NESTED_BULLET_INDENT_CM
                    pf.left_indent = Cm(base_indent)
                    pf.space_after = Pt(6)
                else:
                    list_match_letter = re.match(r'^\[([a-zA-Z])\]\s*(.*)', text_content)
                    list_match_roman = re.match(r'^\[(i{1,3}|iv|v|vi|vii)\]\s*(.*)', text_content)
                    if list_match_letter:
                        letter, rest = list_match_letter.groups()
                        text_content = f"({letter.lower()})\t{rest.lstrip()}"
                        indent = SUB_LETTER_TEXT_INDENT_NO_IND_CM + INDENT_FOR_IND_TAG_CM if is_indented else SUB_LETTER_TEXT_INDENT_NO_IND_CM
                        text_indent = SUB_LETTER_TEXT_START_CM + INDENT_FOR_IND_TAG_CM if is_indented else SUB_LETTER_TEXT_START_CM
                        pf.left_indent = Cm(text_indent)
                        pf.first_line_indent = Cm(indent - text_indent)
                        pf.tab_stops.add_tab_stop(Cm(text_indent))
                    elif list_match_roman:
                        roman, rest = list_match_roman.groups()
                        text_content = f"({roman.lower()})\t{rest.lstrip()}"
                        indent = SUB_ROMAN_TEXT_INDENT_CM + INDENT_FOR_IND_TAG_CM if is_indented else SUB_ROMAN_TEXT_INDENT_CM
                        text_indent = SUB_ROMAN_TEXT_START_CM + INDENT_FOR_IND_TAG_CM if is_indented else SUB_ROMAN_TEXT_START_CM
                        pf.left_indent = Cm(text_indent)
                        pf.first_line_indent = Cm(indent - text_indent)
                        pf.tab_stops.add_tab_stop(Cm(text_indent))
                    elif is_indented:
                        pf.left_indent = Cm(INDENT_FOR_IND_TAG_CM)

                add_formatted_runs(p, text_content, placeholder_map)

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

    fee_table = generate_fee_table(hourly_rate, client_type)

    app_inputs = {
        'qu1_dispute_nature': sanitize_input(qu1_dispute_nature),
        'qu2_initial_steps': sanitize_input(qu2_initial_steps),
        'qu3_timescales': sanitize_input(qu3_timescales),
        'qu4_initial_costs_estimate': sanitize_input(costs_text),
        'fee_table': fee_table,
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
