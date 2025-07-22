import streamlit as st
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import io
from datetime import datetime
import re
import zipfile
import logging
import html

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Constants ---
INDENT_FOR_IND_TAG_CM = 1.25
MAIN_LIST_TEXT_START_CM = 0.7
MARKER_OFFSET_CM = 0.7
SUB_LIST_TEXT_START_CM = 1.4
SUB_ROMAN_TEXT_START_CM = 2.1

# --- Utility Functions ---
def sanitize_input(text):
    if not isinstance(text, str):
        text = str(text)
    # Only escape HTML, don't replace newlines as they are handled in paragraph logic
    return html.escape(text)

# --- Cached Data Loading ---
@st.cache_data
def load_firm_details():
    return {
        "name": "Ramsdens Solicitors LLP", "short_name": "Ramsdens",
        "person_responsible_name": "Paul Pinder", "person_responsible_title": "Senior Associate",
        "supervisor_name": "Nick Armitage", "supervisor_title": "Partner",
        "person_responsible_phone": "01484 821558", "person_responsible_mobile": "07923 250815",
        "person_responsible_email": "paul.pinder@ramsdens.co.uk", "assistant_name": "Reece Collier",
        "supervisor_contact_for_complaints": "Nick Armitage on 01484 507121", "bank_name": "Barclays Bank PLC",
        "bank_address": "17 Market Place, Huddersfield", "account_name": "Ramsdens Solicitors LLP Client Account",
        "sort_code": "20-43-12", "account_number": "03909026",
        "marketing_email": "dataprotection@ramsdens.co.uk",
        "marketing_address": "Ramsdens Solicitors LLP, Oakley House, 1 Hungerford Road, Edgerton, Huddersfield, HD3 3AL"
    }

@st.cache_data
def load_precedent_text():
    try:
        with open("precedent.txt", "r", encoding="utf-8") as f:
            # We don't strip() the content to preserve initial newlines if any
            content = f.read()
            logger.info("Successfully loaded precedent.txt")
            return content
    except FileNotFoundError:
        st.error("precedent.txt not found. Please ensure the file exists in the same directory.")
        return ""
    except Exception as e:
        st.error(f"Error loading precedent.txt: {e}")
        return ""

# --- Placeholder & Run Formatting ---
def get_placeholder_map(app_inputs, firm_details):
    placeholders = {
        'qu1_dispute_nature': app_inputs.get('qu1_dispute_nature', ''),
        'qu2_initial_steps': app_inputs.get('qu2_initial_steps', ''),
        'qu3_timescales': app_inputs.get('qu3_timescales', ''),
        'qu4_initial_costs_estimate': app_inputs.get('qu4_initial_costs_estimate', 'XX,XXX'),
        'fee_table': app_inputs.get('fee_table', ["Fee table not provided"]),
        'our_ref': str(app_inputs.get('our_ref', '')),
        'your_ref': str(app_inputs.get('your_ref', '')),
        'letter_date': str(app_inputs.get('letter_date', '')),
        'client_name_input': str(app_inputs.get('client_name_input', '')),
        # FIX: Reverted to using separate address line placeholders to match precedent.txt
        'client_address_line1': str(app_inputs.get('client_address_line1', '')),
        'client_address_line2_conditional': str(app_inputs.get('client_address_line2_conditional', '')),
        'client_postcode': str(app_inputs.get('client_postcode', '')),
        'matter_number': str(app_inputs.get('our_ref', '')),
        'name': str(app_inputs.get('name', '')),
    }
    firm_placeholders = {k: str(v) for k, v in firm_details.items()}
    placeholders.update(firm_placeholders)
    return placeholders

def add_formatted_runs(paragraph, text_line, placeholder_map):
    try:
        processed_text = text_line
        for placeholder, value in placeholder_map.items():
            processed_text = processed_text.replace(f"{{{placeholder}}}", str(value))

        # FIX: Updated regex to match markers from precedent.txt (<ins>, <bd>)
        parts = re.split(r'(<bd>|</bd>|<ins>|</ins>)', processed_text)
        is_bold = is_underline = False

        for part in parts:
            if not part: continue
            if part == "<bd>": is_bold = True
            elif part == "</bd>": is_bold = False
            elif part == "<ins>": is_underline = True
            elif part == "</ins>": is_underline = False
            else:
                # Handle multi-line text (like the address block)
                for i, line_part in enumerate(part.split('\n')):
                    if i > 0:
                        paragraph.add_run().add_break()
                    run = paragraph.add_run(line_part)
                    run.bold = is_bold
                    run.underline = is_underline
                    run.font.name = 'Arial'
                    run.font.size = Pt(11)
    except Exception as e:
        logger.error(f"Error in add_formatted_runs for text '{text_line}': {e}", exc_info=True)
        raise

