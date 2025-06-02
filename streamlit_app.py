import streamlit as st
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import io
from datetime import datetime

# --- Helper function to add paragraphs with consistent spacing ---
def add_formatted_paragraph(doc, text, bold=False, space_after_pt=6, is_heading=False, heading_level=1):
    if is_heading:
        p = doc.add_heading(text, level=heading_level)
    else:
        p = doc.add_paragraph()
        run = p.add_run(text)
        if bold:
            run.bold = True
    
    # Set paragraph formatting (spacing)
    pf = p.paragraph_format
    pf.space_before = Pt(0) # No space before
    pf.space_after = Pt(space_after_pt) # Default space after, adjust as needed from precedent
    return p

# --- Streamlit App UI ---
st.set_page_config(layout="wide")
st.title("Client Care Letter Generator")

st.sidebar.header("Firm & Letter Details")
our_ref = st.sidebar.text_input("Our Reference", "DEPT/INITIALS/001")
your_ref = st.sidebar.text_input("Your Reference (if any)", "CLIENT/MATTER/001")
letter_date = st.sidebar.date_input("Letter Date", datetime.today())
firm_name = st.sidebar.text_input("Your Firm Name", "Your Law Firm LLP")
complaints_partner_name = st.sidebar.text_input("Complaints Partner Name", "Jane Doe")
complaints_partner_phone = st.sidebar.text_input("Complaints Partner Phone", "01234 567891")
complaints_partner_email = st.sidebar.text_input("Complaints Partner Email", "jane.doe@yourfirm.com")
bank_name = st.sidebar.text_input("Client Account Bank Name", "Global Bank Plc")
interest_threshold = st.sidebar.text_input("Interest Payment Threshold (£)", "50.00")
file_storage_years = st.sidebar.text_input("File Storage Years", "6")


st.header("Client Information")
client_name = st.text_input("Client Full Name / Company Name", "Mr. John Smith")
# client_address_line1 = st.text_input("Client Address Line 1") # Add if needed for letterhead
# client_address_line2 = st.text_input("Client Address Line 2")
# client_postcode = st.text_input("Client Postcode")

client_type = st.radio("Client Type:", 
                       ("Individual Client", "Corporate Client"), 
                       key="client_type_radio")

st.header("Dispute & Claim Details")
q1_dispute_nature = st.text_area("Q1: What is the nature of the dispute?", 
                                 "a contractual dispute regarding the supply of widgets",
                                 height=100)

claim_assigned = st.radio("Has the claim already been assigned to a court track?",
                          ("Yes - claim HAS ALREADY been assigned", "No - claim IS TO BE assigned"), 
                          key="claim_assigned_radio")

track_options = ["Small Claims Track", "Fast Track", "Intermediate Track", "Multi Track"]
selected_track = st.selectbox("Which court track applies or is anticipated?", track_options, key="track_select")

st.header("Scope of Work & Pricing")
q2_initial_advice = st.text_area("Q2: Set out the immediate steps that will be taken (this maybe a review of the facts and papers to allow you to advise in writing or making initial court applications or taking the first step, prosecuting or defending in a mainstream action). If you have agreed to engage counsel or other third party to assist you should also say so here.",
                                 "we will review the provided documentation, assess the merits of your claim, and provide you with initial written advice on potential next steps within 14 days",
                                 height=150)
q3_longer_term_instructions = st.text_area("Q3: Explain estimated time scale for completion of the Work)",
                                           "The initial work will take around 14 days to complete and then the further work is likely to depend on the outcome of the initial letters. The Work is likely to take a total time period of two to three months depending on the other side.",
                                           height=100)
q4_pricing_info = st.text_area("Q4: From the information you have provided us with to date, we estimate that our costs for the Work will be £[x] plus VAT. What is x?",
                               "1,000",
                               height=150)

