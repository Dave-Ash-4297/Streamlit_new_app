import streamlit as st
import re
from io import BytesIO # For file download

# --- TEMPLATE STRING ---
# (Ensure this is the complete and correct template you want to use)
TEMPLATE = """$$ALL[
1.	Further to our recent discussions, we now write to confirm the terms under which Ramsdens Solicitors LLP (“Ramsdens”) will act for you. As a firm that is regulated by the Solicitors Regulation Authority, we are required to send you this letter which contains specific and prescribed information.
2.	We enclose with this letter our Terms and Conditions of Business which must be read in conjunction with this letter. These documents are a formal communication and the language used is reflective of that. We hope that you understand. Please take the time to read these documents carefully. Where there is any conflict between this letter and our Terms and Conditions of Business, the terms of this letter will prevail. Your continuing instructions in this matter will amount to your acceptance of our Terms and Conditions of Business.
Your Instructions
3.	We are instructed in relation to $$[ SET OUT THE NATURE OF THE DISPUTE ]$$ (“the Dispute”). Per our conversations, in the first instance we are instructed to $$[ HERE EXPLAIN THE IMMEDIATE STEPS TO BE TAKEN- IN THE FIRST INSTANCE THIS MAY BE TO REVIEW THE PAPERS AND FACTS AND THEN ALLOW US TO ADVISE LATER OR ABOUT AN APPLICATION OR COURT CLAIM ETC IF WE HAVE AGREED TO INSTRUCT COUNSEL WE MUST SAY SO HERE ]$$  (“the Work”).
4.	This matter may develop over time and the nature of disputes is that opposing parties often seek to present facts and matters in a way that is favourable to their own case. We therefore cannot predict every eventuality but we will work with you to advise on any significant developments and review the overall strategy should that be required. Insofar as changes in the future may have a material impact on any cost estimates provided, we will discuss that with you. We will notify you of any material changes by telephone or in correspondence and we will of course always confirm any verbal advice in writing whenever you request that from us.
Timescales
5.	$$[EXPLAIN TIME SCALE TO COMPLETE THE WORK]$$
Action Required To Be Taken By You
Client Identification and Money Laundering
6.	Solicitors are required by law to obtain evidence of their client’s identity and address to satisfy money laundering and client identification regulations. This includes clients that are corporate entities. ]$$ALL
$$1/2[FOR INDIVIDUAL CLIENTS
7.	To comply with the individual identity requirement, you have two options:
a.	We can carry out a remote ID verification of you and your ID documents using a SmartSearch facility.  If you would like us to verify your identification remotely please provide your name, address, date of birth, personal email and mobile number. Once the search has been undertaken, SmartSearch will send you a text or email with a link to use on your smartphone which will require you to take a photo of your ID document and then yourself which it will then upload to its system that will check the document, provide us with a copy, and verify that you are the person on the ID document. The process is quick and easy, and avoids you having to send in ID documents to us. Or:
b.	You can provide us with two documents referred to in the list below, one photographic and one showing your current address.  If you are local to any of our offices please call with your original documents and they will be copied whilst you wait and the copies forwarded to us.
•	Current signed passport;
•	Household utility bill;
•	Residence permit issued by the Home Office to EEA nationals on sight of own country passport;
•	Current UK or EEA photo-card driving licence; or
•	National Identity Card containing a photograph. ]$$1/2
$$2/2[ FOR CORPORATE CLIENTS
7.	We will make our own enquiries and obtain documentation from Companies House to identify our corporate client. If you believe Companies House’s records to be out of date, please let us know as soon as possible. We may also require documentation or information from the company itself.  We are also obliged to identify the individuals at the corporate client who provide us with instructions, which usually means directors of limited companies or members/partners in LLPs, and sometimes we must do the same for “beneficial owners”. Either situation may include you as the recipient of this letter, but may also include other people at the business. We will tell you who else may be required to provide identification. To comply with the individual identity requirement, you have two options:
a.	We can carry out a remote ID verification of you and your ID documents using a SmartSearch facility.  If you would like us to verify your identification remotely please provide your name, address, date of birth, personal email and mobile number. Once the search has been undertaken, SmartSearch will send you a text or email with a link to use on your smartphone which will require you to take a photo of your ID document and then yourself which it will then upload to its system that will check the document, provide us with a copy, and verify that you are the person on the ID document. The process is quick and easy, and avoids you having to send in ID documents to us.
b.	You can provide us with a copy of one of the documents referred to on the list below. If you are local to any of our offices please call with your original documents and they will be copied whilst you wait and the copies forwarded to us.
•	Current signed passport;
•	Household utility bill;
•	Residence permit issued by the Home Office to EEA nationals on sight of own country passport;
•	Current UK or EEA photo-card driving licence; or
•	National Identity Card containing a photograph. ]$$2/2
8.	$$ALL[ Please note that until these identification requirements have been satisfied, we may not be able to accept any money from you or make any substantial progress with your matter. It is therefore important that you provide your documents as soon as possible to avoid any delays.
Document Preservation and Disclosure
9.	In the event that your matter is litigated before a Court, all parties will be required to give full disclosure of all material relevant to the Dispute. It is therefore essential that you preserve any and all such material that includes correspondence, documents, emails, text and SMS messages and/or other electronic communications of any sort. Your disclosure obligations include an obligation to disclose material that may harm your case or help your opponent’s case, as well as those on which you may rely or which help. If any device on which any such material is stored is to be disposed of or ceases to be used, you must ensure that copies are kept of the material.
People Responsible For Your Case
10.	I shall be the person with responsibility for your case.  My name is Paul Pinder and I am a Senior Associate with the firm.  My work will be carried out under the supervision of Nick Armitage who is a Partner of the firm.
11.	The easiest way to communicate with me will be either by telephone on 01484 821558or via email to paul.pinder@ramsdens.co.uk.
12.	There may be occasions when I am not immediately available to speak or meet with you and in these circumstances you should ask to speak to my Assistant   who will be able to help you.
13.	At Ramsdens we aim to provide the best possible service to our clients and in order to do this we may arrange for one of our client care team to contact you to discuss how we are doing and what we might do better.  Please let us know if you would prefer not to be contacted by our team during our handling of your matter.  We do however, need to know from you if you feel dissatisfied about the service you are receiving. Should you have any occasion to feel unhappy about our service please let me know straight away and I will discuss this with you.  If you are unable to resolve matters with me and still have concerns regarding our service, contact Nick Armitage on 01484 507121 who will attempt to resolve your concerns with you.  Formal complaints will be dealt with in accordance with our Firm's complaints procedures which can be provided on request.  In the event you are not satisfied with our handling of your complaint you can contact the Legal Ombudsman, full details will be given as part of our complaints procedure.
14.	You also have a right to complain about any bill sent by us by applying to the Court for an assessment of the bill under Part III of the Solicitors Act 1974.
Costs and Disbursements
Costs
15.	Our charges to you will be calculated and incurred on a time-spent basis. Time will be recorded on your matter in units of six minutes for letters (generally representing a unit per page or part thereof), emails written (again, representing a unit per equivalent to a page of normal letter) and telephone calls made and received.
16.	Our current hourly charge-out rates, exclusive of VAT, are as follows:
Fee Earner Position Hourly Charge-Out Rate
$$[RATE TABLE TO INSERT]$$
17.	Our hourly charge-out rates are reviewed periodically and we will notify you of any increases. We will also notify you of any changes in the status of legal personnel and their hourly charge-out rate. Unless otherwise agreed with you, we will account to you every month for the fees that have been incurred in relation to this matter. If you require an up to date statement of fees incurred at any time then please ask us and we will provide you with that information. Unless otherwise stated, interim bills are on account of costs and are usually prepared taking into account the value of the time recorded against the matter as at the date of the interim bill. If we hold any monies on account of your costs when an invoice is raised, these monies will be utilised towards discharging the invoice.
Disbursements
18.	Our hourly charge-out rates do not include expenses for which we will be responsible on your behalf.  These expenses are referred to as disbursements and may include travel or accommodation expenses, Court fees or the costs of Barristers or expert witnesses. Where possible, we will endeavour to seek your permission prior to instructing a third party in relation to your matter.
19.	We will not pay out any disbursements on your behalf until the monies have been paid by you.
Legal Expenses Insurance ]$$ALL
$$1/2[ FOR INDIVIDUAL CLIENTS
20.	It may be that you or a member of your household has the benefit of legal expenses insurance that might cover you for legal costs in connection with this matter. If you wish us to check your eligibility, please let us have a copy of the relevant insurance schedule and policy document. Alternatively you may be entitled to have your liability for costs paid by another person; for example, an employer or Trade Union. Again, please let us know if you wish us to assist you in checking such eligibility. Please note that you will remain responsible for our charges until such time as any legal expenses insurers have agreed to cover you for our legal costs. ]$$1/2
$$2/2[ FOR CORPORATE CLIENTS
21.	It may be possible to purchase “After the Event” legal expenses insurance cover to cover your opponents, or, possibly, your costs in this matter. If you wish to explore the possibility of such insurance cover, please let us know. Please bear in mind, though, that there will be costs involved in making an application for cover, and it is likely that a large premium (the amount of which will depend on the amount of costs protected and the prospects of success) will be payable at the outset and possibly on any subsequent anniversary of the inception of the policy. ]$$2/2
$$ALL[ Your Costs Responsibility to Ramsdens
22.	Our charges to you are not contingent upon the result of your case. You are primarily responsible for the payment of our costs and disbursements. Whilst we may be able to recover a portion of your costs from your opponent, this is not always possible and does not affect your primary responsibility to pay our costs and disbursements.
Section 74 Solicitors Act 1974 Agreement & Recovery of Costs
23.	It is common in litigation that even where costs are recoverable from an opponent, such recovery will not equate to the level of costs incurred by the successful party. Our agreement expressly permits us to charge an amount of costs greater than that which you will recover or could have recovered from your opponent, and expressly permits payment of such sum.
24.	This part of our agreement is made under section 74(3) of the Solicitors Act 1974 and Civil Procedure Rules 46.9 (2) and (3).
25.	If a Court orders your opponent to pay your costs, you should be aware that:
a.	You will have to pay the costs to us in the first instance and you may then be reimbursed when cleared funds are received from your opponent.
b.	You are unlikely to recover the entirety of our charges from your opponent. In most cases there will be a shortfall between our charges to you and the amount of costs that you may recover from your opponent. This shortfall may arise because your claim is subject to the fixed recoverable costs regime (see below) or because there is a difference between our hourly charge-out rates and the guideline hourly charge-out rates that are considered by the Court when assessing some costs. In so far as any costs or disbursements are of an unusual nature or amount, these costs might not be recoverable from your opponent.
c.	In the unlikely event that your claim is subject to the fixed recoverable costs regime (see below) and the fixed costs recoverable from your opponent exceed the level of our charges calculated and incurred on a time-spent basis, you agree that the charges due to us from you will be the amount of fixed costs recoverable from your opponent.
d.	Your opponent may refuse to comply with the Court’s order. If they do not pay, then you may seek to enforce the Court’s order (for example by sending in the bailiffs or obtaining a charge over property owned by them). However, you should be aware that this itself costs more money and takes time.
e.	Your opponent may have very little by way of assets or they may simply disappear. If this happens then you will not be able to recover your costs or indeed any other monies awarded to you. That is why it is important that in financial disputes you consider now whether your opponent has sufficient assets to pay you a lump sum or instalments as appropriate.
f.	There may be points during your case (including at its conclusion) where you are successful only in part on the issues in it, as a result of which you are entitled to payment of some of your costs by your opponent.
g.	If your opponent receives funding from the Community Legal Service, there are statutory controls on the amount of costs that can be recovered from them. In these circumstances, it is highly unlikely that the Court will make an order that your opponent would have to contribute anything to your costs.
Fixed Recoverable Costs
26.	Depending upon the value and complexity of a claim, the Court will allocate it to one of four ‘tracks’ when managing the case. The Court can fix the costs payable by your opponent, even where your claim is successful; this means that the amount of the costs that can be recovered may be fixed by the Court. ]$$ALL
$$1/8[ FOR CLAIMS THAT HAVE ALREADY BEEN ALLOCATED OPTIONS SMALL CLAIM ALREADY
27.	From the information that you have supplied us with, your claim has already been allocated to the Small Claims Track which is the normal track for claims with a monetary value of £10,000 or less.
28.	Having been allocated to the Small Claims Track, the normal rule is that only the following limited costs are recoverable by a successful party:
a.	Any Court fees paid.
b.	Fixed issue costs range between £50 and £125.
c.	Loss of earnings not exceeding £95 per person per day.
d.	Expenses reasonably incurred in travelling to and from and attending a Court hearing.
e.	A sum not exceeding £750 for any expert's fees.
f.	There are some exceptions to the usual rule, and the Court can award costs against a party that has acted unreasonably. However, in practice, such awards are rare. ]$$1/8
$$2/8[ FAST TRACK
29.	Based on the information you have provided, your claim has already been allocated to the Fast Track, which is the normal track for claims with a monetary value between £10,000 and £25,000.
30.	Having been allocated to the Fast Track, the Court has alsoassigned your/your opponent's claim to Band 1/2/3/4. As the Claimant/Defendant in the proceedings, we know that the costs that may be recoverable from your opponent/you will be fixed depending upon the stage of the proceedings in which the claim is resolved. A table setting out these fixed recoverable costs is enclosed with this letter. ]$$2/8
$$3/8[ INTERMEDIATE TRACK ££
31.	From the information you have supplied us with, your claim has already been allocated to the Intermediate Track, which is the normal track for claims with a monetary value between £25,000 and £100,000.
32.	Having been allocated to the Intermediate Track, the Court has also assigned your/your opponent's claim to Band 1/2/3/4. As the Claimant/Defendant in the proceedings, we know that the costs that may be recoverable from your opponent/you will be fixed depending upon the stage of the proceedings in which the claim is resolved. A table setting out these fixed recoverable costs is enclosed with this letter . ]$$3/8
$$4/8[ MULTI TRACK
33.	Based on the information you have provided, your claim has already been allocated to the Multi-Track, which is the normal track for claims with a monetary value over £100,000.
34.	Having been allocated to the Multi-Track, this means that the fixed costs regime does not apply to your/your opponent's claim and the general rule that the 'loser pays the winner's costs' will apply, subject to any costs budgeting that has been implemented by the Court and the caveats set out at paragraph 26. ]$$4/8
$$5/8[ SMALL CLAIMS TO ALLOCATE
35.	From the information you have supplied us with, it is likely that if court proceedings were to be commenced, this claim would be allocated to the Small Claims Track, which is the normal track for claims with a monetary value of £10,000 or less.
a.	Upon allocation to the Small Claims Track, the normal rule is that only the following limited costs are recoverable by a successful party:
b.	Any Court fees paid.
c.	Fixed issue costs ranging between £50 and £125.
d.	Loss of earnings not exceeding £95 per person per day.
e.	Expenses reasonably incurred in travelling to and from and attending a Court hearing.
f.	A sum not exceeding £750 for any expert's fees.
g.	There are some exceptions to the normal rule and the Court can award costs against an party that has acted unreasonably. However, in practice such awards are rare. ]$$5/8
$$6/8[ FAST TRACK TO ALLOCATE
36.	From the information you have supplied us with, it is likely that if court proceedings were to be commenced, this claim would be allocated to the Fast Track, which is the normal track for claims with a monetary value between £10,000 and £25,000.
37.	Upon allocation to the Fast Track, the Court will assign your/your opponent’s claim to one of four ‘bands’ depending upon the complexity and number of issues in the claim. When the claim is assigned, as the Claimant/Defendant in the proceedings, we will know that the costs that may be recoverable from your opponent/you will be fixed dependent upon the stage of the proceedings in which the claim is resolved. A table setting out these fixed recoverable costs is enclosed with this letter.  ]$$6/8
$$7/8[ INTERMEDIATE-TRACK TO ALLOCATE
38.	From the information you have supplied us with, it is likely that if court proceedings were to be commenced, this claim would be allocated to the Intermediate Track, which is the normal track for claims with a monetary value between £25,000 and £100,000.
39.	Upon allocation to the Intermediate Track, the Court will assign your/your opponent's claim to one of four 'bands' depending upon the complexity and number of issues in the claim. When the claim is assigned, as the Claimant/Defendant in the proceedings, we know that the costs that may be recoverable from your opponent/you will be fixed dependent upon the stage of the proceedings in which the claim is resolved. A table setting out these fixed recoverable costs is enclosed with this letter. ]$$7/8
$$8/8[ MULTI-TRACK TO ALLOCATE
40.	From the information you have supplied us with, it is likely that if court proceedings were to be commenced, this claim would be allocated to the Multi-Track, which is the normal track for claims with a monetary value over £100,000.
41.	Upon allocation to the Multi-Track, the fixed costs regime will not apply to your/your opponent's claim and the general rule that the 'loser pays the winner's costs' will apply, subject to any costs budgeting that has been implemented by the Court and the caveats set out at paragraph 26. ]$$8/8
$$ALL[ Costs Advice
42.	From the information you have provided us with to date, we estimate that our costs for the Work will be $$[SET OUT THE COSTS PLUS VAT]$$. If any further work is required thereafter, we will discuss the likely associated costs with you beforehand.
43.	It is always difficult to give an indication of the likely costs to be incurred in cases of this type. This is because it is impossible to say at this stage when the case may be brought to a conclusion and the amount of work that may be required to reach that point. The vast majority of cases are settled without the need for Court proceedings and of those where Court proceedings are commenced, the majority are settled without a trial. The actual amount of costs to be incurred will depend upon the arguments being advanced and the amount and nature of the evidence involved. The more evidence that is required, the greater the amount of time that will be spent on it by the parties and the Court and, therefore, the greater the costs.
a.	The involvement of expert evidence (such as in the form of valuation evidence) will also contribute to an increase in the costs involved.
b.	In the event that it may appear that our initial estimate of costs may be exceeded, we will notify you of these changes. We will review our estimate of costs at least every six months.
c.	There may be occasions during the conduct of your case where significant disbursements or major amounts of chargeable time are due to be incurred. We reserve the right to seek payment in advance for these commitments, and routinely do so. In the event that we do seek such payment in advance and it is not made by any reasonable deadline set, we reserve the right to cease acting for you in this matter. In the event that we do cease to act we would attempt to mitigate the impact that doing so would have on your case but it is possible that your case may be prejudiced as a result. We also reserve the right to cease acting for you in the event that any bills rendered to you are not paid within the timescale required.
d.	To this extent, you agree with us that our retainer in this matter is not to be considered an entire agreement, such that we are not obliged to continue acting for you to the conclusion of the matter and are entitled to terminate your retainer before your case is concluded. We are required to make this clear because there has been legal authority that in the absence of such clarity a firm was required to continue acting in a case where they were no longer being funded to do so.
e.	You have a right to ask for your overall cost to be limited to a maximum and we trust you will liaise with us if you wish to limit your costs. We will not then exceed this limit without first obtaining your consent. However this does mean that your case may not be concluded if we have reached your cost limit.
f.	In Court or some Tribunal proceedings, you may be ordered to pay the costs of someone else, either in relation to the whole of the costs of the case if you are unsuccessful or in relation to some part or issue in the case. Also, you may be ordered to pay the costs of another party during the course of proceedings in relation to a particular application to the Court. In such case you will need to provide this firm with funds to discharge such liability within seven days as failure to do so may prevent your case progressing. Please be aware that once we issue a Court or certain Tribunal claims or counterclaim on your behalf, you are generally unable to discontinue your claim or counterclaim without paying the costs of your opponent unless an agreement on costs is reached.
Limitation of Liability
44.	The liability of Ramsdens Solicitors LLP, its partners and employees in any circumstances whatsoever, whether in contract, tort, statute or otherwise and howsoever caused (including our negligence) for loss or damage arising from or in connection with the provision of services to you shall be limited to the sum of £3,000,000.00 (three million pounds) excluding costs and interest.
Bank Accounts and Cybercrime
45.	Should we ask you to pay money to us during the course of your matter then please send your funds to our account held with Barclays Bank PLC at 17 Market Place, Huddersfield to:
Account Name:              Ramsdens Solicitors LLP Client Account
Sort Code:                     20-43-12
Account Number:          03909026
46.	Should you receive any email correspondence regarding our bank account details please telephone your usual contact at Ramsdens before sending your first payment to verify that the details you have been given are correct. We would never advise our clients of any change in our bank account details by email. Should this happen please treat the email as suspicious and contact us immediately. Please do not send any funds until you have verified that the details are correct.
47.	Similarly, if an occasion arises whereby we need to send money to you, we will not accept your bank account details by email without further verification. It is likely that we will telephone you to confirm that the details supplied to us are correct.
Quality Standard
48.	Our firm is registered under the Lexcel quality standard of the Law Society. As a result of this we are or may become subject to periodic checks by outside assessors. This could mean that your file is selected for checking, in which case we would need your consent for inspection to occur. All inspections are, of course, conducted in confidence. If you prefer to withhold consent, work on your file will not be affected in any way. Since very few of our clients do object to this we propose to assume that we do have your consent unless you notify us to the contrary. We will also assume, unless you indicate otherwise, that consent on this occasion will extend to all future matters which we conduct on your behalf. Please do not hesitate to contact us if we can explain this further or if you would like us to mark your file as not to be inspected. Alternatively if you would prefer to withhold consent please put a line through this section in the copy letter and return to us.
Data Protection
49.	The enclosed Privacy Notice explains how and why we collect, store, use and share your personal data. It also explains your rights in relation to your personal data and how to contact us or supervisory authorities in the event you have a complaint. Please read it carefully. This Privacy Notice is also available on our website, www.ramsdens.co.uk.
50.	Our use of your personal data is subject to your instructions, the EU General Data Protection Regulation (GDPR), other relevant UK and EU legislation and our professional duty of confidentiality. Under data protection law, we can only use your personal data if we have a proper reason for doing so. Detailed reasons why we may process your personal data are set out in our Privacy Notice but examples are:
a.	To comply with our legal and regulatory obligations;
b.	For the performance of our contract with you or to take steps at your request before entering into a contract; or
c.	For our legitimate interests or those of a third party, including:
i.	Operational reasons, such as recording transactions, training and quality control;
ii.	Updating and enhancing client records;
iii.	Analysis to help us manage our practice; and
iv.	Marketing, such as by sending you updates about subjects and/or events that may be of interest to you.
51.	However, this does not apply to processing sensitive personal data about you, as defined. If it is necessary to process this data for the continued provision of our services to you, we will need your explicit consent for doing so and will request this from you as required.
Marketing Communications
52.	We would like to use your personal data to send you updates (by email, telephone or post) about legal developments that might be of interest to you and/or information about our services.
53.	This will be done pursuant to our Privacy Notice (referred to above), which contains more information about our and your rights in this respect.
54.	You have the right to opt out of receiving promotional communications at any time, by:
a.	Contacting us by email on dataprotection@ramsdens.co.uk;
b.	Using the ‘unsubscribe’ link in emails; or
c.	Writing to Marketing Department at: Ramsdens Solicitors LLP, Oakley House, 1 Hungerford Road, Edgerton, Huddersfield, HD3 3AL.
Yours faithfully
Ramsdens Solicitors
Direct Tel: 01484 821558
Direct Fax: 01484 558083
paul.pinder@ramsdens.co.uk}$$ALL
"""

