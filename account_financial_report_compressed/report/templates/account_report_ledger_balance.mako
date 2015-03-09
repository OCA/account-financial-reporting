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
        
        %for account in objects:
        <div class="act_as_table list_table" style="margin-top:5px;">
            <div class="act_as_row labels" style="font-weight: bold; font-size: 12px;">
                <div class="act_as_cell first_column" style="width: 450px;">${account.get('name', '')}</div>
                ## label
                <div class="act_as_cell" style="width: 360px;">${_("Cumulated Balance on Account")}</div>
                ## debit
                <div class="act_as_cell amount" style="width: 80px;">${ formatLang(account.get('total_debit', 0.0)) | amount }</div>
                ## credit
                <div class="act_as_cell amount" style="width: 80px;">${ formatLang(account.get('total_credit', 0.0)) | amount }</div>
                ## balance cumulated
                <div class="act_as_cell amount" style="width: 80px; padding-right: 1px;">${ formatLang(account.get('cumul_balance', 0.0)) | amount }</div>
                %if amount_currency(data):
                    ## currency balance
                    %if account.currency_id:
                        <div class="act_as_cell amount sep_left" style="width: 80px;">${ formatLang(account.get('cumul_balance_curr', 0.0)) | amount }</div>
                    %else:
                        <div class="act_as_cell amount sep_left" style="width: 80px;">${ u'-' }</div>
                    %endif
                    ## curency code
                    <div class="act_as_cell amount" style="width: 30px; text-align: right; padding-right: 1px;">${ account.get('currency_name', '') }</div>
                %endif
            </div>
        </div>
        %endfor
    </body>
</html>