st.header("Additional Financial Details")
disbursements_info = st.text_area("Anticipated Disbursements (e.g., court fees, expert fees - state 'None anticipated at this stage' if applicable)",
                                  "Court issue fees (approx. £XXX) and potentially barrister's fees for any hearing (approx. £YYY).",
                                  height=100)
billing_frequency = st.text_input("Billing Frequency (e.g., monthly, quarterly)", "monthly")
payment_due_days = st.text_input("Payment Due In (days)", "28")
interest_rate_over_base = st.text_input("Interest on Unpaid Bills (% over Base Rate)", "4")


if st.button("Generate Client Care Letter"):
    doc = Document()
    #Set default font for the document (optional, but can help consistency)
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Arial' # Or 'Times New Roman' etc.
    font.size = Pt(11) # Or your preferred size

    # --- P1: Refs and Date ---
    add_formatted_paragraph(doc, f"Our Ref: {our_ref}")
    add_formatted_paragraph(doc, f"Your Ref: {your_ref}")
    add_formatted_paragraph(doc, f"Date: {letter_date.strftime('%d %B %Y')}", space_after_pt=18) # More space after date block

    # --- P2: Salutation ---
    add_formatted_paragraph(doc, f"Dear {client_name},", space_after_pt=12)

    # --- P3: Thank you ---
    add_formatted_paragraph(doc, f"Further to our recent discussions, we now write to confirm the terms under which Ramsdens Solicitors LLP (\"Ramsdens\") will act for you. As a firm that is regulated by the Solicitors Regulation Authority, we are required to send you this letter which contains specific and prescribed information.", space_after_pt=12) 
    
    # Thank you for your instructions to act on your behalf in relation to {q1_dispute_nature}")

    # --- P4: This letter and Terms ---
    add_formatted_paragraph(doc, f"We enclose with this letter our Terms and Conditions of Business which must be read in conjunction with this letter. These documents are a formal communication and the language used is reflective of that. We hope that you understand. Please take the time to read these documents carefully. Where there is any conflict between this letter and our Terms and Conditions of Business, the terms of this letter will prevail. Your continuing instructions in this matter will amount to your acceptance of our Terms and Conditions of Business.", space_after_pt=12)
    
    # --- P5 & P6: Your instructions ---
    add_formatted_paragraph(doc, "Your instructions", is_heading=True, heading_level=1, space_after_pt=6) # Using Word's Heading 1 style
    add_formatted_paragraph(doc, f"We are instructed in relation to {q1_dispute_nature} (\"the Dispute\"). Per our recent discussions, in the first instance we are instructed to {q2_initial_advice} (\"the Work\").
    

    # --- P7 & P8: Work we will do ---
    add_formatted_paragraph(doc, "Work we will do", is_heading=True, heading_level=1, space_after_pt=6)
    add_formatted_paragraph(doc, f"This matter may develop over time and the nature of disputes is that opposing parties often seek to present facts and matters in a way that is favourable to their own case. We therefore cannot predict every eventuality but we will work with you to advise on any significant developments and review the overall strategy should that be required. Insofar as changes in the future may have a material impact on any cost estimates provided, we will discuss that with you. We will notify you of any material changes by telephone or in correspondence and we will of course always confirm any verbal advice in writing whenever you request that from us.", space_after_pt=12)
    # --- P9: Timescales ---
    add_formatted_paragraph(doc, "Timescales", is_heading=True, heading_level=1, space_after_pt=6) # Using Word's Heading 1 style
    if q3_longer_term_instructions and q3_longer_term_instructions.strip():
        add_formatted_paragraph(doc, q3_longer_term_instructions)

    # --- P10 & P11: Information on Pricing ---
    # In precedent, "Information on Pricing" is bold.
    para_pricing_heading = add_formatted_paragraph(doc, "Information on Pricing", bold=True, is_heading=True, heading_level=1, space_after_pt=6)
    # para_pricing_heading.runs[0].bold = True # Alternative way to bold specific run if not using heading style
    add_formatted_paragraph(doc, q4_pricing_info)

    # --- P12, P13, P14: Hourly rates, VAT, Cost updates ---
    add_formatted_paragraph(doc, "The hourly rates of the fee earners who may be involved in your matter are set out below: [PLACEHOLDER - You may want to add a specific text area for rates or have standard text here e.g., 'as per our separate schedule of rates' / 'Partner: £X, Solicitor: £Y etc.']")
    add_formatted_paragraph(doc, "We will add VAT to our charges at the rate that applies when the work is done. At present, VAT is 20%.")
    add_formatted_paragraph(doc, "We will provide you with the best possible information about the likely overall cost of your matter, both at the outset and as your matter progresses. If any unforeseen additional work becomes necessary (for example, due to unexpected difficulties or if your requirements or the circumstances significantly change during the course of the matter), we will inform you of this and provide you with an estimate of the additional costs.")

    # --- Conditional Track Paragraphs P23/P24 ---
    track_text_map = {
        "Small Claims Track": "this typically involves minimal procedural steps, focusing on the claim and defence, and often a short hearing. Disclosure of documents is limited, and witness statements are exchanged. Expert evidence is rare unless permitted by the court.",
        "Fast Track": "this involves a more structured timetable including standard disclosure, exchange of witness statements, and potentially expert evidence (usually a single joint expert). The trial is typically limited to one day.",
        "Intermediate Track": "this track is for claims that are too complex for the Fast Track but do not require the full case management of the Multi-Track. It has its own set of directions, disclosure requirements, and potential for more extensive expert evidence and a trial lasting a few days.",
        "Multi Track": "this involves comprehensive case management by the court, including a costs and case management conference (CCMC), detailed disclosure, exchange of lay and expert witness evidence, and a trial of potentially several days or weeks."
    }
    
    if claim_assigned == "Yes - claim HAS ALREADY been assigned":
        track_intro = f"As the claim has already been assigned by the Court to the {selected_track}, we anticipate that the following steps will be necessary: "
    else: # "No - claim IS TO BE assigned"
        track_intro = f"As the claim is yet to be assigned to a track by the Court, based on the current information, we anticipate it is likely to be allocated to the {selected_track}. The procedural steps will broadly follow those typical for this track: "
    
    add_formatted_paragraph(doc, track_intro + track_text_map.get(selected_track, "Details for the selected track will be provided."))


    # --- P15 & P16: Anticipated Disbursements ---
    add_formatted_paragraph(doc, "Anticipated Disbursements", is_heading=True, heading_level=1, space_after_pt=6)
    add_formatted_paragraph(doc, f"The likely disbursements in this matter are {disbursements_info}. We will obtain your approval before incurring any significant disbursements.")

    # --- P17 & P18: Billing Arrangements ---
    add_formatted_paragraph(doc, "Billing Arrangements", is_heading=True, heading_level=1, space_after_pt=6)
    add_formatted_paragraph(doc, f"We will send you interim bills on a {billing_frequency} basis. This will help you to budget for costs as well as keeping you informed of the legal expenses being incurred. Payment is due within {payment_due_days} days of your receiving our bill. We reserve the right to charge interest on unpaid bills at a rate of {interest_rate_over_base}% above the Bank of England base rate.")

    # --- P19 & P20: Complaints ---
    add_formatted_paragraph(doc, "Complaints", is_heading=True, heading_level=1, space_after_pt=6)
    add_formatted_paragraph(doc, f"We are committed to high quality legal advice and client care. If you are unhappy about any aspect of the service you have received, or about the bill, please contact {complaints_partner_name} on {complaints_partner_phone} or by e-mail to {complaints_partner_email} in the first instance so that we can do our best to resolve the problem for you. We have a procedure in place which details how we handle complaints, which is available on request.")

    # --- P21/P22: Ombudsman (conditional on client type) ---
    if client_type == "Individual Client":
        add_formatted_paragraph(doc, "If you are an individual, we are entitled to make a complaint to the Legal Ombudsman if you are not satisfied with our handling of your complaint. The Legal Ombudsman can be contacted at PO Box 6806, Wolverhampton, WV1 9WJ, by telephone on 0300 555 0333, or by email at enquiries@legalombudsman.org.uk. Any complaint to the Legal Ombudsman must usually be made within six months of your receiving a final written response from us about your complaint. For further information, you should contact the Legal Ombudsman.")
    else: # Corporate Client
        add_formatted_paragraph(doc, "If you are a business client (and not a small enterprise, charity, club, association, or trust that would qualify for the Legal Ombudsman scheme), complaints about our service should be directed to us in the first instance. If we are unable to resolve your complaint, you may have recourse through alternative dispute resolution (ADR) methods, but the Legal Ombudsman scheme is generally not available for larger businesses.")

    # --- P25 & P26: Interest on money held ---
    add_formatted_paragraph(doc, "Interest on money held for you", is_heading=True, heading_level=1, space_after_pt=6)
    add_formatted_paragraph(doc, f"Any money we hold on your behalf will be placed in our general client account with {bank_name}. We will account to you for interest earned on such funds where it is fair and reasonable to do so in all the circumstances, in accordanceance with the SRA Accounts Rules. Our policy is not to pay interest if the amount calculated is less than £{interest_threshold}.")

    # --- P27 & P28: Storage of papers ---
    add_formatted_paragraph(doc, "Storage of papers and documents", is_heading=True, heading_level=1, space_after_pt=6)
    add_formatted_paragraph(doc, f"After completing the work, we are entitled to keep all your papers and documents while there is money owing to us for our charges and expenses. We will keep our file of your papers for up to {file_storage_years} years, except those papers that you ask to be returned to you. We keep files on the understanding that we have the authority to destroy them {file_storage_years} years after the date of the final bill we send you for this matter. We will not destroy documents you ask us to deposit in safe custody.")

    # --- P29 & P30: Termination ---
    add_formatted_paragraph(doc, "Termination", is_heading=True, heading_level=1, space_after_pt=6)
    add_formatted_paragraph(doc, "You may terminate your instructions to us in writing at any time, but we will be entitled to keep all your papers and documents while there is money owing to us for our charges and expenses. We may decide to stop acting for you only with good reason, for example, if you do not pay an interim bill or comply with our request for a payment on account. We must give you reasonable notice that we will stop acting for you.")

    # --- P31 & P32: Applicable Law ---
    add_formatted_paragraph(doc, "Applicable Law", is_heading=True, heading_level=1, space_after_pt=6)
    add_formatted_paragraph(doc, "Our relationship with you is governed by English law and subject to the exclusive jurisdiction of the English courts.")

    # --- P33 & P34: Conclusion ---
    add_formatted_paragraph(doc, "Conclusion", is_heading=True, heading_level=1, space_after_pt=6)
    add_formatted_paragraph(doc, "We hope this information is helpful. Please sign and return the enclosed copy of this letter to confirm your agreement to these terms. We look forward to working with you.", space_after_pt=18) # More space before closing

    # --- P35, P36, P37: Closing ---
    add_formatted_paragraph(doc, "Yours sincerely,", space_after_pt=18) # Space for signature
    add_formatted_paragraph(doc, f"{firm_name}")
    add_formatted_paragraph(doc, "Solicitor") # Or specific solicitor name if collected

    # --- Save to buffer and provide download ---
    doc_io = io.BytesIO()
    doc.save(doc_io)
    doc_io.seek(0)

    st.success("Client Care Letter Generated!")
    st.download_button(
        label="Download Word Document",
        data=doc_io,
        file_name=f"Client_Care_Letter_{client_name.replace(' ', '_')}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    
