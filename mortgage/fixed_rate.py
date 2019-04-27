import numpy as np
import pandas as pd

class FixedRateMortgage(object):
    def __init__(self, home_price, down_payment_pct, loan_term_months, interest_rate, extra_payments=None):
        """
        :param home_price: Home purchase price
        :type  home_price: int or float
        :param down_payment_pct: Percentage of home purchase price paid up front
        :type  down_payment_pct: float in decimal format, e.g. 0.90 for 90%
        :param loan_term_months: Expected term of loan if making only the monthly payment each month
        :type  loan_term_months: int
        :param interest_rate: Annual interest rate on the mortgage
        :type  interest_rate: float in decimal format, e.g. 0.0425 for 4.25%
        :param extra_payments: The additional amount of money paid each month. Any values AFTER the mortgage
            is paid off will be ignored
        :type  extra_payments: Iterable of floats, e.g. [100.0, ..., 100.00] with length equal to `loan_term_months`
        """
        self.home_price = home_price
        self.down_payment_pct = down_payment_pct
        self.loan_term_months = loan_term_months
        self.interest_rate = interest_rate
        self.loan_amount = home_price * (1 - down_payment_pct)
        self.balance = self.loan_amount

        # Set extra_payments equal to [0.0, ..., 0.0] if not provided
        if (extra_payments is None):
            extra_payments = np.zeros(loan_term_months)
        assert len(extra_payments) == loan_term_months, "number of extra_payments must be equal to loan_term_months,"\
                + "expected {} but got {}".format(loan_term_months, extra_payments)
        self.extra_payments = extra_payments

        # Store underlying data as a private variable
        self._data = None

    def is_paid(self):
        return self.balance < 0.01

    def get_data(self):
        """
        Get/generate all the data

        :return: Dataframe with columns
            :column month: the month number, starting from 0 and ending at loan_term_months
            :type   month: int
            :column principal: the principal paid for that month
            :type   principal: float
            :column interest: the interest paid for that month
            :type   interest: float
            :column extra_payment: the additional principal paid for that month
            :type   extra_payment: float
            :column balance: the remaining balance on the loan
            :type   balance: float
            :column total_principal: the total principal paid up to and including the current month
            :type   total_principal: float
            :column total_interest: the total interest paid up to and including the current month
            :type   total_interest: float
            :column total_extra_payment: the total extra payments paid up to and including the current month
            :type   total_extra_payment: float
        """
        if self._data is not None:
            return self._data
        self._data = pd.DataFrame({
            'month': range(0, self.loan_term_months),
            'principal': 0.0,
            'interest': 0.0,
            'extra_payment': 0.0,
            'balance': 0.0,
            'total_principal': 0.0,
            'total_interest': 0.0,
            'total_extra_payment': 0.0
        })
        self._amortize()
        self._data['total_principal'] = self._data['principal'].expanding(min_periods=1).sum()
        self._data['total_extra_payment'] = self._data['extra_payment'].expanding(min_periods=1).sum()
        self._data['total_interest'] = self._data['interest'].expanding(min_periods=1).sum()

        return self._data


    def _amortize(self):
        # Get the fixed monthly payment size needed to pay off the loan by the end of the term as a positive number
        payment = -1 * np.pmt(self.interest_rate/12, self.loan_term_months, self.loan_amount)
        month = 0
        while month < self.loan_term_months:
            if not self.is_paid():
                interest = (self.interest_rate/12) * self.balance
                payment = min(payment, self.balance + interest)
                principal = payment - interest

                remaining_loan_balance = self.balance - principal
                extra_payment = min(self.extra_payments[month], remaining_loan_balance)
                self.balance = self.balance - principal - extra_payment
            else:
                # Loan is paid off early
                interest, payment, principal, extra_payment = 0, 0, 0, 0

            # Add data point
            self._data.at[month, 'month'] = month
            self._data.at[month, 'principal'] = principal
            self._data.at[month, 'interest'] = interest
            self._data.at[month, 'extra_payment'] = extra_payment
            self._data.at[month, 'balance'] = self.balance

            # Increment month for next iteration
            month += 1