# --- Conditional Block Logic ---
def should_render_track_block(tag, claim_assigned, selected_track):
    tag_map = {
        'a1': (True, "Small Claims Track"), 'a2': (True, "Fast Track"), 'a3': (True, "Intermediate Track"), 'a4': (True, "Multi Track"),
        'u1': (False, "Small Claims Track"), 'u2': (False, "Fast Track"), 'u3': (False, "Intermediate Track"), 'u4': (False, "Multi Track"),
    }
    expected = tag_map.get(tag)
    if not expected: return False
    return claim_assigned == expected[0] and selected_track == expected[1]

# --- Document Generation Functions ---
def generate_initial_advice_doc(app_inputs, placeholder_map):
    try:
        doc = Document()
        doc.styles['Normal'].font.name = 'Arial'
        doc.styles['Normal'].font.size = Pt(11)
        p = doc.add_paragraph()
        add_formatted_runs(p, "Initial Advice Summary - Matter Number: {matter_number}", placeholder_map)
        p.paragraph_format.space_after = Pt(12)
        table = doc.add_table(rows=3, cols=2)
        table.style = 'Table Grid'
        rows_data = [
            ("Date of Advice", app_inputs['initial_advice_date'].strftime('%d/%m/%Y') if app_inputs.get('initial_advice_date') else ''),
            ("Method of Advice", app_inputs.get('initial_advice_method', '')),
            ("Advice Given", app_inputs.get('initial_advice_content', ''))
        ]
        for i, (label, value) in enumerate(rows_data):
            table.rows[i].cells[0].text = label
            table.rows[i].cells[1].text = value
        doc_io = io.BytesIO()
        doc.save(doc_io)
        doc_io.seek(0)
        return doc_io
    except Exception as e:
        logger.error(f"Failed to generate Initial Advice Summary: {e}", exc_info=True)
        raise

def generate_fee_table(hourly_rate):
    roles = [("Partner", hourly_rate * 1.5), ("Senior Associate", hourly_rate), ("Associate", hourly_rate * 0.8), ("Trainee", hourly_rate * 0.5)]
    # The template uses hardcoded numbers, so we generate the content to be inserted into a numbered list
    return [f"{role}: £{rate:,.2f} per hour (excl. VAT)" for role, rate in roles]

def preprocess_precedent(precedent_content, app_inputs):
    """
    FIX: Major rewrite to parse markers directly from the user's `precedent.txt`.
    Detects <ins> headings, numbered lists (1.), lettered lists (<a>), and roman lists (<i>).
    """
    logical_elements = []
    lines = precedent_content.splitlines()
    i = 0
    current_block_tag = None

    while i < len(lines):
        line = lines[i]
        stripped_line = line.strip()

        # Regex for block tags
        match_start_tag = re.match(r'\[(indiv|corp|a[1-4]|u[1-4])\]', stripped_line)
        match_end_tag = re.match(r'\[/(indiv|corp|a[1-4]|u[1-4])\]', stripped_line)

        # Regex for content types from precedent.txt
        match_heading = re.match(r'^<ins>(.*)</ins>$', stripped_line)
        match_numbered_list = re.match(r'^(\d+)\.\s*(.*)', stripped_line)
        match_letter_list = re.match(r'^<a>\s*(.*)', stripped_line)
        match_roman_list = re.match(r'^<i>\s*(.*)', stripped_line)

        element = None
        if match_start_tag:
            current_block_tag = match_start_tag.group(1)
        elif match_end_tag:
            current_block_tag = None
        elif stripped_line == '[FEE_TABLE_PLACEHOLDER]':
            element = {'type': 'fee_table', 'content_lines': app_inputs['fee_table']}
        elif match_heading:
            element = {'type': 'heading', 'content_lines': [match_heading.group(1)]}
        elif match_numbered_list:
            element = {'type': 'numbered_list_item', 'content_lines': [match_numbered_list.group(2)]}
        elif match_letter_list:
            element = {'type': 'letter_list_item', 'content_lines': [match_letter_list.group(1)]}
        elif match_roman_list:
            element = {'type': 'roman_list_item', 'content_lines': [match_roman_list.group(1)]}
        # A blank line in the file is a paragraph break with default spacing
        elif not stripped_line:
            element = {'type': 'blank_line', 'content_lines': []}
        # Anything else is a general paragraph
        else:
            element = {'type': 'general_paragraph', 'content_lines': [line]} # Keep original line for placeholder replacement

        if element:
            element['block_tag'] = current_block_tag
            logical_elements.append(element)

        i += 1
    return logical_elements

