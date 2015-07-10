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
        %for acc in objects:
          %if agged_lines_accounts[acc.id]:
          <div class="account_title bg" style="width: 1080px; margin-top: 20px; font-size: 12px;">${acc.code} - ${acc.name}</div>



                <div class="act_as_table list_table" style="margin-top: 5px;">
                  <div class="act_as_thead">
                    <div class="act_as_row labels">
                      ## partner
                      <div class="act_as_cell first_column" style="width: 60px;">${_('Partner')}</div>
                      ## code
                      <div class="act_as_cell" style="width: 70px;">${_('Code')}</div>
                      ## balance
                      <div class="act_as_cell classif_title" style="width: 70px;">${_('Balance')}</div>
                      ## Classifications
                      %for title in ranges_titles:
                        <div class="act_as_cell classif classif_title">${title}</div>
                      %endfor
                    </div>
                  </div>
                  <div class="act_as_tbody">
                    %for partner_name, p_id, p_ref, p_name in partners_order[acc.id]:
                       %if agged_lines_accounts[acc.id].get(p_id):
                       <div class="act_as_row lines">
                         <%line = agged_lines_accounts[acc.id][p_id]%>
                         <%percents = agged_percents_accounts[acc.id]%>
                         <%totals = agged_totals_accounts[acc.id]%>
                           <div class="act_as_cell first_column">${partner_name}</div>
                           <div class="act_as_cell">${p_ref or ''}</div>

                           <div class="act_as_cell amount">${formatLang(line.get('balance') or 0.0) | amount}</div>
                            %for classif in ranges:
                              <div class="act_as_cell classif amount">
                                ${formatLang(line['aged_lines'][classif] or 0.0) | amount}
                              </div>
                            %endfor
                       </div>
                       %endif
                    %endfor
                    <div class="act_as_row labels">
                      <div class="act_as_cell total">${_('Total')}</div>
                      <div class="act_as_cell"></div>
                      <div class="act_as_cell amount classif total">${formatLang(totals['balance']) | amount}</div>
                      %for classif in ranges:
                        <div class="act_as_cell amount classif total">${formatLang(totals[classif]) | amount}</div>
                      %endfor
                    </div>

                    <div class="act_as_row">
                      <div class="act_as_cell"><b>${_('Percents')}</b></div>
                      <div class="act_as_cell"></div>
                      <div class="act_as_cell"></div>
                      %for classif in ranges:
                        <div class="act_as_cell amount percent_line  classif">${formatLang(percents[classif]) | amount}%</div>
                      %endfor
                    </div>
                  </div>
                  <br/>

                 %endif
              %endfor
        </div>
    </body>
</html>
