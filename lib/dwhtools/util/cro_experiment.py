from datetime import datetime
from math import exp, log

columns = {
  # keys
  # um. . .

  # metadata features
  'optimize_link' : 'CHARACTER VARYING(256)',
  'clickup_link' : 'CHARACTER VARYING(256)',
  'start' : 'DATE',
  'close' : 'DATE',

  # heirarchical features
  'product' : 'CHARACTER VARYING(256)',
  'page' : 'CHARACTER VARYING(256)',
  'test_name' : 'CHARACTER VARYING(256)',

  # first-order data
  'c_sessions' : 'INT',
  'v_sessions' : 'INT',
  'c_transactions' : 'INT',
  'v_transactions' : 'INT',
  'c_revenue' : 'INT',
  'v_revenue' : 'INT',

  # derived data
  'expected_loss_a' : 'FLOAT',
  'expected_loss_b' : 'FLOAT',
  'expected_lift_a' : 'FLOAT',
  'expected_lift_b' : 'FLOAT',
  'p_win_a' : 'FLOAT',
  'p_win_b' : 'FLOAT',
  'period_revenue' : 'FLOAT',
  }

percentiles = ['_2p5_percent', '_25_percent',  '_50_percent',  '_75_percent',  '_97p5_percent']
# let's create a lot of percentile columns all at once now!
features=['optimize_delta', 'a', 'b', 'cro_delta']
feature_percentiles = []
for feature in features:
  feature_percentiles += [feature + p for p in percentiles]

def sigmoid(x):
  return 1 / (1+ exp(-x))

def logit(x):
  return log(x / (1-x))

def reformat_date(date):
  if type(date) == datetime:
    return date.strftime("%Y-%m-%d")
  try:
    date_tmp = datetime.strptime(date, "%Y-%m-%d")
    return date_tmp.strftime("%Y-%m-%d")
  except:
    try:
      date_tmp = datetime.strptime(date, '%m/%d/%Y')
      return date_tmp.strftime("%Y-%m-%d")
    except:
      try:
        date_tmp = datetime.strptime(date, '%m/%d/%y')
        return date_tmp.strftime("%Y-%m-%d")
      except:
        return None

class Experiment:
  def __init__(self, columns):
    self.columns = columns
    self.native_columns = {}
    self.n_a = None
    self.n_b = None
    self.conversions_a = None
    self.conversions_b = None
    self.expected_loss_a = None
    self.expected_loss_b = None
    self.expected_lift_a = None
    self.expected_lift_b = None
    self.p_win_a = None
    self.p_win_b = None
    self.update()
    self.product = self.columns.get('product', None)
    self.page = self.columns.get('page', None)
    self.name = self.columns.get('test_name', self.columns.get('name', None))

  def __str__(self):
    self.update()
    s = f'** {self.name} **'
    s+= '\nnative columns:' + str(self.native_columns)
    s+= '\nother columns:' + str({k: self.columns[k] for k in self.columns.keys() if k not in self.native_columns.keys()})
    return s

  def update(self, d = None):
    if d:
      self.columns.update(d)
    self.infer_raw_data()
    # TODO: THIS.
    self.columns['start'] = reformat_date(self.columns['start'])
    self.columns['close'] = reformat_date(self.columns['close'])

    self.native_columns = {k : self.columns.get(k, None) for k in columns.keys()}

  # def set_raw_data(self, n_a, n_b, conversions_a, conversions_b):
  #   self.n_a = n_a
  #   self.n_b = n_b
  #   self.conversions_a = conversions_a
  #   self.conversions_b = conversions_b

  def infer_raw_data(self):
    if 'n_a' in self.columns:
      self.n_a = int(self.columns['n_a'])
    elif 'c_sessions' in self.columns:
      self.n_a = int(self.columns['c_sessions'])

    if 'n_b' in self.columns:
      self.n_b = int(self.columns['n_a'])
    elif 'v_sessions' in self.columns:
      self.n_b = int(self.columns['v_sessions'])

    if 'conversion_a' in self.columns:
      self.conversions_a = int(self.columns['conversions_a'])
    if 'c_transactions' in self.columns:
      self.conversions_a = int(self.columns['c_transactions'])

    if 'conversion_b' in self.columns:
      self.conversions_b = int(self.columns['conversions_a'])
    if 'v_transactions' in self.columns:
      self.conversions_b = int(self.columns['v_transactions'])

  def optimize_mean(self):
    if 'optimize_delta' + percentiles[3] in self.columns:
      return(self.columns['optimize_delta' + percentiles[3]])
    else:
      return ' '

  def optimize_data(self):
    s = ''
    for col in ['optimize_delta' + percentiles[i] for i in range(len(percentiles))]:
      s += f'{self.columns.get(col,0)/100:3.0f}%   '

    return s

  def duration(self):
    self.reformat_date()
    try:
      start = datetime.strptime(self.columns['start'], "%Y-%m-%d")
      end = datetime.strptime(self.columns['close'], "%Y-%m-%d")
      return (end-start).days
    except:
      return None