# --- Helper Function to convert number to letter (for a, b, c lists) ---
def num_to_alpha(n):
    """Converts 1 to a, 2 to b, ..., 26 to z."""
    if n <= 0 or n > 26:
        return str(n) # Fallback for out of range
    return chr(ord('a') + n - 1)

# --- Helper Function to convert number to roman numeral (for i, ii, iii lists) ---
def num_to_roman_lower(num):
    """Converts number to lowercase Roman numeral (simplified for small numbers)."""
    if not 0 < num < 40: # Basic check, extend if needed
        return str(num) # Fallback
    val = [
        10, 9, 5, 4, 1
        ]
    syb = [
        "x", "ix", "v", "iv", "i"
        ]
    roman_num = ''
    i = 0
    while  num > 0:
        for _ in range(num // val[i]):
            roman_num += syb[i]
            num -= val[i]
        i += 1
    return roman_num

# --- Core Logic Function ---
def process_template_logic(template_text, conditional_choices, placeholder_inputs):
    # 0. Pre-processing: Store original list markers and clean lines
    lines_with_original_markers = []
    cleaned_lines_for_processing = []

    # Regex to capture leading list markers (numbers, letters, bullets) and the rest of the line
    # Handles: "1.", "1.\t", "a.", "a.\t", "i.", "i.\t", "•", "•\t"
    # And also section headers that are not numbered but should be preserved.
    list_marker_pattern = re.compile(r"^\s*([0-9]+[.]|[a-z][.]|[ivx]+[.]|[•])?\s*(.*)", re.IGNORECASE)
    section_header_pattern = re.compile(r"^\s*([A-Za-z\s]+[^a-z0-9\s\.•])\s*$", re.IGNORECASE) # Non-numbered headers

    for line in template_text.splitlines():
        stripped_line = line.strip()
        if not stripped_line: # Keep empty lines for spacing
            lines_with_original_markers.append(("", "", line)) # marker, type, original_text
            cleaned_lines_for_processing.append(line)
            continue

        match = list_marker_pattern.match(line)
        if match:
            marker_with_space = match.group(1) if match.group(1) else ""
            content = match.group(2)

            marker_type = ""
            if marker_with_space:
                marker = marker_with_space.strip().lower()
                if marker.endswith('.'):
                    if marker[:-1].isdigit():
                        marker_type = "decimal"
                    elif 'a' <= marker[:-1] <= 'z' and len(marker[:-1]) == 1:
                        marker_type = "alpha"
                    elif all(c in 'ivx' for c in marker[:-1]):
                        marker_type = "roman"
                elif marker == '•':
                    marker_type = "bullet"

            lines_with_original_markers.append((marker_with_space.strip(), marker_type, line))
            cleaned_lines_for_processing.append(content if marker_type else line) # Store only content if it was a list item

        else: # Non-list item line (e.g., section header, signature)
            lines_with_original_markers.append(("", "header", line)) # Keep original line
            cleaned_lines_for_processing.append(line)


    processed_text_intermediate = "\n".join(cleaned_lines_for_processing)


    # 1. Conditional Blocks ($$X/Y[...]$$X/Y)
    def conditional_replacer(match):
        # ... (conditional logic as before, operating on processed_text_intermediate) ...
        current_option = match.group(1)
        total_options_in_block_group = match.group(2)
        content = match.group(3)

        if total_options_in_block_group in conditional_choices:
            chosen_option_for_this_group = conditional_choices[total_options_in_block_group]
            if current_option == chosen_option_for_this_group:
                return content
            else:
                # Before returning empty, we need to adjust lines_with_original_markers
                # This is tricky because the content being removed might span multiple original lines.
                # For simplicity in this iteration, we'll rely on the re-numbering to fix gaps.
                # A more robust solution would mark lines for removal here.
                return ""
        return match.group(0)

    processed_text_intermediate = re.sub(
        r"\$\$([0-9]+)/([0-9]+)\[(.*?)\]\$\$\1/\2",
        conditional_replacer,
        processed_text_intermediate,
        flags=re.DOTALL
    )

    # 2. ALL Blocks ($$ALL[...]$$ALL)
    processed_text_intermediate = re.sub(
        r"\$\$ALL\[(.*?)\]\$\$ALL",
        r"\1",
        processed_text_intermediate,
        flags=re.DOTALL
    )

    # 3. Placeholder Blocks ($$[ Placeholder Text ]$$)
    placeholder_pattern = r"\$\$\[(.*?)\]\$\$"
    def replace_placeholder(match):
        placeholder_key = match.group(1).strip()
        user_text = placeholder_inputs.get(placeholder_key, f"") # Default to empty if skipped
        return user_text.replace("ENDPARA", "\n")

    processed_text_intermediate = re.sub(placeholder_pattern, replace_placeholder, processed_text_intermediate, flags=re.DOTALL)


    # 4. Re-assemble and Re-number
    final_lines = []
    main_para_counter = 0
    #alpha_counters = {} # To store current alpha count for each main_para_counter
    #roman_counters = {}  # To store current roman count for each main_para_counter
    #bullet_indent = "    " # For indenting bullet points if not directly under a,b,c etc.

    # We need to reconstruct based on the original structure and the processed content
    # The processed_text_intermediate now has the content, but split by newlines.
    # This makes it hard to map back directly to lines_with_original_markers if placeholders expanded to multiple lines.

    # Simpler re-numbering approach for now:
    # Iterate through the processed_text_intermediate line by line.
    # If a line is not empty and not a sub-item, it's a main paragraph.
    # This won't perfectly replicate complex nested lists from the original Word doc without more state.

    output_lines = []
    current_main_list_number = 0
    # These would need to be reset based on context if nesting is deeper or changes type
    current_alpha_list_char_code = ord('a')
    current_roman_list_number = 1
    # last_marker_type = None

    # Split the processed content, which now has placeholders filled and conditionals resolved
    processed_content_lines = processed_text_intermediate.splitlines()
    
    # Iterate through the *original* structure to guide renumbering
    original_line_idx = 0
    processed_line_idx = 0

    final_output_lines = []

    # This mapping is complex because placeholder expansion and conditional removal
    # changes the number of lines. A direct 1:1 mapping after processing is hard.
    #
    # New Strategy:
    # 1. Clean the *original* template (remove markers, $$...$$) to get a "base content" list.
    # 2. Clean the *processed* template (after $$...$$, placeholders) to get "final content" list.
    # 3. Attempt to align these. This is still non-trivial.
    #
    # Simplest Reliable Renumbering for now:
    #   - Strip all existing numbers from the processed_text_intermediate.
    #   - Identify paragraphs and apply new sequential numbering.
    #   - This version will *not* try to recreate a,b,c or i,ii,iii sub-lists automatically.
    #     It will treat everything that's not a section header or blank line as a main paragraph.
    #     This is a simplification due to the complexity of tracking nested list state from a text template.

    cleaned_for_renumbering = []
    for line in processed_text_intermediate.splitlines():
        # Strip any potential leading list markers that might have been introduced by user in placeholders
        # or survived from the original template parts not fully cleaned.
        temp_line = re.sub(r"^\s*([0-9]+[.]|[a-z][.]|[ivx]+[.]|[•])?\s*", "", line, 1)
        cleaned_for_renumbering.append(temp_line)
    
    renumbered_lines = []
    main_para_count = 0
    for line_content in cleaned_for_renumbering:
        stripped_content = line_content.strip()
        # Heuristic: if it's short and all caps or ends with colon, might be a header
        is_header_heuristic = (len(stripped_content) < 50 and stripped_content.isupper()) or \
                              (stripped_content.endswith(':') and not stripped_content[:-1].strip().endswith('.'))

        if not stripped_content: # Blank line
            renumbered_lines.append("")
        elif is_header_heuristic and not "$$[" in line_content : # A non-placeholder section header (crude check)
            renumbered_lines.append(line_content) # Keep headers as is
        elif "Ramsdens Solicitors" in line_content or "Direct Tel:" in line_content or "Yours faithfully" in line_content: # Signature block
             renumbered_lines.append(line_content)
        elif "Fee Earner" in line_content and "Hourly Charge-Out Rate" in line_content: # Rate table header
             renumbered_lines.append(line_content)
        else:
            main_para_count += 1
            renumbered_lines.append(f"{main_para_count}.\t{line_content.lstrip()}") # Ensure left alignment after number

    return "\n".join(renumbered_lines)


# --- Streamlit UI ---
st.set_page_config(page_title="Ramsdens Document Builder", layout="wide")
st.image("https://www.ramsdens.co.uk/wp-content/uploads/ramsdens-logo-fb.png", width=300) # Add your logo if you have a URL
st.title("Ramsdens Solicitors LLP - Initial Letter Builder")
st.markdown("---")

# --- Collect Conditional Choices ---
st.header("1. Select Document Options")

if 'conditional_choices' not in st.session_state:
    st.session_state.conditional_choices = {}

client_type_options_map = {
    "Individual Clients": "1",
    "Corporate Clients": "2"
}
client_type_descriptions = list(client_type_options_map.keys())
# Ensure default selection is valid if session_state is partially filled
default_client_key = st.session_state.conditional_choices.get("2", client_type_options_map[client_type_descriptions[0]])
default_client_desc = next((k for k, v in client_type_options_map.items() if v == default_client_key), client_type_descriptions[0])

selected_client_desc = st.radio(
    "Client Type (for Identification & Legal Expenses Insurance):",
    client_type_descriptions,
    key="client_type_radio",
    index=client_type_descriptions.index(default_client_desc)
)
st.session_state.conditional_choices["2"] = client_type_options_map[selected_client_desc]

claim_allocation_options_map = {
    "Small Claims - Already Allocated": "1",
    "Fast Track - Already Allocated": "2",
    "Intermediate Track - Already Allocated": "3",
    "Multi Track - Already Allocated": "4",
    "Small Claims - To Be Allocated": "5",
    "Fast Track - To Be Allocated": "6",
    "Intermediate Track - To Be Allocated": "7",
    "Multi Track - To Be Allocated": "8"
}
claim_alloc_descriptions = list(claim_allocation_options_map.keys())
default_claim_key = st.session_state.conditional_choices.get("8", claim_allocation_options_map[claim_alloc_descriptions[0]])
default_claim_desc = next((k for k, v in claim_allocation_options_map.items() if v == default_claim_key), claim_alloc_descriptions[0])

selected_claim_desc = st.selectbox(
    "Claim Allocation / Track Option:",
    claim_alloc_descriptions,
    key="claim_alloc_select",
    index=claim_alloc_descriptions.index(default_claim_desc)
)
st.session_state.conditional_choices["8"] = claim_allocation_options_map[selected_claim_desc]

st.markdown("---")
st.header("2. Fill in the Details")

if 'placeholder_inputs' not in st.session_state:
    st.session_state.placeholder_inputs = {}

temp_processed_for_placeholders = TEMPLATE
current_conditional_choices = st.session_state.conditional_choices

def temp_conditional_replacer(match):
    current_opt = match.group(1)
    total_opt_group = match.group(2)
    content = match.group(3)
    # Strip existing list markers from content before showing in placeholder UI
    content_cleaned = "\n".join([re.sub(r"^\s*([0-9]+[.]|[a-z][.]|[ivx]+[.]|[•])?\s*", "", line, 1) for line in content.splitlines()])
    if total_opt_group in current_conditional_choices and current_opt == current_conditional_choices[total_opt_group]:
        return content_cleaned
    return ""

# First pass: resolve conditionals
temp_processed_for_placeholders_cond = re.sub(
    r"\$\$([0-9]+)/([0-9]+)\[(.*?)\]\$\$\1/\2",
    temp_conditional_replacer,
    temp_processed_for_placeholders,
    flags=re.DOTALL
)
# Second pass: resolve ALL blocks
temp_processed_for_placeholders_all = re.sub(
    r"\$\$ALL\[(.*?)\]\$\$ALL",
    lambda m: "\n".join([re.sub(r"^\s*([0-9]+[.]|[a-z][.]|[ivx]+[.]|[•])?\s*", "", line, 1) for line in m.group(1).splitlines()]), # Strip markers
    temp_processed_for_placeholders_cond,
    flags=re.DOTALL
)

unique_placeholders_ordered = []
seen_placeholders = set()
for match in re.finditer(r"\$\$\[(.*?)]\$\$", temp_processed_for_placeholders_all, flags=re.DOTALL):
    ph_text_clean = match.group(1).strip()
    if ph_text_clean not in seen_placeholders:
        unique_placeholders_ordered.append(ph_text_clean)
        seen_placeholders.add(ph_text_clean)

if not unique_placeholders_ordered:
    st.info("No specific details required based on current selections, or all details are in fixed sections.")
else:
    st.markdown("Please provide the following information. For multi-paragraph input within a field, type `ENDPARA` where you want a new line within that field's content.")
    cols = st.columns(2)
    col_idx = 0
    for i, ph_text_clean in enumerate(unique_placeholders_ordered):
        default_value = st.session_state.placeholder_inputs.get(ph_text_clean, "")
        with cols[col_idx % 2]:
            user_val = st.text_area(
                f"{ph_text_clean}:",
                value=default_value,
                key=f"ph_input_{ph_text_clean.replace(' ', '_').lower().replace('[','').replace(']','').replace('/','_')}", # Make key more robust
                height=100 if len(ph_text_clean) < 80 else 150 # Slightly taller for longer prompts
            )
            st.session_state.placeholder_inputs[ph_text_clean] = user_val
        col_idx +=1

st.markdown("---")
if st.button("✨ Generate Document", type="primary", use_container_width=True):
    if not all(st.session_state.conditional_choices.values()):
        st.error("Please make selections for all document options.")
    else:
        current_placeholder_inputs = st.session_state.placeholder_inputs
        final_document = process_template_logic(TEMPLATE, st.session_state.conditional_choices, current_placeholder_inputs)
        st.session_state.generated_document = final_document

if 'generated_document' in st.session_state and st.session_state.generated_document:
    st.header("3. Generated Document")
    st.text_area("Completed Letter:", st.session_state.generated_document, height=600, key="output_text_area")

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="📥 Download as .txt",
            data=st.session_state.generated_document.encode('utf-8'),
            file_name="generated_letter.txt",
            mime="text/plain",
            use_container_width=True
        )
    with col2:
        try:
            from docx import Document
            from docx.shared import Pt
            from docx.enum.text import WD_ALIGN_PARAGRAPH

            doc = Document()
            # Example: Set default font for the document
            # style = doc.styles['Normal']
            # font = style.font
            # font.name = 'Calibri' # Or your firm's standard font
            # font.size = Pt(11)

            for line_text in st.session_state.generated_document.splitlines():
                p = doc.add_paragraph()
                if line_text.strip() == "": # Handle blank lines explicitly
                    continue # Or add an empty paragraph if specific spacing is needed: p.text = ""

                match_numbered = re.match(r"^\s*([0-9]+[.])\s*(.*)", line_text)
                # match_alpha = re.match(r"^\s*([a-z][.])\s*(.*)", line_text, re.IGNORECASE)
                # match_roman = re.match(r"^\s*([ivx]+[.])\s*(.*)", line_text, re.IGNORECASE)
                # match_bullet = re.match(r"^\s*[•]\s*(.*)", line_text)

                if match_numbered:
                    p.style = 'ListNumber' # Apply Word's built-in numbering
                    content = match_numbered.group(2)
                    p.add_run(content)
                # elif match_alpha:
                #     # For 'a.', 'b.' type lists, you might need a custom style or indent
                #     # For simplicity, treat as indented paragraph under ListNumber or new ListBullet
                #     p.text = f"\t{line_text.strip()}" # Simple tab indent
                # elif match_bullet:
                #      p.style = 'ListBullet'
                #      content = match_bullet.group(1)
                #      p.add_run(content)
                else: # Normal text, headers, signature
                    # For headers or special text, you could apply custom styles
                    if line_text.strip().isupper() and len(line_text.strip()) < 50 and not "$$[" in line_text:
                        run = p.add_run(line_text.strip())
                        run.bold = True
                        p.alignment = WD_ALIGN_PARAGRAPH.CENTER if "INSTRUCTIONS" in line_text.strip() else WD_ALIGN_PARAGRAPH.LEFT
                    else:
                         p.add_run(line_text)


            doc_io = BytesIO()
            doc.save(doc_io)
            doc_io.seek(0)

            st.download_button(
                label="📄 Download as .docx",
                data=doc_io,
                file_name="generated_letter_final.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
        except ImportError:
            st.warning("python-docx library not available. .docx download unavailable.")
        except Exception as e:
            st.error(f"Error creating .docx file: {e}")
            st.exception(e) # Print full traceback for debugging

st.markdown("---")
st.caption("Ramsdens LLP - Document Builder")