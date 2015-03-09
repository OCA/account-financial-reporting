## -*- coding: utf-8 -*-
<!DOCTYPE html SYSTEM "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <style type="text/css">
            .overflow_ellipsis {
                text-overflow: ellipsis;
                overflow: hidden;
                white-space: nowrap;
            }

            ${css}
        </style>
    </head>
    <body>
        <%!
        def amount(text):
            return text.replace('-', '&#8209;')  # replace by a non-breaking hyphen (it will not word-wrap between hyphen and numbers)
        %>

        <%setLang(user.lang)%>

        <%
        initial_balance_text = {'initial_balance': _('Computed'), 'opening_balance': _('Opening Entries'), False: _('No')}
        %>

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
                <div class="act_as_cell">${_('Accounts Filter')}</div>
                <div class="act_as_cell">${_('Target Moves')}</div>
                <div class="act_as_cell">${_('Initial Balance')}</div>
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
                <div class="act_as_cell">
                    %if partner_ids:
                        ${_('Custom Filter')}
                    %else:
                        ${ display_partner_account(data) }
                    %endif
                </div>
                <div class="act_as_cell">${ display_target_move(data) }</div>
                <div class="act_as_cell">${ initial_balance_text[initial_balance_mode] }</div>
            </div>
        </div>

        %for account in objects:
            %if account.ledger_lines or account.init_balance:
                <%
                if not account.partners_order:
                    continue
                %>

                <div class="account_title bg" style="width: 1080px; margin-top: 20px; font-size: 12px;">${account.code} - ${account.name}</div>

                %for partner_name, p_id, p_ref, p_name in account.partners_order:
                <%
                  total_debit = 0.0
                  total_credit = 0.0
                  cumul_balance = 0.0
                  cumul_balance_curr = 0.0

                  part_cumul_balance = 0.0
                  part_cumul_balance_curr = 0.0
                %>
                <div class="act_as_table list_table" style="margin-top: 5px;">
                    <div class="act_as_caption account_title">
                        ${partner_name or _('No Partner')}
                    </div>
                    <div class="act_as_thead">
                        <div class="act_as_row labels">
                            ## date
                            <div class="act_as_cell first_column" style="width: 50px;">${_('Date')}</div>
                            ## period
                            <div class="act_as_cell" style="width: 70px;">${_('Period')}</div>
                            ## move
                            <div class="act_as_cell" style="width: 100px;">${_('Entry')}</div>
                            ## journal
                            <div class="act_as_cell" style="width: 70px;">${_('Journal')}</div>
                            ## partner
                            <div class="act_as_cell" style="width: 100px;">${_('Partner')}</div>
                            ## move reference
                            <div class="act_as_cell" style="width: 60px;">${_('Reference')}</div>
                            ## label
                            <div class="act_as_cell" style="width: 280px;">${_('Label')}</div>
                            ## reconcile
                            <div class="act_as_cell" style="width: 80px;">${_('Rec.')}</div>
                            ## debit
                            <div class="act_as_cell amount" style="width: 80px;">${_('Debit')}</div>
                            ## credit
                            <div class="act_as_cell amount" style="width: 80px;">${_('Credit')}</div>
                            ## balance cumulated
                            <div class="act_as_cell amount" style="width: 80px;">${_('Cumul. Bal.')}</div>
                            %if amount_currency(data):
                                ## currency balance
                                <div class="act_as_cell amount sep_left" style="width: 80px;">${_('Curr. Balance')}</div>
                                ## curency code
                                <div class="act_as_cell amount" style="width: 30px; text-align: right;">${_('Curr.')}</div>
                            %endif
                        </div>
                    </div>
                    <div class="act_as_tbody">
                        <%
                        total_debit = account.init_balance.get(p_id, {}).get('debit') or 0.0
                        total_credit = account.init_balance.get(p_id, {}).get('credit') or 0.0
                        %>
                          %if initial_balance_mode and (total_debit or total_credit):
                            <%
                              part_cumul_balance = account.init_balance.get(p_id, {}).get('init_balance') or 0.0
                              part_cumul_balance_curr = account.init_balance.get(p_id, {}).get('init_balance_currency') or 0.0
                              balance_forward_currency = account.init_balance.get(p_id, {}).get('currency_name') or ''

                              cumul_balance += part_cumul_balance
                              cumul_balance_curr += part_cumul_balance_curr
                            %>
                            <div class="act_as_row initial_balance">
                              ## date
                              <div class="act_as_cell first_column"></div>
                              ## period
                              <div class="act_as_cell"></div>
                              ## move
                              <div class="act_as_cell"></div>
                              ## journal
                              <div class="act_as_cell"></div>
                              ## partner
                              <div class="act_as_cell"></div>
                              ## move reference
                              <div class="act_as_cell"></div>
                              ## label
                              <div class="act_as_cell" >${_('Initial Balance')}</div>
                              ## reconcile
                              <div class="act_as_cell"></div>
                              ## debit
                              <div class="act_as_cell amount">${formatLang(total_debit) | amount }</div>
                              ## credit
                              <div class="act_as_cell amount">${formatLang(total_credit) | amount }</div>
                              ## balance cumulated
                              <div class="act_as_cell amount" style="padding-right: 1px;">${formatLang(part_cumul_balance) | amount }</div>
                             %if amount_currency(data):
                                  ## currency balance
                                  <div class="act_as_cell sep_left amount">${formatLang(part_cumul_balance_curr) | amount }</div>
                                  ## curency code
                                  <div class="act_as_cell">${balance_forward_currency}</div>
                             %endif

                          </div>
                          %endif

                        %for line in account.ledger_lines.get(p_id, []):
                          <%
                          total_debit += line.get('debit') or 0.0
                          total_credit += line.get('credit') or 0.0

                          label_elements = [line.get('lname') or '']
                          if line.get('invoice_number'):
                            label_elements.append("(%s)" % (line['invoice_number'],))
                          label = ' '.join(label_elements)
                          %>
                            <div class="act_as_row lines">
                              ## date
                              <div class="act_as_cell first_column">${formatLang(line.get('ldate') or '', date=True)}</div>
                              ## period
                              <div class="act_as_cell">${line.get('period_code') or ''}</div>
                              ## move
                              <div class="act_as_cell">${line.get('move_name') or ''}</div>
                              ## journal
                              <div class="act_as_cell">${line.get('jcode') or ''}</div>
                              ## partner
                              <div class="act_as_cell overflow_ellipsis">${line.get('partner_name') or ''}</div>
                              ## move reference
                              <div class="act_as_cell">${line.get('lref') or ''}</div>
                              ## label
                              <div class="act_as_cell">${label}</div>
                              ## reconcile
                              <div class="act_as_cell">${line.get('rec_name') or ''}</div>
                              ## debit
                              <div class="act_as_cell amount">${formatLang(line.get('debit') or 0.0) | amount }</div>
                              ## credit
                              <div class="act_as_cell amount">${formatLang(line.get('credit') or 0.0) | amount }</div>
                              ## balance cumulated
                              <% cumul_balance += line.get('balance') or 0.0 %>
                              <div class="act_as_cell amount" style="padding-right: 1px;">${formatLang(cumul_balance) | amount }</div>
                              %if amount_currency(data):
                                  ## currency balance
                                  <div class="act_as_cell sep_left amount">${formatLang(line.get('amount_currency') or 0.0) | amount }</div>
                                  ## curency code
                                  <div class="act_as_cell" style="text-align: right; ">${line.get('currency_code') or ''}</div>
                              %endif
                          </div>
                        %endfor
                        <div class="act_as_row lines labels">
                          ## date
                          <div class="act_as_cell first_column"></div>
                          ## period
                          <div class="act_as_cell"></div>
                          ## move
                          <div class="act_as_cell"></div>
                          ## journal
                          <div class="act_as_cell"></div>
                          ## partner
                          <div class="act_as_cell"></div>
                          ## move reference
                          <div class="act_as_cell"></div>
                          ## label
                          <div class="act_as_cell">${_('Cumulated Balance on Partner')}</div>
                          ## reconcile
                          <div class="act_as_cell"></div>
                          ## debit
                          <div class="act_as_cell amount">${formatLang(total_debit) | amount }</div>
                          ## credit
                          <div class="act_as_cell amount">${formatLang(total_credit) | amount }</div>
                          ## balance cumulated
                          <div class="act_as_cell amount" style="padding-right: 1px;">${formatLang(cumul_balance) | amount }</div>
                          %if amount_currency(data):
                              ## currency balance
                              %if account.currency_id:
                                  <div class="act_as_cell amount sep_left">${formatLang(cumul_balance_curr) | amount }</div>
                              %else:
                                  <div class="act_as_cell sep_left amount">${ u'-' }</div>
                              %endif
                              ## currency code
                              <div class="act_as_cell" style="text-align: right; padding-right: 1px;">${ account.currency_id.name if account.currency_id else u'' }</div>
                          %endif
                      </div>
                    </div>
                </div>
                %endfor
                </div>
            %endif
        %endfor
    </body>
</html>
