import streamlit as st
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
import io
from datetime import datetime
import re
import zipfile
import logging

# --- Setup Logging ---
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Constants ---
INDENT_FOR_IND_TAG_CM = 1.25
SUB_LETTER_HANGING_OFFSET_CM = 0.50
SUB_LETTER_TEXT_INDENT_NO_IND_CM = 0.7  # Indent for lettered lists
SUB_ROMAN_TEXT_INDENT_CM = 1.4  # Indent for Roman numeral lists
NESTED_BULLET_INDENT_CM = INDENT_FOR_IND_TAG_CM + 0.5

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
        "[qu1_dispute_nature]": app_inputs.get('qu1_dispute_nature', ""),
        "[qu2_initial_steps]": app_inputs.get('qu2_initial_steps', ""),
        "[qu3_timescales]": app_inputs.get('qu3_timescales', ""),
        "[qu4_initial_costs_estimate]": app_inputs.get('qu4_initial_costs_estimate', 'XX,XXX'),
        "[FEE_TABLE]": app_inputs.get('fee_table', "Fee table not provided"),
        "{our_ref}": str(app_inputs.get('our_ref', '')),
        "{your_ref}": str(app_inputs.get('your_ref', '')),
        "{letter_date}": str(app_inputs.get('letter_date', '')),
        "{client_name_input}": str(app_inputs.get('client_name_input', '')),
        "{client_address_line1}": str(app_inputs.get('client_address_line1', '')),
        "{client_address_line2_conditional}": str(app_inputs.get('client_address_line2_conditional', '')),
        "{client_postcode}": str(app_inputs.get('client_postcode', '')),
        "{name}": str(app_inputs.get('name', ''))
    }
    firm_placeholders = {f"{{{k}}}": str(v) for k, v in firm_details.items()}
    placeholders.update(firm_placeholders)
    logger.debug("Placeholder map created: %s", placeholders)
    return placeholders

