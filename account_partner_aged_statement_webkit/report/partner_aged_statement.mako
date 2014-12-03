## -*- coding: utf-8 -*-
<!DOCTYPE html SYSTEM
"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <style type="text/css">
            .total{
               font-weight:bold;
            }
            .break{
                display: block;
                clear: both;
                page-break-after: always;
            }

            ${css}
        </style>
    </head>

    <%!
    def amount(text):
        # replace by a non-breaking hyphen (it will not word-wrap between hyphen and numbers)
        return text.replace('-', '&#8209;')

    first = True
    %>
    <body>
    %for partner in objects:
        <%setLang(partner.lang)%>
        %if not first:
            <div class="break"></div>
        %endif
        <br/>
        <br/>
        <%from datetime import date %>
        ${_('Date')}: ${formatLang(str(date.today()), date=True)}
        <br>
        ${_('Partner')}: ${partner.name}
        <br>
        ${_('Subject')}: <b>${_('Overdue Statement')}</b>
        <br/>
        <br/>
        %for message_line in message(partner, company):
            <p>
            ${message_line}
            </p>
        %endfor
        <br>
        ${user.name}
        <br>
        <br>
        %if (partner.credit + partner.debit == 0) :
            <div class="title">${_('Nothing due for this partner')}</div>
        %else:
            <div class="title">${_('Aged Balance')}</div>
            <br>
        %for l in get_lines(data['form'], partner):
            %if l:
                <table class=basic_table style="width: 100%;">
                    <tr>
                        <th>${_('Not Due')}</th>
                        <th>${_('0-30')}</th>
                        <th>${_('30-60')}</th>
                        <th>${_('60-90')}</th>
                        <th>${_('90-120')}</th>
                        <th>${_('+120')}</th>
                        <th>${_('Total')}</th>
                    </tr>
                    <tr>
                        <td>${ formatLang(l['direction'], currency_obj=company.currency_id) }</td>
                        <td>${ formatLang(l['4'], currency_obj=company.currency_id) }</td>
                        <td>${ formatLang(l['3'], currency_obj=company.currency_id) }</td>
                        <td>${ formatLang(l['2'], currency_obj=company.currency_id) }</td>
                        <td>${ formatLang(l['1'], currency_obj=company.currency_id) }</td>
                        <td>${ formatLang(l['0'], currency_obj=company.currency_id) }</td>
                        <td>${ formatLang(l['total'], currency_obj=company.currency_id) }</td>
                    </tr>
                </table>
            %endif  ## if l
        %endfor  ## for l in get_lines(data['form'])
        <br>
        <br>
        <div class="title">${_('List of Due Invoices')}</div>
        <br>
        %if getLines30(partner):
            <div class="total">${_('0-30')}</div>
            <table class=basic_table style="width: 100%;">
                <tr>
                    <th>${_('Date')}</th>
                    <th>${_('Description')}</th>
                    <th>${_('Reference')}</th>
                    <th>${_('Due date')}</th>
                    <th>${_('Amount')}</th>
                    <th>${_('Paid')}</th>
                    <th>${_('Total')}<br/>(${company.currency_id.name})</th>
                    <th>${_('Total')}<br/>(fgn. cur.)</th>
                </tr>
                %for line in getLines30(partner):
                <tr>
                    <td>${ formatLang(line.date, date=True) }</td>
                    <td>${ line.move_id.name }</td>
                    <td>${ line.ref }</td>
                    <td>${ line.date_maturity and formatLang(line.date_maturity,date=True) or '' }</td>
                    <td style="text-align: right;">${ formatLang(line.debit) or 0.0 }</td>
                    <td style="text-align: right;">${ formatLang(line.credit) or 0.0 }</td>
                    <td style="text-align: right;">${ formatLang(line.debit - line.credit, currency_obj = company.currency_id)  }</td>
                    <td style="text-align: right;">${ line.amount_currency and formatLang(line.amount_currency, currency_obj = line.currency_id) or '' }</td>
                </tr>
                %endfor  ## for line in getLines30(partner)
            </table>
        %endif  ## if getLines30(partner)
        <br/>
        %if getLines3060(partner):
            <div class="total">${_('30-60')}</div>
            <table class=basic_table style="width: 100%;">
                <tr>
                    <th>${_('Date')}</th>
                    <th>${_('Description')}</th>
                    <th>${_('Reference')}</th>
                    <th>${_('Due date')}</th>
                    <th>${_('Amount')}</th>
                    <th>${_('Paid')}</th>
                    <th>${_('Total')}<br/>(${company.currency_id.name})</th>
                    <th>${_('Total')}<br/>(fgn. cur.)</th>
                </tr>
                %for line in getLines3060(partner):
                <tr>
                    <td>${ formatLang(line.date, date=True) }</td>
                    <td>${ line.move_id.name }</td>
                    <td>${ line.ref }</td>
                    <td>${ line.date_maturity and formatLang(line.date_maturity,date=True) or '' }</td>
                    <td style="text-align: right;">${ formatLang(line.debit) or 0 }</td>
                    <td style="text-align: right;">${ formatLang(line.credit) or 0 }</td>
                    <td style="text-align: right;">${ formatLang(line.debit - line.credit, currency_obj = company.currency_id)  }</td>
                    <td style="text-align: right;">${ line.amount_currency and formatLang(line.amount_currency, currency_obj = line.currency_id) or '' }</td>
                </tr>
                %endfor  ## for line in getLines3060(partner)
            </table>
        %endif  ## if getLines3060(partner)
        <br/>
        %if getLines60(partner):
            <div class="total">${_('+60')}</div>
            <table class=basic_table style="width: 100%;">
                <tr>
                    <th>${_('Date')}</th>
                    <th>${_('Description')}</th>
                    <th>${_('Reference')}</th>
                    <th>${_('Due date')}</th>
                    <th>${_('Amount')}</th>
                    <th>${_('Paid')}</th>
                    <th>${_('Total')}<br/>(${company.currency_id.name})</th>
                    <th>${_('Total')}<br/>(fgn. cur.)</th>
                </tr>
                %for line in getLines60(partner):
                <tr>
                    <td>${ formatLang(line.date, date=True) }</td>
                    <td>${ line.move_id.name }</td>
                    <td>${ line.ref }</td>
                    <td>${ line.date_maturity and formatLang(line.date_maturity,date=True) or '' }</td>
                    <td style="text-align: right;">${ formatLang(line.debit) or 0 }</td>
                    <td style="text-align: right;">${ formatLang(line.credit) or 0 }</td>
                    <td style="text-align: right;">${ formatLang(line.debit - line.credit, currency_obj = company.currency_id)  }</td>
                    <td style="text-align: right;">${ line.amount_currency and formatLang(line.amount_currency, currency_obj = line.currency_id) or '' }</td>
                </tr>
                %endfor  ## for line in getLines60(partner)
            </table>
        %endif  ## if getLines60(partner)
        %endif  ## if (partner.credit + partner.debit == 0

        <%! first = False %>
    %endfor  ## for partner in objects
    </body>
</html>
