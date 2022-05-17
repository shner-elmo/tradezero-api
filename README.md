# TradeZero_API

### Non-official TradeZero API
<br />
This connection is obtained by logging onto TZ's ZeroFree web platform with Selenium, and therefore the window must always remain open for the driver to interact with the elements.<br />
The following guide will show you how to get started using the TradeZero API, and how to use some of the most common methods, if you still want to learn more check out the docs, good luck!<br /><br />
To create the connection you must instantiate the TradeZero class and provide the following arguments:

```python
from tradezero_api import TradeZero

tz = TradeZero('chromedriver.exe', 'username', 'password')
tz.login()
```
If some time has passed since we've logged in and we want to execute something, we can make sure the connection is still active by calling tz.conn() like so:
```python
tz.conn()
```
Popular data Property Values
```python
aapl = tz.data('AAPL')
print(f'bid: {aapl.bid}, ask: {aapl.ask}, volume: {aapl.volume}')
```
```
'bid: 145.18, ask: 145.21, volume: 86473580.0'
```
For more properties check out the docstring for this method.
<br /><br />
Check if we alredy own a Stock, otherwise: place a Buy Limit order:
```python
if not tz.invested('AAPL'):    
    tz.limit_order('buy', 'AAPL', aapl.ask + 0.02, 100)
```
Fetch the last three Notifications:
```python
notifications = tz.fetch_notif(3)
print(notifications)
# returns a nested list with time, title, and message
```
```
[['17:57:22', 'Level 2', 'You are not authorized for symbol: AMD'],
 ['17:57:22', 'Error', 'You are not authorized for symbol: AMD'],
 ['17:50:04', 'Level 2', 'You are not authorized for symbol: AAPL']]
```
Locate 100 shares of UBER
```python
# total_price is the max amount in USD we're willing to pay for the shares
tz.locate_stock('uber', max_price=0.10, shares_amount=100)
```
To credit located shares:
```python
tz.credit_locates('uber')
```
Finally, once you're done using the module, before closing it you should close the driver like so:
```python
tz.exit()
```
<br />

<!-- Task List -->
## To-do list
* [ ] Add MarketOrder()
* [ ] Add StopMarketOrder()
* [ ] Make a Tutorial video on YT (once stars >= 5)
