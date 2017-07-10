"""Definitions for the `Parameter` class."""
import numpy as np

from collections import OrderedDict
from mosfit.modules.module import Module
from mosfit.utils import listify

# Important: Only define one ``Module`` class per file.


class Parameter(Module):
    """Model parameter that can either be free or fixed."""

    def __init__(self, **kwargs):
        """Initialize module."""
        super(Parameter, self).__init__(**kwargs)
        self._max_value = kwargs.get('max_value', None)
        self._min_value = kwargs.get('min_value', None)
        if (self._min_value is not None and self._max_value is not None and
                self._min_value == self._max_value):
            self._printer.message('min_max_same', [self._name], warning=True)
            self._value = self._min_value
            self._min_value, self._max_value = None, None
        self._value = kwargs.get('value', None)
        self._log = kwargs.get('log', False)
        self._latex = kwargs.get('latex', self._name)
        self._derived_keys = listify(kwargs.get('derived_keys', [])) + [
            'reference_' + self._name]
        if (self._log and self._min_value is not None and
                self._max_value is not None):
            if self._min_value <= 0.0 or self._max_value <= 0.0:
                raise ValueError(
                    'Parameter with log prior cannot have range values <= 0!')
            self._min_value = np.log(self._min_value)
            self._max_value = np.log(self._max_value)
        self._reference_value = None
        self._clipped_warning = False

    def fix_value(self, value):
        """Fix value of parameter."""
        self._max_value = None
        self._min_value = None
        self._value = value

    def is_log(self):
        """Return if `Parameter`'s value is stored as log10(value)."""
        return self._log

    def latex(self):
        """Return the LaTeX representation of the parameter."""
        return self._latex

    def lnprior_pdf(self, x):
        """Evaluate natural log of probability density function."""
        return 0.0

    def prior_cdf(self, u):
        """Evaluate cumulative density function."""
        return u

    def value(self, f):
        """Return the value of the parameter in parameter's units."""
        value = np.clip(f *
                        (self._max_value - self._min_value) + self._min_value,
                        self._min_value, self._max_value)
        if self._log:
            value = np.exp(value)
        return value

    def fraction(self, value, clip=True):
        """Return fraction given a parameter's value."""
        if self._log:
            value = np.log(value)
        f = (value - self._min_value) / (self._max_value - self._min_value)
        if clip:
            of = f
            f = np.clip(f, 0.0, 1.0)
            if f != of and not self._clipped_warning:
                self._clipped_warning = True
                self._printer.message(
                    'parameter_clipped', [self._name], warning=True)
        return f

    def get_derived_keys(self):
        """Return list of keys that should be generated by this parameter."""
        return self._derived_keys

    def process(self, **kwargs):
        """Process module.

        Initialize a parameter based upon either a fixed value or a
        distribution, if one is defined.
        """
        if (self._name in kwargs or self._min_value is None or
                self._max_value is None):
            # If this parameter is not free and is already set, then skip
            if self._name in kwargs:
                return {}

            value = self._value
        else:
            value = self.value(kwargs['fraction'])

        output = OrderedDict([[self._name, value]])
        if self._reference_value is not None:
            output['reference_' + self._name] = self._reference_value

        return output

    def receive_requests(self, **requests):
        """Receive requests from other ``Module`` objects."""
        # Get the first value in the requests dictionary.
        req_keys = list(requests.keys())
        if len(req_keys):
            self._reference_value = requests.get(req_keys[0], None)
