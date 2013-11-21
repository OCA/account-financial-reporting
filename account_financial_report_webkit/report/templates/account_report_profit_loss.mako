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
        </style>
    </head>
    <body>
        <%!

        def amount(text):
            return text.replace('-', '&#8209;')  # replace by a non-breaking hyphen (it will not word-wrap between hyphen and numbers)
        %>

        <%def name="format_amount(amount, display_option=None)">
            <%
            output = amount
            if display_option == 'normal':
                output = amount
            elif display_option == 'round':
                output = u"%.0f" % round(amount)
            elif display_option == 'kilo':
                if amount:
                    output = u"%.2fK" % (amount / 1000,)
            %>
            ${output}
        </%def>

        <%setLang(user.lang)%>

        <div class="act_as_table data_table">
            <div class="act_as_row labels">
                <div class="act_as_cell">${_('Chart of Account')}</div>
                <div class="act_as_cell">${_('Fiscal Year')}</div>
                <div class="act_as_cell">
                    %if filter_form(data) == 'filter_date':
                        ${_('Dates')}
                    %else:
                        ${_('Periods')}
                    %endif
                </div>
                <div class="act_as_cell">${_('Displayed Accounts')}</div>
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
                <div class="act_as_cell">${ _('Yes') if initial_balance else _('No') }</div>
            </div>
        </div>

        %for index, params in enumerate(comp_params):
            <div class="act_as_table data_table">
                <div class="act_as_row">
                    <div class="act_as_cell">${_('Comparison %s') % (index + 1,)} (${"C%s" % (index + 1,)})</div>
                    <div class="act_as_cell">
                        %if params['comparison_filter'] == 'filter_date':
                            ${_('Dates : ')}&nbsp;${formatLang(params['start'], date=True) }&nbsp;-&nbsp;${formatLang(params['stop'], date=True) }
                        %elif params['comparison_filter'] == 'filter_period':
                            ${_('Periods : ')}&nbsp;${params['start'].name}&nbsp;-&nbsp;${params['stop'].name}
                        %else:
                            ${_('Fiscal Year : ')}&nbsp;${params['fiscalyear'].name}
                        %endif
                    </div>
                    <div class="act_as_cell">${_('Initial Balance:')} ${ _('Yes') if params['initial_balance'] else _('No') }</div>
                </div>
            </div>
        %endfor

        <div class="act_as_table list_table" style="margin-top: 20px;">

            <div class="act_as_thead">
                <div class="act_as_row labels">
                    ## account name
                    <div class="act_as_cell" style="width: 80px;">${_('Account')}</div>
                    %if comparison_mode == 'no_comparison':
                        %if initial_balance:
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
                %for account_at in objects:
                    <%
                    current_account = account_at['current']
                    level = current_account['level']
                    %>
                    %if level_print(data, level):  ## how to manage levels?
                    <%
                        styles = []
                        if level_bold(data, level):
                            styles.append('font-weight: bold;')
                        else:
                            styles.append('font-weight: normal;')

                        if level_italic(data, level):
                            styles.append('font-style: italic;')
                        else:
                            styles.append('font-style: normal;')

                        if level_underline(data, level):
                            styles.append('text-decoration: underline;')
                        else:
                            styles.append('text-decoration: none;')

                        if level_uppercase(data, level):
                            styles.append('text-transform: uppercase;')
                        else:
                            styles.append('font-decoration: none;')

                        styles.append("font-size: %spx;" % (level_size(data, level),))

                    %>
                        <div class="act_as_row lines ${"account_level_%s" % (current_account['level'])}" styles="${' '.join(styles)}">
                            ## account name
                            <div class="act_as_cell" style="padding-left: ${current_account.get('level', 0) * 5}px; ${' '.join(styles)}">${current_account['name']}</div>
                            %if comparison_mode == 'no_comparison':
                                %if initial_balance:
                                    ## opening balance
                                    <div class="act_as_cell amount" style="${' '.join(styles)}">${format_amount(current_account['init_balance'], numbers_display(data)) | amount}</div>
                                %endif
                                ## debit
                                <div class="act_as_cell amount" style="${' '.join(styles)}">${format_amount(current_account['debit'], numbers_display(data)) | amount}</div>
                                ## credit
                                <div class="act_as_cell amount" style="${' '.join(styles)}">${format_amount(current_account['credit'] * -1, numbers_display(data)) if current_account['credit'] else 0.0 | amount}</div>
                            %endif
                            ## balance
                            <div class="act_as_cell amount" style="${' '.join(styles)}">${format_amount(current_account['balance'], numbers_display(data)) | amount}</div>

                            %if comparison_mode in ('single', 'multiple'):
                                %for comp_account in account_at['comparisons']:
                                    <div class="act_as_cell amount" style="${' '.join(styles)}">${format_amount(comp_account['balance'], numbers_display(data)) | amount}</div>
                                    %if comparison_mode == 'single':  ## no diff in multiple comparisons because it shows too data
                                        <div class="act_as_cell amount" style="${' '.join(styles)}">${format_amount(comp_account['diff'], numbers_display(data)) | amount}</div>
                                        <div class="act_as_cell amount" style="${' '.join(styles)}">
                                        %if comp_account['percent_diff'] is False:
                                         ${ '-' }
                                        %else:
                                           ${comp_account['percent_diff'] | amount} &#37;
                                        %endif
                                        </div>
                                    %endif
                                %endfor
                            %endif
                        </div>
                    %endif
                %endfor
            </div>
        </div>
    </body>
</html>
