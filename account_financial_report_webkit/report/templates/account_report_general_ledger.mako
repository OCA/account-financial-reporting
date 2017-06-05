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

        %if amount_currency(data):
        <div class="act_as_table data_table" style="width: 1205px;">
        %else:
        <div class="act_as_table data_table" style="width: 1100px;">
        %endif
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
                    %if accounts(data):
                        ${', '.join([account.code for account in accounts(data)])}
                    %else:
                        ${_('All')}
                    %endif

                </div>
                <div class="act_as_cell">${ display_target_move(data) }</div>
                <div class="act_as_cell">${ initial_balance_text[initial_balance_mode] }</div>
            </div>
        </div>

        <!-- we use div with css instead of table for tabular data because div do not cut rows at half at page breaks -->
        %for account in objects:
        <%
          display_initial_balance = init_balance[account.id] and (init_balance[account.id].get('debit') != 0.0 or init_balance[account.id].get('credit', 0.0) != 0.0)
          display_ledger_lines = ledger_lines[account.id]
        %>
          %if display_account_raw(data) == 'all' or (display_ledger_lines or display_initial_balance):
              <%
              cumul_debit = 0.0
              cumul_credit = 0.0
              cumul_balance =  0.0
              cumul_balance_curr = 0.0
              %>
            <div class="act_as_table list_table" style="margin-top: 10px;">

                <div class="act_as_caption account_title">
                    ${account.code} - ${account.name}
                </div>
                <div class="act_as_thead">
                    <div class="act_as_row labels">
                        ## date
                        <div class="act_as_cell first_column" style="width: 50px;">${_('Date')}</div>
                        ## period
                        <div class="act_as_cell" style="width: 50px;">${_('Period')}</div>
                        ## move
                        <div class="act_as_cell" style="width: 100px;">${_('Entry')}</div>
                        ## journal
                        <div class="act_as_cell" style="width: 70px;">${_('Journal')}</div>
                        ## account code
                        <div class="act_as_cell" style="width: 65px;">${_('Account')}</div>
                        ## partner
                        <div class="act_as_cell" style="width: 140px;">${_('Partner')}</div>
                        ## move reference
                        <div class="act_as_cell" style="width: 140px;">${_('Reference')}</div>
                        ## label
                        <div class="act_as_cell" style="width: 160px;">${_('Label')}</div>
                        ## counterpart
                        <div class="act_as_cell" style="width: 100px;">${_('Counter part')}</div>
                        ## debit
                        <div class="act_as_cell amount" style="width: 75px;">${_('Debit')}</div>
                        ## credit
                        <div class="act_as_cell amount" style="width: 75px;">${_('Credit')}</div>
                        ## balance cumulated
                        <div class="act_as_cell amount" style="width: 75px;">${_('Cumul. Bal.')}</div>
                        %if amount_currency(data):
                            ## currency balance
                            <div class="act_as_cell amount sep_left" style="width: 75px;">${_('Curr. Balance')}</div>
                            ## curency code
                            <div class="act_as_cell amount" style="width: 30px; text-align: right;">${_('Curr.')}</div>
                        %endif
                    </div>
                </div>

                %if  account.id not in clients_dict:
                  <div class="act_as_tbody">
                        %if display_initial_balance:
                          <%
                          cumul_debit = init_balance[account.id].get('debit') or 0.0
                          cumul_credit = init_balance[account.id].get('credit') or 0.0
                          cumul_balance = init_balance[account.id].get('init_balance') or 0.0
                          cumul_balance_curr = init_balance[account.id].get('init_balance_currency') or 0.0
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
                            ## account code
                            <div class="act_as_cell"></div>
                            ## partner
                            <div class="act_as_cell"></div>
                            ## move reference
                            <div class="act_as_cell"></div>
                            ## label
                            <div class="act_as_cell">${_('Initial Balance')}</div>
                            ## counterpart
                            <div class="act_as_cell"></div>
                            ## debit
                            <div class="act_as_cell amount">${formatLang(init_balance[account.id].get('debit')) | amount}</div>
                            ## credit
                            <div class="act_as_cell amount">${formatLang(init_balance[account.id].get('credit')) | amount}</div>
                            ## balance cumulated
                            <div class="act_as_cell amount" style="padding-right: 1px;">${formatLang(cumul_balance) | amount }</div>
                           %if amount_currency(data):
                                ## currency balance
                                <div class="act_as_cell amount sep_left">${formatLang(cumul_balance_curr) | amount }</div>
                                ## curency code
                                <div class="act_as_cell amount"></div>
                           %endif

                          </div>
                        %endif
                        %for line in ledger_lines[account.id]:
                          <%
                          cumul_debit += line.get('debit') or 0.0
                          cumul_credit += line.get('credit') or 0.0
                          cumul_balance_curr += line.get('amount_currency') or 0.0
                          cumul_balance += line.get('balance') or 0.0
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
                            ## account code
                            <div class="act_as_cell">${account.code}</div>
                            ## partner
                            <div class="act_as_cell overflow_ellipsis">${line.get('partner_name') or ''}</div>
                            ## move reference
                            <div class="act_as_cell">${line.get('lref') or ''}</div>
                            ## label
                            <div class="act_as_cell">${label}</div>
                            ## counterpart
                            <div class="act_as_cell">${line.get('counterparts') or ''}</div>
                            ## debit
                            <div class="act_as_cell amount">${ formatLang(line.get('debit', 0.0)) | amount }</div>
                            ## credit
                            <div class="act_as_cell amount">${ formatLang(line.get('credit', 0.0)) | amount }</div>
                            ## balance cumulated
                            <div class="act_as_cell amount" style="padding-right: 1px;">${ formatLang(cumul_balance) | amount }</div>
                            %if amount_currency(data):
                                ## currency balance
                                <div class="act_as_cell amount sep_left">${formatLang(line.get('amount_currency') or 0.0)  | amount }</div>
                                ## curency code
                                <div class="act_as_cell amount" style="text-align: right;">${line.get('currency_code') or ''}</div>
                            %endif
                        </div>
                        %endfor
                  </div>
                %endif ## finish if initial for report

                ## Init group by partner
                %if  account.id in clients_dict:
                  <div class="act_as_tbody">
                        %if display_initial_balance:
                          <%
                          cumul_debit = init_balance[account.id].get('debit') or 0.0
                          cumul_credit = init_balance[account.id].get('credit') or 0.0
                          cumul_balance = init_balance[account.id].get('init_balance') or 0.0
                          cumul_balance_curr = init_balance[account.id].get('init_balance_currency') or 0.0
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
                            ## account code
                            <div class="act_as_cell"></div>
                            ## partner
                            <div class="act_as_cell"></div>
                            ## move reference
                            <div class="act_as_cell"></div>
                            ## label
                            <div class="act_as_cell">${_('Initial Balance')}</div>
                            ## counterpart
                            <div class="act_as_cell"></div>
                            ## debit
                            <div class="act_as_cell amount">${formatLang(init_balance[account.id].get('debit')) | amount}</div>
                            ## credit
                            <div class="act_as_cell amount">${formatLang(init_balance[account.id].get('credit')) | amount}</div>
                            ## balance cumulated
                            <div class="act_as_cell amount" style="padding-right: 1px;">${formatLang(cumul_balance) | amount }</div>
                           %if amount_currency(data):
                                ## currency balance
                                <div class="act_as_cell amount sep_left">${formatLang(cumul_balance_curr) | amount }</div>
                                ## curency code
                                <div class="act_as_cell amount"></div>
                           %endif

                          </div>
                        %endif

                        <%
                          old_client_name = False
                          client_cumul_debit = 0.0
                          client_cumul_credit = 0.0
                          client_cumul_balance_curr = 0.0
                          client_cumul_balance = 0.0
                          balance_line = 0.0
                          label_elements = []
                          label = ' '.join(label_elements)
                        %>
                        %for name_line in clients_dict[account.id]:

                          %for client_line in clients_dict[account.id][name_line]:

                              %if old_client_name != False and old_client_name != client_line.get('partner_name'):
                                ## Client sumatory
                                <div class="act_as_row labels">
                                    ## client name
                                    <div class="act_as_cell first_column"></div>
                                    ## period
                                    <div class="act_as_cell"></div>
                                    ## move
                                    <div class="act_as_cell"></div>
                                    ## journal
                                    <div class="act_as_cell"></div>
                                    ## account code
                                    <div class="act_as_cell"></div>
                                    ## partner
                                    <div class="act_as_cell overflow_ellipsis"></div>
                                    ## move reference
                                    <div class="act_as_cell"></div>
                                    ## label
                                    <div class="act_as_cell"></div>
                                    ## counterpart
                                    <div class="act_as_cell"></div>
                                    ## debit
                                    <div class="act_as_cell amount">${formatLang(client_cumul_debit)}</div>
                                    ## credit
                                    <div class="act_as_cell amount">${formatLang(client_cumul_credit)}</div>
                                    ## balance cumulated
                                    <div class="act_as_cell amount" style="padding-right: 1px;">${formatLang(client_cumul_balance)}</div>
                                </div>
                                ## End Client sumatory
                                <%
                                  old_client_name = False
                                  client_cumul_debit = 0.0
                                  client_cumul_credit = 0.0
                                  client_cumul_balance_curr = 0.0
                                  client_cumul_balance = 0.0
                                  balance_line = 0.0
                                %>
                              %endif ## End if client sumatory

                            %if old_client_name != client_line.get('partner_name'):
                              ## Client header
                              <div class="act_as_row labels">
                                  ## client name
                                  <div class="act_as_cell first_column"></div>
                                  ## period
                                  <div class="act_as_cell"></div>
                                  ## move
                                  <div class="act_as_cell" style="font-weight: bold;">${client_line.get('partner_name')}</div>
                                  ## journal
                                  <div class="act_as_cell"></div>
                                  ## account code
                                  <div class="act_as_cell"></div>
                                  ## partner
                                  <div class="act_as_cell overflow_ellipsis"></div>
                                  ## move reference
                                  <div class="act_as_cell"></div>
                                  ## label
                                  <div class="act_as_cell"></div>
                                  ## counterpart
                                  <div class="act_as_cell"></div>
                                  ## debit
                                  <div class="act_as_cell amount"></div>
                                  ## credit
                                  <div class="act_as_cell amount"></div>
                                  ## balance cumulated
                                  <div class="act_as_cell amount" style="padding-right: 1px;"></div>
                              </div>
                              ## End Client header
                            %endif ## End if client name
                            <%
                              balance_line = balance_line + client_line.get('debit', 0.0) - client_line.get('credit', 0.0)
                            %>
                            <div class="act_as_row lines">
                                ## date
                                <div class="act_as_cell first_column">${formatLang(client_line.get('ldate') or '', date=True)}</div>
                                ## period
                                <div class="act_as_cell">${client_line.get('period_code') or ''}</div>
                                ## move
                                <div class="act_as_cell">${client_line.get('move_name') or ''}</div>
                                ## journal
                                <div class="act_as_cell">${client_line.get('jcode') or ''}</div>
                                ## account code
                                <div class="act_as_cell">${account.code}</div>
                                ## partner
                                <div class="act_as_cell overflow_ellipsis">${client_line.get('partner_name') or ''}</div>
                                ## move reference
                                <div class="act_as_cell">${client_line.get('lref') or ''}</div>
                                ## label
                                <div class="act_as_cell">${label}</div>
                                ## counterpart
                                <div class="act_as_cell">${client_line.get('counterparts') or ''}</div>
                                ## debit
                                <div class="act_as_cell amount">${ formatLang(client_line.get('debit', 0.0)) | amount }</div>
                                ## credit
                                <div class="act_as_cell amount">${ formatLang(client_line.get('credit', 0.0)) | amount }</div>
                                ## balance cumulated
                                <div class="act_as_cell amount" style="padding-right: 1px;">${formatLang(balance_line)}</div>
                                %if amount_currency(data):
                                    ## currency balance
                                    <div class="act_as_cell amount sep_left">${formatLang(client_line.get('amount_currency') or 0.0)  | amount }</div>
                                    ## curency code
                                    <div class="act_as_cell amount" style="text-align: right;">${client_line.get('currency_code') or ''}</div>
                                %endif
                            </div>

                            <%
                              old_client_name = client_line.get('partner_name')
                              client_cumul_debit += client_line.get('debit')
                              client_cumul_credit += client_line.get('credit')
                              client_cumul_balance_curr += client_line.get('amount_currency')
                              client_cumul_balance += client_line.get('balance')
                              label_elements = [client_line.get('lname') or '']
                            %>
                          %endfor ## End for de cliente line
                        %endfor ## en for de account
                  </div> ## End client group by
                %endif ## End client group by

                <div class="act_as_table list_table">
                    <div class="act_as_row labels" style="font-weight: bold;">
                        ## date
                        <div class="act_as_cell first_column" style="width: 615px;">${account.code} - ${account.name}</div>
                        <div class="act_as_cell" style="width: 260px;">${_("Cumulated Balance on Account")}</div>
                        ## debit
                        <div class="act_as_cell amount" style="width: 75px;">${ formatLang(cumul_debit) | amount }</div>
                        ## credit
                        <div class="act_as_cell amount" style="width: 75px;">${ formatLang(cumul_credit) | amount }</div>
                        ## balance cumulated
                        <div class="act_as_cell amount" style="width: 75px; padding-right: 1px;">${ formatLang(cumul_balance) | amount }</div>
                        %if amount_currency(data):
                            %if account.currency_id:
                                ## currency balance
                                <div class="act_as_cell amount sep_left" style="width: 75px;">${formatLang(cumul_balance_curr) | amount }</div>
                            %else:
                                <div class="act_as_cell amount sep_left" style="width: 75px;">-</div>
                            %endif
                            ## curency code
                            <div class="act_as_cell amount" style="width: 30px; text-align: right;"></div>
                        %endif
                    </div>
                </div>
            </div>
          %endif
        %endfor
    </body>
</html>
