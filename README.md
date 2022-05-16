# TradeZero_API
Non-official TradeZero API, this connection is created by logging in to TZ's ZeroFree web platform thru Selenium and therefore the window must always remain open for the driver to interact with the elements.

To create the connection u must instantiate the TradeZero class and provide the following arguements:
```python
from tradezero_api import TradeZero

tz = TradeZero('chromedriver.exe', 'username', 'password')
tz.login()
```

If some time has passed since we've logged in and we want to execute something, 
we can make sure the connection is still active by calling tz.conn() like so:
```python
tz.conn()
```

To get the current bid/ask for a given stock:
```python
aapl = tz.data('AAPL')
print(f'bid: {aapl.bid}, ask: {aapl.ask}, volume: {aapl.volume}')
```
```
bid: 145.18, ask: 145.21, volume: 86473580.0
```

Check if we alredy own a stock, otherwise: place a Buy Limit order:
```python
if not tz.invested('AAPL'):
    tz.limit_order('buy', 'AAPL', aapl.ask + 0.02, 100)
```

Fetch the last three Notifications:
```python
notifications = tz.fetch_notif(3)
print(notifications)
```
```
[['17:57:22', 'Level 2', 'You are not authorized for symbol: AMD'],
 ['17:57:22', 'Error', 'You are not authorized for symbol: AMD'],
 ['17:50:04', 'Level 2', 'You are not authorized for symbol: AAPL']]
```
Locate 100 shares of UBER
```python
# total_price is the max amount in USD we're willing to pay for the shares
tz.locate_stock('uber', total_price=0.11, shares_amount=100)
```
To credit located shares:
```python
tz.credit_locates('uber')
```

Finally, once youre done using the module, before closing it you shoul close the driver like so:
```python
tz.exit()
```
