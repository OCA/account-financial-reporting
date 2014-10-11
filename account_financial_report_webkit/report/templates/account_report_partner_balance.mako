## -*- coding: utf-8 -*-
<!DOCTYPE html SYSTEM "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <style type="text/css">
            ${css}

            .list_table .act_as_row {
                margin-top: 10px;
                margin-bottom: 10px;
                font-size:10px;
            }

            .account_line {
                font-weight: bold;
                font-size: 15px;
                background-color:#F0F0F0;
            }

            .account_line .act_as_cell {
                height: 30px;
                vertical-align: bottom;
            }

        </style>
    </head>
    <body>
        <%!
        def amount(text):
            return text.replace('-', '&#8209;')  # replace by a non-breaking hyphen (it will not word-wrap between hyphen and numbers)

        def display_line(all_comparison_lines):
            return any([line.get('balance') for line in all_comparison_lines])
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
                <div class="act_as_cell">${_('Partners Filter')}</div>
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
                <div class="act_as_cell">${display_partner_account(data)}</div>
                <div class="act_as_cell">${ display_target_move(data) }</div>
                <div class="act_as_cell">${ initial_balance_text[initial_balance_mode] }</div>
            </div>
        </div>

        %for index, params in enumerate(comp_params):
            <div class="act_as_table data_table">
                <div class="act_as_row">
                    <div class="act_as_cell">${_('Comparison %s') % (index + 1,)} (${"C%s" % (index + 1,)})</div>
                    <div class="act_as_cell">
                        %if params['comparison_filter'] == 'filter_date':
                            ${_('Dates Filter:')}&nbsp;${formatLang(params['start'], date=True) }&nbsp;-&nbsp;${formatLang(params['stop'], date=True) }
                        %elif params['comparison_filter'] == 'filter_period':
                            ${_('Periods Filter:')}&nbsp;${params['start'].name}&nbsp;-&nbsp;${params['stop'].name}
                        %else:
                            ${_('Fiscal Year :')}&nbsp;${params['fiscalyear'].name}
                        %endif
                    </div>
                    <div class="act_as_cell">${ _('Initial Balance:')} ${ initial_balance_text[params['initial_balance_mode']] }</div>
                </div>
            </div>
        %endfor

        %for current_account in objects:
            <%
            partners_order = partners_order_accounts[current_account.id]

            # do not display accounts without partners
            if not partners_order:
                continue

            comparisons = comparisons_accounts[current_account.id]

            # in multiple columns mode, we do not want to print accounts without any rows
            if comparison_mode in ('single', 'multiple'):
                all_comparison_lines = [comp['partners_amounts'][partner_id[1]]
                                      for partner_id in partners_order 
                                      for comp in comparisons]
                if not display_line(all_comparison_lines):
                    continue

            current_partner_amounts = partners_amounts_accounts[current_account.id]

            total_initial_balance = 0.0
            total_debit = 0.0
            total_credit = 0.0
            total_balance = 0.0
            if comparison_mode in ('single', 'multiple'):
                comparison_total = {}
                for i, comp in enumerate(comparisons):
                    comparison_total[i] = {'balance': 0.0}
            %>

            <div class="account_title bg" style="margin-top: 20px; font-size: 12px; width: 690px;">${current_account.code} - ${current_account.name}</div>

            <div class="act_as_table list_table">

                <div class="act_as_thead">
                    <div class="act_as_row labels">
                        ## account name
                        <div class="act_as_cell" style="width: 80px;">${_('Account / Partner Name')}</div>
                        ## code
                        <div class="act_as_cell first_column" style="width: 20px;">${_('Code / Ref')}</div>
                        %if comparison_mode == 'no_comparison':
                            %if initial_balance_mode:
                                ## initial balance
                                <div class="act_as_cell amount" style="width: 30px;">${_('Initial Balance')}</div>
                            %endif
                            ## debit
                            <div class="act_as_cell amount" style="width: 30px;">${_('Debit')}</div>
                            ## credit
                            <div class="act_as_cell amount" style="width: 30px;">${_('Credit')}</div>
                        %endif
                        ## balance
                        <div class="act_as_cell amount" style="width: 30px;">
                        %if comparison_mode == 'no_comparison' or not fiscalyear:
                            ${_('Balance')}
                        %else:
                            ${_('Balance %s') % (fiscalyear.name,)}
                        %endif
                        </div>
                        %if comparison_mode in ('single', 'multiple'):
                            %for index in range(nb_comparison):
                                <div class="act_as_cell amount" style="width: 30px;">
                                    %if comp_params[index]['comparison_filter'] == 'filter_year' and comp_params[index].get('fiscalyear', False):
                                        ${_('Balance %s') % (comp_params[index]['fiscalyear'].name,)}
                                    %else:
                                        ${_('Balance C%s') % (index + 1,)}
                                    %endif
                                </div>
                                %if comparison_mode == 'single':  ## no diff in multiple comparisons because it shows too data
                                    <div class="act_as_cell amount" style="width: 30px;">${_('Difference')}</div>
                                    <div class="act_as_cell amount" style="width: 30px;">${_('% Difference')}</div>
                                %endif
                            %endfor
                        %endif
                    </div>
                </div>

                <div class="act_as_tbody">

                    %for (partner_code_name, partner_id, partner_ref, partner_name) in partners_order:
                        <%
                        partner = current_partner_amounts.get(partner_id, {})

                        # in single mode, we have to display all the partners
                        # even if their balance is 0.0 because the initial balance
                        # should match with the previous year closings

                        # in multiple columns mode, we do not want to print partners
                        # which have a balance at 0.0 in each comparison column
                        if comparison_mode in ('single', 'multiple'):
                            all_comparison_lines = [comp['partners_amounts'][partner_id]
                                                    for comp in comparisons 
                                                    if comp['partners_amounts'].get(partner_id)]
                            if not display_line(all_comparison_lines):
                                continue

                        total_initial_balance += partner.get('init_balance', 0.0)
                        total_debit += partner.get('debit', 0.0)
                        total_credit += partner.get('credit', 0.0)
                        total_balance += partner.get('balance', 0.0)
                        %>
                        <div class="act_as_row lines">
                            <div class="act_as_cell">${partner_name if partner_name else _('Unallocated') }</div>
                            <div class="act_as_cell first_column">${partner_ref if partner_ref else ''}</div>
                            %if comparison_mode == 'no_comparison':
                                %if initial_balance_mode:
                                    <div class="act_as_cell amount">${formatLang(partner.get('init_balance', 0.0)) | amount}</div>
                                %endif
                                <div class="act_as_cell amount">${formatLang(partner.get('debit', 0.0)) | amount}</div>
                                <div class="act_as_cell amount">${formatLang(partner.get('credit', 0.0)) | amount}</div>
                            %endif
                            <div class="act_as_cell amount">${formatLang(partner['balance'] if partner else 0.0) | amount}</div>

                            %if comparison_mode in ('single', 'multiple'):
                                %for i, comp in enumerate(comparisons):
                                    <%
                                    comp_partners = comp['partners_amounts']
                                    balance = diff = percent_diff = 0
                                    if comp_partners.get(partner_id):
                                        balance = comp_partners[partner_id]['balance']
                                        diff = comp_partners[partner_id]['diff']
                                        percent_diff = comp_partners[partner_id]['percent_diff']
                                        comparison_total[i]['balance'] += balance
                                    %>
                                    <div class="act_as_cell amount">${formatLang(balance) | amount}</div>
                                    %if comparison_mode == 'single':  ## no diff in multiple comparisons because it shows too data
                                        <div class="act_as_cell amount">${formatLang(diff) | amount}</div>
                                        <div class="act_as_cell amount">
                                        %if percent_diff is False:
                                         ${ '-' }
                                        %else:
                                           ${int(round(percent_diff)) | amount} &#37;
                                        %endif
                                        </div>
                                    %endif
                                %endfor
                            %endif
                        </div>
                    %endfor

                </div>
                <div class="act_as_tfoot" style="margin-top:5px;">
                    <div class="act_as_row labels" style="font-weight: bold; font-size: 11x;">
                        ## account name
                        <div class="act_as_cell">${current_account.name}</div>
                        ## code
                        <div class="act_as_cell first_column">${current_account.code}</div>
                        %if comparison_mode == 'no_comparison':
                            %if initial_balance_mode:
                                ## opening balance
                                <div class="act_as_cell amount">${formatLang(total_initial_balance) | amount}</div>
                            %endif
                            ## debit
                            <div class="act_as_cell amount">${formatLang(total_debit) | amount}</div>
                            ## credit
                            <div class="act_as_cell amount">${formatLang(total_credit and total_credit * -1 or 0.0) | amount}</div>
                        %endif
                        ## balance
                        <div class="act_as_cell amount">${formatLang(total_balance) | amount}</div>

                        %if comparison_mode in ('single', 'multiple'):
                            %for i, comp in enumerate(comparisons):
                                <%
                                comp_account = comp['account']
                                diffs = compute_diff(total_balance, comparison_total[i]['balance'])
                                %>
                                <div class="act_as_cell amount">${formatLang(comparison_total[i]['balance']) | amount}</div>
                                %if comparison_mode == 'single':  ## no diff in multiple comparisons because it shows too data
                                    <div class="act_as_cell amount">${formatLang(diffs['diff']) | amount}</div>
                                    <div class="act_as_cell amount">
                                    %if diffs['percent_diff'] is False:
                                     ${ '-' }
                                    %else:
                                       ${int(round(diffs['percent_diff'])) | amount} &#37;
                                    %endif
                                    </div>
                                %endif
                            %endfor
                        %endif
                    </div>
                </div>
            </div>

        %endfor

    </body>
</html>
