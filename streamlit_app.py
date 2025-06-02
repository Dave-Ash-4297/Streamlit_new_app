# --- Document Generation Logic ---
if st.button("Generate Client Care Letter"):
    doc = Document()
    
    style = doc.styles['Normal']
    style.font.name = DEFAULT_FONT_NAME
    style.font.size = DEFAULT_FONT_SIZE

    # Ensure your precedent_content string has newlines ONLY for actual paragraph breaks.
    # Manually check and fix line breaks like the one in "In Court or some Tribunal..."
    lines = precedent_content.split('\n')
    
    in_indiv_block = False; in_corp_block = False; active_track_block_type = None
    main_paragraph_counter = 0
    in_main_numbered_section = False
    
    numbered_para_left_indent_cm = 0.75
    numbered_para_first_line_indent_cm = -0.75 
    numbered_para_tab_stop_cm = 0.75

    sub_item_marker_effective_margin_cm = 0.75 
    sub_item_text_additional_indent_cm = 0.5
    sub_item_left_indent_cm = sub_item_marker_effective_margin_cm + sub_item_text_additional_indent_cm 
    sub_item_first_line_indent_cm = -sub_item_text_additional_indent_cm 
    sub_item_tab_stop_cm = sub_item_left_indent_cm 
    ind_item_indent_cm = 0.75 # Default for [ind] items

    FIRST_NUMBERED_PARAGRAPH_CONTAINS = "Further to our recent discussions, we now write to confirm the terms under which Ramsdens Solicitors LLP"
    STOP_NUMBERING_IF_LINE_IS = "Yours sincerely,"

    track_tags_map = {
        '[all_sc]': ("Yes", "Small Claims Track"), '[all_ft]': ("Yes", "Fast Track"),
        '[all_int]': ("Yes", "Intermediate Track"), '[all_mt]': ("Yes", "Multi Track"),
        '[sc]': ("No", "Small Claims Track"), '[ft]': ("No", "Fast Track"),
        '[int]': ("No", "Intermediate Track"), '[mt]': ("No", "Multi Track")
    }

    for line_idx, line_raw in enumerate(lines):
        current_line_stripped_for_logic = line_raw.strip()
        content_to_process_for_runs = current_line_stripped_for_logic 

        # --- State Management for Conditional Blocks (Tags on their own lines) ---
        is_pure_control_line = False
        # Client type block pure tags
        if current_line_stripped_for_logic == "[indiv]": in_indiv_block = True; is_pure_control_line = True
        elif current_line_stripped_for_logic == "[end indiv]": in_indiv_block = False; is_pure_control_line = True
        elif current_line_stripped_for_logic == "[corp]": in_corp_block = True; is_pure_control_line = True
        elif current_line_stripped_for_logic == "[end corp]": in_corp_block = False; is_pure_control_line = True
        else: # Track block pure tags
            # Check for track start tags
            if not active_track_block_type: # Only if not already in a track block
                for tag_key in track_tags_map:
                    if current_line_stripped_for_logic == tag_key:
                        active_track_block_type = tag_key; is_pure_control_line = True; break
            # Check for track end tags (only if a block is active and not just started)
            if active_track_block_type and not is_pure_control_line: 
                end_tag_for_current_block = f"[end {active_track_block_type[1:-1]}]"
                if current_line_stripped_for_logic == end_tag_for_current_block:
                    active_track_block_type = None; is_pure_control_line = True
        
        if is_pure_control_line: continue

        # --- Process lines that might have content AND tags ---
        _line_had_start_tag_this_iteration = False 
        _line_had_end_tag_this_iteration = False

        # Determine effective block states for *this line's content*
        current_line_in_indiv = in_indiv_block
        current_line_in_corp = in_corp_block
        current_line_in_track = active_track_block_type

        if content_to_process_for_runs.startswith("[indiv]"): current_line_in_indiv = True; _line_had_start_tag_this_iteration = True; content_to_process_for_runs = content_to_process_for_runs.removeprefix("[indiv]")
        if content_to_process_for_runs.endswith("[end indiv]"): _line_had_end_tag_this_iteration = True; content_to_process_for_runs = content_to_process_for_runs.removesuffix("[end indiv]")
        if content_to_process_for_runs.startswith("[corp]"): current_line_in_corp = True; _line_had_start_tag_this_iteration = True; content_to_process_for_runs = content_to_process_for_runs.removeprefix("[corp]")
        if content_to_process_for_runs.endswith("[end corp]"): _line_had_end_tag_this_iteration = True; content_to_process_for_runs = content_to_process_for_runs.removesuffix("[end corp]")
        
        if not current_line_in_track: # Check for start of track block on this line
            for tag_key in track_tags_map:
                if content_to_process_for_runs.startswith(tag_key): current_line_in_track = tag_key; _line_had_start_tag_this_iteration = True; content_to_process_for_runs = content_to_process_for_runs.removeprefix(tag_key); break
        if current_line_in_track: # Check for end of track block on this line
            end_tag_for_current_block = f"[end {current_line_in_track[1:-1]}]"
            if content_to_process_for_runs.endswith(end_tag_for_current_block): _line_had_end_tag_this_iteration = True; content_to_process_for_runs = content_to_process_for_runs.removesuffix(end_tag_for_current_block)
        
        final_content_after_all_stripping = content_to_process_for_runs.strip()

        # Update global states based on tags actually processed from this line
        if _line_had_start_tag_this_iteration:
            if content_to_process_for_runs.startswith("[indiv]"): in_indiv_block = True # This logic is tricky if tag was stripped
            # More accurate: use the temp states
            in_indiv_block = current_line_in_indiv
            in_corp_block = current_line_in_corp
            active_track_block_type = current_line_in_track


        # --- Determine if content from THIS line should be rendered based on APP_INPUTS ---
        should_render_this_line_content = True
        if current_line_in_indiv and app_inputs['client_type'] != "Individual": should_render_this_line_content = False
        elif current_line_in_corp and app_inputs['client_type'] != "Corporate": should_render_this_line_content = False
        
        if current_line_in_track and should_render_this_line_content: 
            target_assignment, target_track_name = track_tags_map[current_line_in_track]
            current_assignment_str = "Yes" if app_inputs['claim_assigned'] else "No"
            if not (current_assignment_str == target_assignment and app_inputs['selected_track'] == target_track_name):
                should_render_this_line_content = False
        
        # --- Substitute Placeholders ---
        current_content_substituted = final_content_after_all_stripping
        current_content_substituted = current_content_substituted.replace("{our_ref}", our_ref) 
        current_content_substituted = current_content_substituted.replace("{your_ref}", your_ref)
        current_content_substituted = current_content_substituted.replace("{letter_date}", letter_date.strftime('%d %B %Y'))
        current_content_substituted = current_content_substituted.replace("{client_name_input}", client_name_input)
        current_content_substituted = current_content_substituted.replace("{client_address_line1}", client_address_line1)
        current_content_substituted = current_content_substituted.replace("{client_address_line2_conditional}", client_address_line2 if client_address_line2 else "")
        current_content_substituted = current_content_substituted.replace("{client_postcode}", client_postcode)
        for key, val_firm in firm_details.items():
            current_content_substituted = current_content_substituted.replace(f"{{{key}}}", str(val_firm))


        # --- Numbering Section Logic ---
        if not in_main_numbered_section and FIRST_NUMBERED_PARAGRAPH_CONTAINS in current_content_substituted:
            in_main_numbered_section = True
        
        paragraph_number_prefix = ""; is_this_a_main_numbered_paragraph = False
        is_this_a_sub_item_type = None # Can be 'bp', 'ab', 'ind'

        if current_content_substituted == STOP_NUMBERING_IF_LINE_IS:
            in_main_numbered_section = False 
        elif in_main_numbered_section:
            should_get_main_number = True 

            # Corrected check for "[]To comply..." (Issue 4)
            # If the original stripped line was "[]" it's a spacer.
            # If it starts with "[]" but has text, it's content.
            if current_line_stripped_for_logic == "[]": 
                should_get_main_number = False
            elif not final_content_after_all_stripping: # Empty after all tag stripping (e.g. line was just [indiv][end indiv])
                should_get_main_number = False
            elif final_content_after_all_stripping.startswith("[bp]"): 
                is_this_a_sub_item_type = 'bp'; should_get_main_number = False
            elif re.match(r'\[([a-g])\]', final_content_after_all_stripping): 
                is_this_a_sub_item_type = 'ab'; should_get_main_number = False
            elif final_content_after_all_stripping.startswith("[ind]"):
                is_this_a_sub_item_type = 'ind'; should_get_main_number = False # [ind] items are not main numbered
            elif current_content_substituted == "[FEE_TABLE_PLACEHOLDER]": 
                should_get_main_number = False
            # IMPORTANT: Check if content is inside a conditional block (indiv/corp/track)
            # This is to prevent numbering paragraphs that are part of those blocks' specific details.
            # However, headings *within* these blocks (if any) might follow a different rule,
            # but your example shows headings like "Legal Expenses Insurance" *are* numbered.
            # The `is_pure_heading` check now only affects formatting, not the decision to number.
            elif current_line_in_indiv or current_line_in_corp or current_line_in_track:
                # If the line's content falls within one of these blocks, it generally shouldn't get a main number,
                # UNLESS it itself is a heading that your new style dictates should be numbered.
                # For now, this means text like "Solicitors are required by law..." won't get a main number.
                # The heading "Legal Expenses Insurance" will get a number because it's not *inside* such a block when its number is decided.
                if not (final_content_after_all_stripping.startswith(("[bold]", "[underline]")) and final_content_after_all_stripping.endswith("[end]")): # If it's NOT a heading within the block
                    should_get_main_number = False

            if should_get_main_number:
                main_paragraph_counter += 1
                paragraph_number_prefix = f"{main_paragraph_counter}.\t" 
                is_this_a_main_numbered_paragraph = True
        
        # --- Paragraph Rendering ---
        if current_line_stripped_for_logic == "[]": 
            if doc.paragraphs and should_render_this_line_content: 
                 doc.paragraphs[-1].paragraph_format.space_after = Pt(12)
        elif should_render_this_line_content and (final_content_after_all_stripping or current_line_stripped_for_logic == ""): 
            text_for_runs_final = paragraph_number_prefix + current_content_substituted
            
            p = doc.add_paragraph()
            pf = p.paragraph_format
            pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            
            para_style_to_apply = 'Normal'
            
            if is_this_a_main_numbered_paragraph:
                pf.left_indent = Cm(numbered_para_left_indent_cm)
                pf.first_line_indent = Cm(numbered_para_first_line_indent_cm)
                pf.tab_stops.add_tab_stop(Cm(numbered_para_tab_stop_cm))
            elif is_this_a_sub_item_type:
                pf.left_indent = Cm(sub_item_left_indent_cm)
                pf.first_line_indent = Cm(sub_item_first_line_indent_cm)
                pf.tab_stops.add_tab_stop(Cm(sub_item_tab_stop_cm)) 
                
                if is_this_a_sub_item_type == 'bp':
                    para_style_to_apply = 'ListBullet'
                    text_for_runs_final = current_content_substituted.replace("[bp]", "", 1).lstrip()
                elif is_this_a_sub_item_type == 'ind':
                     pf.left_indent = Cm(ind_item_indent_cm) 
                     pf.first_line_indent = Cm(0) 
                     pf.tab_stops.clear_all()
                     text_for_runs_final = current_content_substituted.replace("[ind]", "", 1).lstrip()
                elif is_this_a_sub_item_type == 'ab': 
                    match_ab = re.match(r'\[([a-g])\](.*)', final_content_after_all_stripping)
                    if match_ab:
                        text_for_runs_final = f"({match_ab.group(1)})\t" + match_ab.group(2).lstrip()
            
            # Pure headings (which might now be numbered) might not want the standard hanging indent.
            # However, if they are numbered, they will get the main numbered paragraph format.
            # If a numbered heading needs *different* indent, this needs another specific condition.
            # For now, numbered headings get the same indent as other numbered paragraphs.
            
            if para_style_to_apply != 'Normal': p.style = para_style_to_apply

            if current_content_substituted == "[FEE_TABLE_PLACEHOLDER]":
                # Special handling for fee table, does not use paragraph 'p'
                # Ensure 'p' is not left empty if it was created for the placeholder
                if p.text == "" and not p.runs: # Check if paragraph is truly empty
                    # A bit risky to remove, let's just not add text to it.
                    # Instead, just create new paragraphs for fee lines.
                    # This 'p' might be the last one from previous iteration, or newly created.
                    # If newly created, it will be empty.
                    pass # Let it be an empty paragraph if nothing else, or rely on next loop pass

                fee_lines = app_inputs['fee_table_content'].split('\n')
                for fee_idx, fee_line in enumerate(fee_lines):
                    # Create new paragraphs for each fee line
                    p_fee = doc.add_paragraph() 
                    p_fee.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT 
                    p_fee.paragraph_format.space_after = Pt(6); 
                    add_runs_from_text(p_fee, fee_line, app_inputs)
                if doc.paragraphs: doc.paragraphs[-1].paragraph_format.space_after = Pt(0)
            elif final_content_after_all_stripping or current_line_stripped_for_logic == "": 
                add_runs_from_text(p, text_for_runs_final, app_inputs)
            
            pf.space_after = Pt(0) 

        # --- Deactivate global states based on tags seen on THIS line (if they were end tags) ---
        if _line_had_end_tag_this_iteration:
            original_line_content_for_end_tag_check = line_raw.strip() # Check the original stripped line
            if original_line_content_for_end_tag_check.endswith("[end indiv]"): in_indiv_block = False
            if original_line_content_for_end_tag_check.endswith("[end corp]"): in_corp_block = False
            if active_track_block_type and original_line_content_for_end_tag_check.endswith(f"[end {active_track_block_type[1:-1]}]"):
                active_track_block_type = None


    if doc.paragraphs and doc.paragraphs[-1].paragraph_format.space_after == Pt(0):
        doc.paragraphs[-1].paragraph_format.space_after = Pt(6)

    doc_io = io.BytesIO(); doc.save(doc_io); doc_io.seek(0)
    st.success("Client Care Letter Generated!")
    st.download_button("Download Word Document", data=doc_io, file_name=f"Client_Care_Letter_{client_name_input.replace(' ', '_')}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

