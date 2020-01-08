# -*- coding: utf8 -*-
from flask import Flask, redirect, url_for, render_template, request, flash
from flask_httpauth import HTTPBasicAuth

import os
from os.path import join, dirname
from dotenv import load_dotenv
import braintree
from gateway import generate_client_token, transact, find_transaction

from flask_sslify import SSLify

load_dotenv()

app = Flask(__name__)
auth = HTTPBasicAuth()

app.secret_key = os.environ.get('APP_SECRET_KEY')

PORT = int(os.environ.get('PORT', 4567))

sslify = SSLify(app)

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

RECAPTCHA_SITE_KEY = os.environ.get('BT_RECAPTCHA_SITE_KEY') 

@auth.verify_password
def verify_password(username, password):
    return (username == os.environ.get('BT_AUTH_USER')) and \
            (password == os.environ.get('BT_AUTH_PASSWORD'))

@app.route('/', methods=['GET'])
@auth.login_required
def index():
    return render_template('index.html');

@app.route('/checkouts/<string:invoice>/<int:amount>', methods=['GET'], defaults={'currency': 'USD'})
@app.route('/checkouts/<string:invoice>/<int:amount>/<string:currency>', methods=['GET'])
@auth.login_required
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
        recaptcha_token=RECAPTCHA_SITE_KEY,
    )

@app.route('/checkouts/new', methods=['GET'])
@auth.login_required
def new_checkout():
    client_token = generate_client_token()
    return render_template('checkouts/new.html', client_token=client_token, recaptcha_token=RECAPTCHA_SITE_KEY)

@app.route('/checkouts/<transaction_id>', methods=['GET'])
@auth.login_required
def show_checkout(transaction_id):
    transaction = find_transaction(transaction_id)
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
@auth.login_required
def create_checkout():
    sale_payload = {
        'amount': request.form['amount'],
        'order_id': request.form['invoice'],
        'payment_method_nonce': request.form['payment_method_nonce'],
        'options': {
            'submit_for_settlement': True
        }
    }

    currency_account = CURRENCY_ACCOUNTS[request.form['currency']]
    if currency_account:
        sale_payload['merchant_account_id'] = currency_account

    result = transact(sale_payload)
    

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
    app.run(host='0.0.0.0', port=PORT, debug=True)
