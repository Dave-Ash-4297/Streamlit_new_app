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
    """Escapes HTML characters in user input to prevent issues."""
    if not isinstance(text, str):
        text = str(text)
    return html.escape(text)

def add_formatted_runs(paragraph, text_line, placeholder_map):
    """
    Adds text to a paragraph, handling placeholders, bold, and underline tags.
    This is now a top-level function accessible by all document generators.
    """
    processed_text = text_line
    for placeholder, value in placeholder_map.items():
        processed_text = processed_text.replace(f"{{{placeholder}}}", str(value))

    parts = re.split(r'(<bd>|</bd>|<ins>|</ins>)', processed_text)
    is_bold = is_underline = False
    for part in parts:
        if not part: continue
        if part == "<bd>": is_bold = True
        elif part == "</bd>": is_bold = False
        elif part == "<ins>": is_underline = True
        elif part == "</ins>": is_underline = False
        else:
            run = paragraph.add_run(part)
            run.bold, run.underline = is_bold, is_underline
            run.font.name = 'Arial'
            run.font.size = Pt(11)

# --- Data Loading ---
@st.cache_data
def load_firm_details():
    """Loads static firm details."""
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
    """Loads the precedent text file."""
    try:
        with open("precedent.txt", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        st.error("precedent.txt not found.")
        return ""

# --- Document Generation Logic ---
def generate_client_care_document(precedent_content, app_inputs):
    """
    Parses the precedent text and generates a .docx file in memory.
    """
    
    # 1. SETUP THE DOCUMENT AND NUMBERING
    doc = Document()
    doc.styles['Normal'].font.name = 'Arial'
    doc.styles['Normal'].font.size = Pt(11)

    numbering_elm = doc.part.numbering_part.element
    abstract_num_id, num_instance_id = 10, 1

    def setup_numbering_style(numbering_element):
        """Creates the multi-level list style for the document."""
        abstract_num = OxmlElement('w:abstractNum')
        abstract_num.set(qn('w:abstractNumId'), str(abstract_num_id))

        def create_level(ilvl, numFmt, lvlText, left_cm):
            lvl = OxmlElement('w:lvl')
            lvl.set(qn('w:ilvl'), str(ilvl))
            lvl.append(OxmlElement('w:start', {qn('w:val'): '1'}))
            lvl.append(OxmlElement('w:numFmt', {qn('w:val'): numFmt}))
            lvl.append(OxmlElement('w:lvlText', {qn('w:val'): lvlText}))
            pPr = OxmlElement('w:pPr')
            ind = OxmlElement('w:ind')
            ind.set(qn('w:left'), str(Cm(left_cm).twips))
            ind.set(qn('w:hanging'), str(Cm(MARKER_OFFSET_CM).twips))
            pPr.append(ind)
            lvl.append(pPr)
            return lvl

        abstract_num.append(create_level(0, 'decimal', '%1.', MAIN_LIST_TEXT_START_CM))
        abstract_num.append(create_level(1, 'lowerLetter', '%2.', SUB_LIST_TEXT_START_CM))
        abstract_num.append(create_level(2, 'lowerRoman', '%3.', SUB_ROMAN_TEXT_START_CM))
        numbering_element.append(abstract_num)

        num = OxmlElement('w:num')
        num.set(qn('w:numId'), str(num_instance_id))
        num.append(OxmlElement('w:abstractNumId', {qn('w:val'): str(abstract_num_id)}))
        numbering_element.append(num)

    setup_numbering_style(numbering_elm)
    placeholder_map = app_inputs['placeholder_map']

    # 2. HELPER FUNCTION FOR ADDING LIST ITEMS
    def add_list_item(text, level):
        """Adds a paragraph formatted as a list item at the specified level."""
        p = doc.add_paragraph()
        pPr = p._p.get_or_add_pPr()
        numPr = pPr.get_or_add_numPr()
        numPr.get_or_add_ilvl().val = level
        numPr.get_or_add_numId().val = num_instance_id
        add_formatted_runs(p, text, placeholder_map)
        p.paragraph_format.alignment = WD_PARAGRAPH_ALIGNMENT.JUSTIFY
        p.paragraph_format.space_after = Pt(6)

    # 3. PARSE THE PRECEDENT AND RENDER THE DOCUMENT
    current_block_tag = None
    lines = precedent_content.splitlines()

    for line in lines:
        stripped_line = line.strip()

        match_start_tag = re.match(r'\[(indiv|corp|a[1-4]|u[1-4])\]', stripped_line)
        match_end_tag = re.match(r'\[/(indiv|corp|a[1-4]|u[1-4])\]', stripped_line)

        if match_start_tag:
            current_block_tag = match_start_tag.group(1)
            continue
        if match_end_tag:
            current_block_tag = None
            continue
        
        should_render = True
        if current_block_tag:
            tag = current_block_tag
            claim_assigned = app_inputs['claim_assigned']
            selected_track = app_inputs['selected_track']
            
            tag_map = {
                'a1': (True, "Small Claims Track"), 'a2': (True, "Fast Track"), 'a3': (True, "Intermediate Track"), 'a4': (True, "Multi Track"),
                'u1': (False, "Small Claims Track"), 'u2': (False, "Fast Track"), 'u3': (False, "Intermediate Track"), 'u4': (False, "Multi Track")
            }
            
            if tag in ['indiv', 'corp']:
                should_render = (tag == 'indiv' and app_inputs['client_type'] == 'Individual') or \
                                (tag == 'corp' and app_inputs['client_type'] == 'Corporate')
            elif tag in tag_map:
                expected_assignment, expected_track = tag_map[tag]
                should_render = (claim_assigned == expected_assignment and selected_track == expected_track)

        if not should_render:
            continue

        if not stripped_line:
            continue
        
        match_heading = re.match(r'^<ins>(.*)</ins>$', stripped_line)
        match_numbered_list = re.match(r'^(\d+)\.\s*(.*)', stripped_line)
        match_letter_list = re.match(r'^<a>\s*(.*)', stripped_line)
        match_roman_list = re.match(r'^<i>\s*(.*)', stripped_line)

        if stripped_line == '[FEE_TABLE_PLACEHOLDER]':
            for fee_line in app_inputs['fee_table']:
                add_list_item(fee_line, level=0)
        elif match_heading:
            p = doc.add_paragraph()
            add_formatted_runs(p, f"<ins>{match_heading.group(1)}</ins>", placeholder_map)
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(6)
        elif match_numbered_list:
            add_list_item(match_numbered_list.group(2), level=0)
        elif match_letter_list:
            add_list_item(match_letter_list.group(1), level=1)
        elif match_roman_list:
            add_list_item(match_roman_list.group(1), level=2)
        else:
            p = doc.add_paragraph()
            cleaned_content = line.replace('[ind]', '').strip()
            if '[ind]' in line:
                p.paragraph_format.left_indent = Cm(INDENT_FOR_IND_TAG_CM)
            add_formatted_runs(p, cleaned_content, placeholder_map)
            p.paragraph_format.alignment = WD_PARAGRAPH_ALIGNMENT.JUSTIFY
            p.paragraph_format.space_after = Pt(12)
    
    return doc

def generate_initial_advice_doc(app_inputs):
    """Generates the initial advice summary document."""
    doc = Document()
    doc.styles['Normal'].font.name, doc.styles['Normal'].font.size = 'Arial', Pt(11)
    p = doc.add_paragraph()
    add_formatted_runs(p, "Initial Advice Summary - Matter Number: {matter_number}", app_inputs['placeholder_map'])
    p.paragraph_format.space_after = Pt(12)
    table = doc.add_table(rows=3, cols=2)
    table.style = 'Table Grid'
    advice_date = app_inputs['initial_advice_date'].strftime('%d/%m/%Y') if app_inputs.get('initial_advice_date') else ''
    rows_data = [
        ("Date of Advice", advice_date),
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

# --- Streamlit UI ---
st.set_page_config(layout="wide", page_title="Ramsdens Client Care Letter Generator")
st.title("Ramsdens Client Care Letter Generator")

firm_details = load_firm_details()
precedent_content = load_precedent_text()
if not precedent_content:
    st.stop()

with st.form("input_form"):
    st.header("1. Letter & Client Details")
    c1, c2 = st.columns(2)
    with c1:
        our_ref = st.text_input("Our Reference", "PDP/10011/001")
        your_ref = st.text_input("Your Reference", "REF")
        letter_date = st.date_input("Letter Date", datetime.today())
    with c2:
        client_name_input = st.text_input("Client Full Name / Company Name", "Mr. John Smith")
        client_address_line1 = st.text_input("Address Line 1", "123 Example Street")
        client_address_line2 = st.text_input("Address Line 2 (optional)", "SomeTown")
        client_postcode = st.text_input("Postcode", "EX4 MPL")
        client_type = st.radio("Client Type", ("Individual", "Corporate"), horizontal=True)

    st.header("2. Initial Advice & Case Details")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Initial Advice Summary")
        initial_advice_content = st.text_area("Advice Given", "Advised on merits...", height=100)
        initial_advice_method = st.selectbox("Method", ["Phone Call", "In Person", "Teams Call"])
        initial_advice_date = st.date_input("Date", datetime.today())
    with c2:
        st.subheader("Case Track")
        claim_assigned_input = st.radio("Is claim already assigned?", ("No", "Yes"), horizontal=True)
        selected_track = st.selectbox("Which track applies?", ["Small Claims Track", "Fast Track", "Intermediate Track", "Multi Track"])

    st.header("3. Dynamic Content")
    qu1_dispute_nature = st.text_area('Dispute Nature', "a contractual matter ^lower case to start and end^", height=75)
    qu2_initial_steps = st.text_area('Initial Work', "^Per our recent discussions^ we agreed I would review documentation", height=100)
    qu3_timescales = st.text_area("Estimated Timescales", "^Start with cap and end with full stop^ The initial part of the Work will take around two to four weeks to complete and then when we have more information as to.", height=100)
    
    st.subheader("Estimated Initial Costs")
    hourly_rate = st.number_input("Your Hourly Rate (£)", value=295, step=5)
    cost_type_is_range = st.toggle("Use a cost range", True)
    if cost_type_is_range:
        lower_cost = st.number_input("Lower £", value=int(hourly_rate * 2))
        upper_cost = st.number_input("Upper £", value=int(hourly_rate * 3))
    else:
        fixed_cost = st.number_input("Fixed cost £", value=int(hourly_rate * 2.5))

    submitted = st.form_submit_button("Generate Documents")

if submitted:
    # 1. Collate all inputs
    costs_text = (f"£{lower_cost:,.2f} to £{upper_cost:,.2f} plus VAT" if cost_type_is_range 
                  else f"a fixed fee of £{fixed_cost:,.2f} plus VAT")
    
    roles = [("Partner", hourly_rate * 1.5), ("Senior Associate", hourly_rate), 
             ("Associate", hourly_rate * 0.8), ("Trainee", hourly_rate * 0.5)]
    fee_table = [f"{role}: £{rate:,.2f} per hour (excl. VAT)" for role, rate in roles]

    app_inputs = {
        'client_type': client_type,
        'claim_assigned': claim_assigned_input == "Yes",
        'selected_track': selected_track,
        'fee_table': fee_table,
        'initial_advice_content': initial_advice_content, 
        'initial_advice_method': initial_advice_method,
        'initial_advice_date': initial_advice_date
    }
    
    placeholder_map = {
        'matter_number': sanitize_input(our_ref),
        'your_ref': sanitize_input(your_ref),
        'letter_date': letter_date.strftime('%d %B %Y'),
        'client_name_input': sanitize_input(client_name_input),
        'client_address_line1': sanitize_input(client_address_line1),
        'client_address_line2_conditional': sanitize_input(client_address_line2) if client_address_line2 else "",
        'client_postcode': sanitize_input(client_postcode),
        'qu1_dispute_nature': sanitize_input(qu1_dispute_nature),
        'qu2_initial_steps': sanitize_input(qu2_initial_steps),
        'qu3_timescales': sanitize_input(qu3_timescales),
        'qu4_initial_costs_estimate': costs_text,
        'name': sanitize_input(firm_details["person_responsible_name"]),
    }
    placeholder_map.update(firm_details)
    app_inputs['placeholder_map'] = placeholder_map

    # 2. Generate documents
    try:
        care_letter_doc = generate_client_care_document(precedent_content, app_inputs)
        
        # Save care letter to a memory buffer
        client_care_doc_io = io.BytesIO()
        care_letter_doc.save(client_care_doc_io)
        client_care_doc_io.seek(0)
        
        # Generate advice note
        advice_doc_io = generate_initial_advice_doc(app_inputs)
        
        # Create Zip file
        client_name_safe = re.sub(r'[^\w\s-]', '', client_name_input).strip().replace(' ', '_')
        zip_io = io.BytesIO()
        with zipfile.ZipFile(zip_io, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.writestr(f"Client_Care_Letter_{client_name_safe}.docx", client_care_doc_io.getvalue())
            zipf.writestr(f"Initial_Advice_Summary_{client_name_safe}.docx", advice_doc_io.getvalue())
        zip_io.seek(0)
        
        st.success("✅ Documents Generated Successfully!")
        st.download_button("Download All Documents as ZIP", zip_io, f"Client_Docs_{client_name_safe}.zip", "application/zip")

    except Exception as e:
        st.error(f"An error occurred: {e}")
        logger.exception("Error during document generation:")
