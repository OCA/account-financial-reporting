## -*- coding: utf-8 -*-
<!DOCTYPE html SYSTEM
"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <style type="text/css">
            .overflow_ellipsis {
                text-overflow: ellipsis;
                overflow: hidden;
                white-space: nowrap;
            }

            .open_invoice_previous_line {
                font-style: italic;
            }

            .percent_line {
                font-style: italic;
            }

            .amount {
                text-align:right;
            }

            .classif_title {
                text-align:right;
            }

            .classif{
              width: ${700/len(ranges)}px;
            }
            .total{
               font-weight:bold;
            }
            ${css}
        </style>
    </head>

    <%!
    def amount(text):
        # replace by a non-breaking hyphen (it will not word-wrap between hyphen and numbers)
        return text.replace('-', '&#8209;')
    %>
    <body>
        <%setLang(user.lang)%>

        <div class="act_as_table data_table">
            <div class="act_as_row labels">
                <div class="act_as_cell">${_('Chart of Account')}</div>
                <div class="act_as_cell">${_('Fiscal Year')}</div>
                <div class="act_as_cell">
                    %if filter_form(data) == 'filter_date':
                        ${_('Dates Filter')}
                    %else:
                        ${_('Periods Filter')}
                    %endif
                </div>
                <div class="act_as_cell">${_('Clearance Date')}</div>
                <div class="act_as_cell">${_('Accounts Filter')}</div>
                <div class="act_as_cell">${_('Target Moves')}</div>

            </div>
            <div class="act_as_row">
                <div class="act_as_cell">${ chart_account.name }</div>
                <div class="act_as_cell">${ fiscalyear.name if fiscalyear else '-' }</div>
                <div class="act_as_cell">
                    ${_('From:')}
                    %if filter_form(data) == 'filter_date':
                        ${formatLang(start_date, date=True) if start_date else u'' }
                    %else:
                        ${start_period.name if start_period else u''}
                    %endif
                    ${_('To:')}
                    %if filter_form(data) == 'filter_date':
                        ${ formatLang(stop_date, date=True) if stop_date else u'' }
                    %else:
                        ${stop_period.name if stop_period else u'' }
                    %endif
                </div>
                <div class="act_as_cell">${ formatLang(date_until, date=True) }</div>
                <div class="act_as_cell">
                    %if partner_ids:
                        ${_('Custom Filter')}
                    %else:
                        ${ display_partner_account(data) }
                    %endif
                </div>
                <div class="act_as_cell">${ display_target_move(data) }</div>
            </div>
        </div>
        %for account in objects:
            %if aged_open_inv[account.id] and partners_order[account.id]:

                <div class="account_title bg" style="width: 1080px; margin-top: 20px; font-size: 12px;">${account.code} - ${account.name}</div>

                %for partner_name, p_id, p_ref, p_name in partners_order[account.id]:
                    <div class="act_as_table list_table" style="margin-top: 5px;">
                        <div class="act_as_caption account_title">
                            ${partner_name or _('No Partner')}
                        </div>
                        <div class="act_as_thead">
                            <div class="act_as_row labels">
                            ## date
                            <div class="act_as_cell first_column" style="width: 60px;">${_('Date')}</div>
                            ## move
                            <div class="act_as_cell" style="width: 100px;">${_('Entry')}</div>
                            ## journal
                            <div class="act_as_cell" style="width: 70px;">${_('Journal')}</div>
                            ## label
                            <div class="act_as_cell" style="width: 180px;">${_('Label')}</div>
                            ## reconcile
                            <div class="act_as_cell" style="width: 80px;">${_('Rec.')}</div>
                            ## maturity
                            <div class="act_as_cell" style="width: 60px;">${_('Due Date')}</div>
                            ## balance
                            <div class="act_as_cell amount" style="width: 80px;">${_('Amount')}</div>
                            ## Classifications
                            %for title in ranges_titles:
                                <div class="act_as_cell classif classif_title">${title}</div>
                            %endfor
                        </div>
                    </div>
                    <div class="act_as_tbody">
                        %for line in aged_open_inv[account.id][p_id].get('lines', []):
                            <div class="act_as_row lines ${line.get('is_from_previous_periods') and 'open_invoice_previous_line' or ''} ${line.get('is_clearance_line') and 'clearance_line' or ''}">
                                ## date
                                <div class="act_as_cell first_column">${formatLang(line.get('ldate') or '', date=True)}</div>
                                ## move
                                <div class="act_as_cell">${line.get('move_name') or ''}</div>
                                ## journal
                                <div class="act_as_cell">${line.get('jcode') or ''}</div>
                                ## label
                                <div class="act_as_cell">${line.get('lname')}</div>
                                ## reconcile
                                <div class="act_as_cell">${line.get('rec_name') or ''}</div>
                                ## maturity date
                                <div class="act_as_cell">${formatLang(line.get('date_maturity') or '', date=True)}</div>
                                ## balance
                                <div class="act_as_cell amount">${formatLang(line.get('balance') or 0.0) | amount }</div>
                                ## classifications
                                %for classif in ranges:
                                    <div class="act_as_cell classif amount">
                                        ${formatLang(line.get(classif) or 0.0) | amount }
                                    </div>
                                %endfor
                            </div>
                        %endfor  # end of the loop on lines
                        <div class="act_as_row labels">
                            <div class="act_as_cell total">${_('Total Partner')}</div>
                            <div class="act_as_cell"></div>
                            <div class="act_as_cell"></div>
                            <div class="act_as_cell"></div>
                            <div class="act_as_cell"></div>
                            <div class="act_as_cell"></div>
                            <div class="act_as_cell amount classif total">${formatLang(aged_open_inv[account.id][p_id]['balance']) | amount}</div>
                            %for classif in ranges:
                                <div class="act_as_cell amount classif total">${formatLang(aged_open_inv[account.id][p_id][classif]) | amount }</div>
                            %endfor
                        </div>
                    </div>
                %endfor  # end of the loop on partners
                <div class="act_as_row labels">
                    <div class="act_as_cell total account_title bg">${_('Total')}</div>
                    <div class="act_as_cell"></div>
                    <div class="act_as_cell"></div>
                    <div class="act_as_cell"></div>
                    <div class="act_as_cell"></div>
                    <div class="act_as_cell"></div>
                    <div class="act_as_cell amount classif total account_title bg">${formatLang(aged_open_inv[account.id]['balance']) | amount}</div>
                    %for classif in ranges:
                        <div class="act_as_cell amount classif total account_title bg">${formatLang(aged_open_inv[account.id][classif]) | amount }</div>
                    %endfor
                </div>
            %endif
        %endfor  # end of the loop on accounts
    </body>
</html>
