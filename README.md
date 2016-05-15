# Vitamin Software Payment System

Handles ad-hoc credit card and Paypal payments for Vitamin Software LLC invoices.
The repo is based on the [Braintree integration for Flask example](https://github.com/braintree/braintree_flask_example).

## Setup Instructions

1. Install requirements:
  ```sh
  pip install -r requirements.txt
  ```

2. Copy the `example.env` file to `.env` and fill in your Braintree API credentials. Credentials can be found by navigating to Account > My User > View Authorizations in the Braintree Control Panel. Full instructions can be [found on our support site](https://articles.braintreepayments.com/control-panel/important-gateway-credentials#api-credentials).

3. Start server:
  ```sh
  python app.py
  ```

## Usage

The app will process card payments for invoices issued by **Vitamin Software LLC invoices ONLY**. The payment form is unique to each invoice and follows the pattern http://pay.vitaminsoftware.com/checkouts/[invoice]/[amount].
- *invoice* field should match the invoice number we'd like to get paid for;
- *amount* represents the total value of the invoice in cents (USD pence).

For example to receive a payment for invoice **VIT00117** in the amount of **$218.75** the following URL should be distributed to the client: `http://pay.vitaminsoftware.com/checkouts/VIT00117/21875`. 


## Deploying to Heroku

You can deploy this app directly to Heroku to see the app live. Skip the setup instructions above and click the button below. This will walk you through getting this app up and running on Heroku in minutes.

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/vitaminsoftware/vitamin-pay&env[BT_ENVIRONMENT]=production)

## Running tests

Unit tests do not make API calls to Braintree and do not require Braintree credentials. You can run this project's unit tests by calling `python test_app.py` on the command line.

## Pro Tips

- The `application.cfg.example` contains an `APP_SECRET_KEY` setting. Even in development you should [generate your own custom secret key for your app](http://flask.pocoo.org/docs/0.10/quickstart/#sessions).

## Help

 * Found a bug? Have a suggestion for improvement? [Submit an issue](https://github.com/vitaminsoftware/vitamin-pay/issues)