def add_formatted_runs(paragraph, text_line):
    """
    Adds text runs to a paragraph, processing inline formatting tags.
    Supported tags: [bd], [/bd], [b], [/b], [italics], [/italics], [u]/[underline]
    """
    parts = re.split(r'(\[bd\]|\[/bd\]|\[b\]|\[/b\]|\[italics\]|\[/italics\]|\[u\]|\[/u\]|\[underline\]|\[/underline\])', text_line)
    is_bold = is_italic = is_underline = False
    for part in parts:
        if not part:
            continue
        if part == "[bd]": is_bold = True
        elif part == "[/bd]": is_bold = False
        elif part == "[italics]": is_italic = True
        elif part == "[/italics]": is_italic = False
        elif part in ["[u]", "[underline]"]: is_underline = True
        elif part in ["[/u]", "[/underline]"]: is_underline = False
        else:
            run = paragraph.add_run(part)
            run.bold = is_bold
            run.italic = is_italic
            run.underline = is_underline
            run.font.name = 'Arial'
            run.font.size = Pt(11)
    logger.debug("Processed formatted runs for text: %s", text_line)

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
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'HelveticaNeueLT Pro 45 Lt'
    style.font.size = Pt(11)

    p = doc.add_paragraph()
    p.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
    placeholder_map = get_placeholder_map(app_inputs, app_inputs['firm_details'])
    add_formatted_runs(p, f"Initial Advice Summary - Matter Number: {placeholder_map.get('[matter_number]', '')}")
    p.paragraph_format.space_after = Pt(12)

    table = doc.add_table(rows=3, cols=2)
    table.style = 'Table Grid'
    table.autofit = True
    rows = [
        ("Date of Advice", app_inputs.get('initial_advice_date', '').strftime('%d/%m/%Y')),
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

def generate_fee_table(hourly_rate, client_type):
    """Generates a fee table as a string based on hourly rate and client type."""
    roles = [
        ("Partner", hourly_rate * 1.5),
        ("Senior Associate", hourly_rate),
        ("Associate", hourly_rate * 0.8),
        ("Trainee", hourly_rate * 0.5)
    ]
    table_content = "Role | Hourly Rate (excl. VAT)\n-----|------------------------\n"
    for role, rate in roles:
        table_content += f"{role} | £{rate:,.2f}\n"
    if client_type == "Corporate":
        table_content += "\nNote: Corporate clients may be subject to additional administrative fees."
    return table_content

def process_precedent_text(precedent_content, app_inputs, placeholder_map):
    """Process the precedent text and return a Document object."""
    doc = Document()
    doc.styles['Normal'].font.name = 'HelveticaNeueLT Pro 45 Lt'
    doc.styles['Normal'].font.size = Pt(11)

    # Track conditional rendering state
    rendering_state = {
        'in_indiv_block': False,
        'in_corp_block': False,
        'active_track_blocks': []  # Stack to handle nested blocks
    }
    
    lines = precedent_content.splitlines()
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        logger.debug("Processing line %d: %s", i, line)

        # Handle opening/closing tags
        if line.startswith("[indiv]"):
            rendering_state['in_indiv_block'] = True
            logger.debug("Entered individual block")
            i += 1
            continue
        elif line.startswith("[/indiv]"):
            rendering_state['in_indiv_block'] = False
            logger.debug("Exited individual block")
            i += 1
            continue
        elif line.startswith("[corp]"):
            rendering_state['in_corp_block'] = True
            logger.debug("Entered corporate block")
            i += 1
            continue
        elif line.startswith("[/corp]"):
            rendering_state['in_corp_block'] = False
            logger.debug("Exited corporate block")
            i += 1
            continue
        
        # Handle track blocks
        track_tag_match = re.match(r'\[/?(a[1-4]|u[1-4])\]', line)
        if track_tag_match:
            tag = track_tag_match.group(1)
            if line.startswith('[/'):
                # Closing tag
                if tag in rendering_state['active_track_blocks']:
                    rendering_state['active_track_blocks'].remove(tag)
                    logger.debug("Exited track block: %s", tag)
            else:
                # Opening tag
                rendering_state['active_track_blocks'].append(tag)
                logger.debug("Entered track block: %s", tag)
            i += 1
            continue

        # Check if we should render this content
        should_render = True
        
        # Check client type conditions
        if rendering_state['in_indiv_block'] and app_inputs['client_type'] != "Individual":
            should_render = False
            logger.debug("Skipping line - in individual block but client is corporate")
        elif rendering_state['in_corp_block'] and app_inputs['client_type'] != "Corporate":
            should_render = False
            logger.debug("Skipping line - in corporate block but client is individual")
        
        # Check track conditions
        elif rendering_state['active_track_blocks']:
            track_should_render = False
            for track_tag in rendering_state['active_track_blocks']:
                if should_render_track_block(track_tag, app_inputs['claim_assigned'], app_inputs['selected_track']):
                    track_should_render = True
                    break
            should_render = track_should_render
            if not should_render:
                logger.debug("Skipping line - track conditions not met for tags: %s", rendering_state['active_track_blocks'])

        if not should_render:
            i += 1
            continue
            
        # Process empty lines
        if not line or line == "[]":
            if doc.paragraphs:
                doc.paragraphs[-1].paragraph_format.space_after = Pt(12)
            i += 1
            continue

        # Replace placeholders
        for placeholder, value in placeholder_map.items():
            line = line.replace(placeholder, str(value))

        # Create paragraph and apply formatting
        p = doc.add_paragraph()
        pf = p.paragraph_format
        pf.alignment = WD_PARAGRAPH_ALIGNMENT.JUSTIFY
        pf.space_after = Pt(0)
        
        text_content = line
        is_indented = "[ind]" in text_content
        if is_indented:
            text_content = text_content.replace("[ind]", "").lstrip()

        # Handle end-of-paragraph marker
        has_end_paragraph = "[/p]" in text_content
        if has_end_paragraph:
            text_content = text_content.replace("[/p]", "").rstrip()
            pf.space_after = Pt(12)

        # Handle list formatting
        list_match_letter = re.match(r'^\[([a-zA-Z])\]\s(.*)', text_content)
        list_match_roman = re.match(r'^\[(i{1,3}|iv|v|vi|vii)\]\s(.*)', text_content)

        if text_content.startswith("[#]"):
            p.style = 'List Number'
            text_content = text_content.replace("[#]", "", 1).lstrip()
            add_formatted_runs(p, text_content)
        elif list_match_letter:
            letter, rest = list_match_letter.groups()
            text_content = f"({letter.lower()})\t{rest.lstrip()}"
            pf.left_indent = Cm(SUB_LETTER_TEXT_INDENT_NO_IND_CM)
            pf.first_line_indent = Cm(-SUB_LETTER_HANGING_OFFSET_CM)
            pf.tab_stops.add_tab_stop(Cm(SUB_LETTER_TEXT_INDENT_NO_IND_CM))
            add_formatted_runs(p, text_content)
        elif list_match_roman:
            roman, rest = list_match_roman.groups()
            text_content = f"({roman.lower()})\t{rest.lstrip()}"
            pf.left_indent = Cm(SUB_ROMAN_TEXT_INDENT_CM)
            pf.first_line_indent = Cm(-SUB_LETTER_HANGING_OFFSET_CM)
            pf.tab_stops.add_tab_stop(Cm(SUB_ROMAN_TEXT_INDENT_CM))
            add_formatted_runs(p, text_content)
        elif text_content.startswith("[bp]"):
            text_content = text_content.replace("[bp]", "", 1).lstrip()
            p.style = 'List Bullet'
            pf.space_after = Pt(6)
            base_indent = INDENT_FOR_IND_TAG_CM
            if is_indented:
                base_indent = NESTED_BULLET_INDENT_CM
            pf.left_indent = Cm(base_indent)
            add_formatted_runs(p, text_content)
        elif is_indented:
            pf.left_indent = Cm(INDENT_FOR_IND_TAG_CM)
            add_formatted_runs(p, text_content)
        else:
            add_formatted_runs(p, text_content)

        i += 1
    
    return doc

# --- Streamlit App UI ---

st.set_page_config(layout="wide", page_title="Ramsdens Client Care Letter Generator")

# --- Custom CSS for better aesthetics ---
st.markdown("""
<style>
    .stApp {
        background-color: #1E1E1E; /* Dark background */
        color: #FFFFFF;
    }
    .stButton>button {
        background-color: #0078D4; /* A bright, accessible blue */
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
        color: #FFFFFF; /* White text for high contrast */
    }
    .stTextInput, .stTextArea, .stDateInput, .stSelectbox, .stNumberInput {
        border-radius: 5px;
        border: 1px solid #888;
    }
    .stForm {
        background-color: #2D2D2D; /* Slightly lighter dark for the form */
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
        color: #FFFFFF !important; /* Ensure radio button labels are white */
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
        our_ref = st.text_input("Our Reference", "PP/LEGAL/RAM001/001")
        your_ref = st.text_input("Your Reference (if any)", "")
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

    # Generate fee table based on hourly rate and client type
    fee_table = generate_fee_table(hourly_rate, client_type)

    app_inputs = {
        'qu1_dispute_nature': qu1_dispute_nature, 
        'qu2_initial_steps': qu2_initial_steps,
        'qu3_timescales': qu3_timescales, 
        'qu4_initial_costs_estimate': costs_text,
        'fee_table': fee_table,
        'client_type': client_type,
        'claim_assigned': claim_assigned_input == "Yes", 
        'selected_track': selected_track,
        'our_ref': our_ref, 
        'your_ref': your_ref, 
        'letter_date': letter_date.strftime('%d/%m/%Y'),
        'client_name_input': client_name_input, 
        'client_address_line1': client_address_line1,
        'client_address_line2_conditional': client_address_line2 if client_address_line2 else "",
        'client_postcode': client_postcode, 
        'name': firm_details["person_responsible_name"],
        'initial_advice_content': initial_advice_content,
        'initial_advice_method': initial_advice_method, 
        'initial_advice_date': initial_advice_date,
        'firm_details': firm_details
    }

    placeholder_map = get_placeholder_map(app_inputs, firm_details)

    # --- Generate Client Care Letter ---
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

    # --- Generate Initial Advice Document ---
    advice_doc_io = generate_initial_advice_doc(app_inputs)

    # --- Create ZIP file for Download ---
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
