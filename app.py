from flask import Flask, render_template, request, send_file
import yfinance as yf
import pandas as pd
import io

app = Flask(__name__)

def format_large_number(value):
    if pd.isna(value):
        return 'N/A'
    
    if abs(value) >= 1e9:
        return f'{value/1e9:,.2f} B'
    elif abs(value) >= 1e6:
        return f'{value/1e6:,.2f} M'
    elif abs(value) >= 1e3:
        return f'{value/1e3:,.2f} K'
    else:
        return f'{value:,.2f}'

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        symbol = request.form['symbol']
        statement_type = request.form['statement_type']
        period = request.form['period']
        
        stock = yf.Ticker(symbol)
        
        if statement_type == 'income':
            statement = stock.income_stmt if period == 'annual' else stock.quarterly_income_stmt
        elif statement_type == 'balance':
            statement = stock.balance_sheet if period == 'annual' else stock.quarterly_balance_sheet
        elif statement_type == 'cash':
            statement = stock.cashflow if period == 'annual' else stock.quarterly_cashflow
        else:
            statement = None
        
        currency = stock.info.get('currency', 'Unknown')
        
        if statement is not None:
            formatted_statement = statement.applymap(lambda x: format_large_number(x))
        else:
            formatted_statement = None
        
        return render_template('statement.html', statement=formatted_statement, symbol=symbol, statement_type=statement_type, period=period, currency=currency)
    
    return render_template('index.html')

@app.route('/download_excel', methods=['POST'])
def download_excel():
    statement = pd.read_json(request.form['statement'])
    symbol = request.form['symbol']
    statement_type = request.form['statement_type']
    period = request.form['period']
    
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        statement.columns = statement.columns.strftime('%b %Y')
        
        statement.to_excel(writer, sheet_name='Sheet1', index=True)
        
        workbook = writer.book
        worksheet = writer.sheets['Sheet1']
        
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': False,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1,
            'align': 'center'
        })
        
        metrics_format = workbook.add_format({
            'align': 'left'
        })
        
        data_format = workbook.add_format({
            'align': 'right'
        })
        
        for col_num, value in enumerate(statement.columns.values):
            worksheet.write(0, col_num + 1, value, header_format)
        
        for row_num, value in enumerate(statement.index):
            worksheet.write(row_num + 1, 0, value, metrics_format)
        
        for row_num, row in enumerate(statement.values):
            for col_num, value in enumerate(row):
                worksheet.write(row_num + 1, col_num + 1, value, data_format)
        
        worksheet.set_column(0, 0, 30) 
        
        for i, col in enumerate(statement.columns):
            max_len = max(
                len(col),
                max(len(str(val)) for val in statement[col])
            )
            worksheet.set_column(i + 1, i + 1, max_len + 2)
    
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'{symbol}_{statement_type}_{period}.xlsx'
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)