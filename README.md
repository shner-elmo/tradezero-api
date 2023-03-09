# tradezero-api

### Non-official TradeZero API


---
[![PyPi](https://img.shields.io/badge/PyPi-0.3.0-yellow)](https://pypi.org/project/tradezero-api/)
[![Downloads](https://pepy.tech/badge/tradezero-api)](https://pepy.tech/project/tradezero-api)
[![Downloads](https://pepy.tech/badge/tradezero-api/month)](https://pepy.tech/project/tradezero-api)

You can get the package directly from [PyPI](https://pypi.org/project/tradezero-api/)
```
pip install tradezero-api
```
---


<br />
This connection is obtained by logging onto TZ's ZeroFree web platform with Selenium, and therefore the window must always remain open for the driver to interact with the elements.<br />
The following guide will show you how to get started using the TradeZero API, and how to use some of the most common methods, if you still want to learn more check out the docs, good luck!<br /><br />
To create the connection you must instantiate the TradeZero class and provide the following arguments:

```python
from tradezero_api import TradeZero

tz = TradeZero(user_name='username', password='password')
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

Place a Market Order:
```python
from tradezero_api import Order

tz.market_order(Order.SHORT, 'AAPL', 200)  
```
Check if we alredy own a Stock, otherwise: place a Buy Limit order:
```python
if not tz.Portfolio.invested('AMD'):
    limit_price = tz.data('AMD').ask + 0.02
    tz.limit_order(Order.BUY, 'AMD', 100, limit_price)
```
Get last three Notifications:
```python
notifications = tz.Notification.get_notifications(3)
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
# max_price is the max amount in USD we're willing to pay for the shares
tz.locate_stock('uber', 100, max_price=0.10)
```
To credit located shares:
```python
tz.credit_locates('uber')
```
Finally, once you're done using the module, before closing it you should close the driver like so:
```python
tz.exit()
```

### Accessing Bid, Ask and Last prices faster
So far we have covered accessing data for a given stock with ```tz.data(stock)```  
but there is another way to access the Bid, Ask and Last prices, and that is directly from  
the attributes:
```python
print(f'Bid: {tz.bid}, Ask: {tz.ask}, Last: {tz.last}')
```
```
Bid: 22.11, Ask: 22.13, Last: 22.12
```
The advantage of using the attribute instead of tz.data(), is that its much faster, 
as it takes about 20ms to locate each property, and tz.data() will locate all eight properties
even if youre just going to use one of them.  
tz.bid on the other hand locates only one property so it will take about 20ms 
to fetch the price.  
However the disadvantage of using tz.bid is that it will simply show the 
bid of the symbol that is currently present in the top panel, which in our case is UBER 
because we called tz.locate_stock()  
But we can make sure that the current symbol is what we expect like so:  
```python
symbol = 'amd'
if tz.current_symbol() == symbol.upper():
    print(f'Bid: {tz.bid}')
```
The current_symbol() method will add about 25ms, so in total it will be roughly 50ms 
using our previous example.  

In conclusion, when should we use tz.data().bid ? and when should we use the faster tz.bid method ?  
if we are sure that the current symbol is the correct one, use: ```tz.bid```  
But if we are not sure whats the current symbol, then use: ```tz.data(stock).bid```  

Although we can still use tz.bid in combination with tz.current_symbol() like the example above,  
but if the symbol isnt what we expect than it will do nothing, so better to stick with those
two options.
