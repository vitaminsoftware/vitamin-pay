# -*- coding: utf8 -*-
from flask import Flask, redirect, url_for, render_template, request, flash

import os
from os.path import join, dirname
from dotenv import load_dotenv
import braintree

app = Flask(__name__)
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)
app.secret_key = os.environ.get('APP_SECRET_KEY')

braintree.Configuration.configure(
    os.environ.get('BT_ENVIRONMENT'),
    os.environ.get('BT_MERCHANT_ID'),
    os.environ.get('BT_PUBLIC_KEY'),
    os.environ.get('BT_PRIVATE_KEY'),
)

TRANSACTION_SUCCESS_STATUSES = [
    braintree.Transaction.Status.Authorized,
    braintree.Transaction.Status.Authorizing,
    braintree.Transaction.Status.Settled,
    braintree.Transaction.Status.SettlementConfirmed,
    braintree.Transaction.Status.SettlementPending,
    braintree.Transaction.Status.Settling,
    braintree.Transaction.Status.SubmittedForSettlement
]

CURRENCY_SYMBOLS = {
    'EUR': '€',
    'USD': '$',
    'GBP': '£',
}

CURRENCY_ACCOUNTS = {
    'EUR': os.environ.get('BT_MERCHANT_ACCOUNT_EUR'),
    'USD': os.environ.get('BT_MERCHANT_ACCOUNT_USD'),
    'GBP': os.environ.get('BT_MERCHANT_ACCOUNT_GBP'),
}

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html');

@app.route('/checkouts/<string:invoice>/<int:amount>', methods=['GET'], defaults={'currency': 'USD'})
@app.route('/checkouts/<string:invoice>/<int:amount>/<string:currency>', methods=['GET'])
def new_checkout_invoice(invoice, amount, currency):
    client_token = braintree.ClientToken.generate()
    currency_symbol = CURRENCY_SYMBOLS[currency]
    return render_template(
        'checkouts/new.html',
        client_token=client_token,
        invoice=invoice, 
        amount=amount / 100.0,
        currency=currency,
        currency_symbol=currency_symbol,
    )

@app.route('/checkouts/new', methods=['GET'])
def new_checkout():
    client_token = braintree.ClientToken.generate()
    return render_template('checkouts/new.html', client_token=client_token)

@app.route('/checkouts/<transaction_id>', methods=['GET'])
def show_checkout(transaction_id):
    transaction = braintree.Transaction.find(transaction_id)
    result = {}
    if transaction.status in TRANSACTION_SUCCESS_STATUSES:
        result = {
            'header': 'Success!',
            'icon': 'success',
            'message': 'Your transaction has been successfully processed. Thank you for your business!'
        }
    else:
        result = {
            'header': 'Transaction Failed',
            'icon': 'fail',
            'message': 'Your transaction has a status of ' + transaction.status + '.'
        }

    return render_template('checkouts/show.html', transaction=transaction, result=result)

@app.route('/checkouts', methods=['POST'])
def create_checkout():
    sale_payload = {
        'amount': request.form['amount'],
        'order_id': request.form['invoice'],
        'payment_method_nonce': request.form['payment_method_nonce'],
    }

    currency_account = CURRENCY_ACCOUNTS[request.form['currency']]
    if currency_account:
        sale_payload['merchant_account_id'] = currency_account

    result = braintree.Transaction.sale(sale_payload)

    if result.is_success or result.transaction:
        return redirect(url_for('show_checkout', transaction_id=result.transaction.id))
    else:
        for x in result.errors.deep_errors: flash('Error: %s: %s' % (x.code, x.message))
        return redirect(url_for(
            'new_checkout_invoice',
            invoice=request.form['invoice'],
            amount=int(float(request.form['amount'])*100),
            currency=request.form['currency'],
        ))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4567, debug=True)