def process_precedent_text(precedent_content, app_inputs, placeholder_map):
    try:
        doc = Document()
        doc.styles['Normal'].font.name = 'Arial'
        doc.styles['Normal'].font.size = Pt(11)

        # Create one multi-level list definition to handle all list types
        numbering = doc.part.numbering_part
        abstract_num = numbering.new_abstract_num()
        # Level 0: Numbered (1.)
        lvl0 = abstract_num.add_level(level=0, num_format='decimal', start=1)
        lvl0.text_format = '%1.'
        lvl0.paragraph_format.left_indent = Cm(MAIN_LIST_TEXT_START_CM)
        lvl0.paragraph_format.first_line_indent = -Cm(MARKER_OFFSET_CM)
        # Level 1: Lettered (a) - Note: template uses <a>, but Word will render as (a) or a.
        lvl1 = abstract_num.add_level(level=1, num_format='lowerLetter', start=1)
        lvl1.text_format = '%2.'
        lvl1.paragraph_format.left_indent = Cm(SUB_LIST_TEXT_START_CM)
        lvl1.paragraph_format.first_line_indent = -Cm(MARKER_OFFSET_CM)
        # Level 2: Roman (i)
        lvl2 = abstract_num.add_level(level=2, num_format='lowerRoman', start=1)
        lvl2.text_format = '%3.'
        lvl2.paragraph_format.left_indent = Cm(SUB_ROMAN_TEXT_START_CM)
        lvl2.paragraph_format.first_line_indent = -Cm(MARKER_OFFSET_CM)
        # Link to a concrete instance
        num_id = numbering.add_num(abstract_num)

        logical_elements = preprocess_precedent(precedent_content, app_inputs)

        for element in logical_elements:
            render_this_element = True
            tag = element.get('block_tag')
            if tag:
                if tag in ['indiv', 'corp']:
                    render_this_element = (tag == 'indiv' and app_inputs['client_type'] == 'Individual') or \
                                         (tag == 'corp' and app_inputs['client_type'] == 'Corporate')
                else:
                    render_this_element = should_render_track_block(tag, app_inputs['claim_assigned'], app_inputs['selected_track'])

            if not render_this_element: continue

            content = element['content_lines'][0] if element['content_lines'] else ""

            def add_list_item(level, text, p_num_id):
                p = doc.add_paragraph(text, style='List Paragraph')
                p.paragraph_format.left_indent = None
                p.paragraph_format.first_line_indent = None
                p.numbering_style = f"num_lvl_{p_num_id.numId}_{level}"
                # The numbering style applies indents. Re-apply formatting after.
                p.paragraph_format.alignment = WD_PARAGRAPH_ALIGNMENT.JUSTIFY
                p.paragraph_format.space_after = Pt(6)

            if element['type'] == 'blank_line':
                doc.add_paragraph()
            elif element['type'] == 'fee_table':
                for fee_line in element['content_lines']:
                    add_list_item(0, fee_line, num_id)
            elif element['type'] == 'heading':
                p = doc.add_paragraph()
                run = p.add_run(content)
                run.underline = True
                run.bold = True
                run.font.name = 'Arial'
                run.font.size = Pt(11)
                p.paragraph_format.space_before = Pt(12)
                p.paragraph_format.space_after = Pt(6)
            elif element['type'] == 'numbered_list_item':
                add_list_item(0, content, num_id)
            elif element['type'] == 'letter_list_item':
                add_list_item(1, content, num_id)
            elif element['type'] == 'roman_list_item':
                add_list_item(2, content, num_id)
            elif element['type'] == 'general_paragraph':
                p = doc.add_paragraph()
                pf = p.paragraph_format
                pf.alignment = WD_PARAGRAPH_ALIGNMENT.JUSTIFY
                # The [ind] tag is for line-level indentation, not a block
                cleaned_content = content.replace('[ind]', '').strip()
                if '[ind]' in content:
                    pf.left_indent = Cm(INDENT_FOR_IND_TAG_CM)
                add_formatted_runs(p, cleaned_content, placeholder_map)
                pf.space_after = Pt(12)

        return doc
    except Exception as e:
        logger.error(f"Error processing precedent text: {e}", exc_info=True)
        raise

# --- Streamlit App UI (largely unchanged, a few input labels updated for clarity) ---
st.set_page_config(layout="wide", page_title="Ramsdens Client Care Letter Generator")
st.title("Ramsdens Client Care Letter Generator")

firm_details = load_firm_details()
precedent_content = load_precedent_text()

if not precedent_content: st.stop()

with st.form("input_form"):
    # ... Form definition ...
    st.header("1. Letter & Client Details")
    col1, col2 = st.columns(2)
    with col1:
        our_ref = st.text_input("Our Reference", "PDP/10011/001")
        your_ref = st.text_input("Your Reference (if any)", "REF")
        letter_date = st.date_input("Letter Date", datetime.today())
    with col2:
        client_name_input = st.text_input("Client Full Name / Company Name", "Mr. John Smith")
        client_address_line1 = st.text_input("Client Address Line 1", "123 Example Street")
        client_address_line2 = st.text_input("Client Address Line 2 (optional)", "SomeTown")
        client_postcode = st.text_input("Client Postcode", "EX4 MPL")
        client_type = st.radio("Client Type", ("Individual", "Corporate"), horizontal=True)

    st.header("2. Initial Advice & Case Details")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Initial Advice Summary")
        initial_advice_content = st.text_area("Advice Given", "Advised on the merits of the claim and potential next steps.", height=100)
        initial_advice_method = st.selectbox("Method of Advice", ["Phone Call", "In Person", "Teams Call"])
        initial_advice_date = st.date_input("Date of Advice", datetime.today())
    with col2:
        st.subheader("Case Track (for Fixed Costs section)")
        claim_assigned_input = st.radio("Is the claim already assigned to a court track?", ("Yes", "No"), horizontal=True)
        track_options = ["Small Claims Track", "Fast Track", "Intermediate Track", "Multi Track"]
        selected_track = st.selectbox("Which court track applies or is anticipated?", track_options)

    st.header("3. Dynamic Content for Letter")
    qu1_dispute_nature = st.text_area('Dispute Nature (for "Your Instructions" section)', "a contractual matter where you wish to bring a claim against your landlord", height=75)
    qu2_initial_steps = st.text_area('Initial Work (for "Your Instructions" section)', "review the documentation you have provided and advise you on the merits of your case and set out the next steps", height=100)
    qu3_timescales = st.text_area("Estimated Timescales", "We estimate that to complete the initial advice for you we will take approximately two to four weeks to complete.", height=100)
    
    st.subheader("Estimated Initial Costs (for 'Costs Advice' section)")
    hourly_rate = st.number_input("Your Hourly Rate (£)", value=295)
    cost_type_is_range = st.toggle("Use a cost range", value=True)
    if cost_type_is_range:
        lower_cost = st.number_input("Lower estimate (£)", value=float(hourly_rate * 2))
        upper_cost = st.number_input("Upper estimate (£)", value=float(hourly_rate * 3))
    else:
        fixed_cost = st.number_input("Fixed cost estimate (£)", value=float(hourly_rate * 2.5))

    submitted = st.form_submit_button("Generate Documents")

if submitted:
    vat_rate = 0.20
    if cost_type_is_range:
        costs_text = f"£{lower_cost:,.2f} to £{upper_cost:,.2f} plus VAT (currently at 20%)"
    else:
        costs_text = f"a fixed fee of £{fixed_cost:,.2f} plus VAT (currently at 20%)"

    app_inputs = {
        'qu1_dispute_nature': sanitize_input(qu1_dispute_nature),
        'qu2_initial_steps': sanitize_input(qu2_initial_steps),
        'qu3_timescales': sanitize_input(qu3_timescales),
        'qu4_initial_costs_estimate': costs_text,
        'fee_table': generate_fee_table(hourly_rate),
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
        'initial_advice_content': initial_advice_content,
        'initial_advice_method': initial_advice_method,
        'initial_advice_date': initial_advice_date,
        'firm_details': firm_details
    }

    placeholder_map = get_placeholder_map(app_inputs, firm_details)

    try:
        doc = process_precedent_text(precedent_content, app_inputs, placeholder_map)
        client_care_doc_io = io.BytesIO()
        doc.save(client_care_doc_io)
        client_care_doc_io.seek(0)
        advice_doc_io = generate_initial_advice_doc(app_inputs, placeholder_map)
        
        client_name_safe = re.sub(r'[^\w\s-]', '', client_name_input).strip().replace(' ', '_')
        zip_io = io.BytesIO()
        with zipfile.ZipFile(zip_io, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.writestr(f"Client_Care_Letter_{client_name_safe}.docx", client_care_doc_io.getvalue())
            if advice_doc_io:
                zipf.writestr(f"Initial_Advice_Summary_{client_name_safe}.docx", advice_doc_io.getvalue())
        zip_io.seek(0)

        st.success("Documents Generated Successfully!")
        st.download_button(label="Download All Documents as ZIP", data=zip_io, file_name=f"Client_Docs_{client_name_safe}.zip", mime="application/zip")

    except Exception as e:
        st.error(f"An error occurred while building the documents: {e}")
        logger.exception("Error during document generation:")
