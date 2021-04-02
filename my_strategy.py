class Strategy():
    # option setting needed
    def __setitem__(self, key, value):
        self.options[key] = value

    # option setting needed
    def __getitem__(self, key):
        return self.options.get(key, '')

    def __init__(self):
        # strategy property
        self.subscribedBooks = {
            'Binance': {
                'pairs': ['BTC-USDT'],
            },
        }
        self.period = 15 * 60
        self.options = {}

        # user defined class attribute
        self.last_type = 'sell'
        self.last_cross_status = None
        self.close_price_trace = np.array([])
        self.ma_long = 25
        self.ma_short = 5
        self.UP = 1
        self.DOWN = 2

        self.bb_length = 20

    def on_order_state_change(self,  order):
        Log("on order state change message: " + str(order) + " order price: " + str(order["price"]))

    def get_current_ma_cross(self):
        s_ma = talib.SMA(self.close_price_trace, self.ma_short)[-1]
        l_ma = talib.SMA(self.close_price_trace, self.ma_long)[-1]

        upper, middle, lower = talib.BBANDS(
                                self.close_price_trace, 
                                timeperiod=self.bb_length,
                                # number of non-biased standard deviations from the mean
                                nbdevup=1,
                                nbdevdn=1,
                                # Moving average type: simple moving average here
                                matype=0)

        rsi_score = talib.RSI(self.close_price_trace)[-1]   

        Log('rsi:'+str(rsi_score)+'bb low:' +str(lower[-1]))


        if np.isnan( lower[-1]):
            if rsi_score < 42:
                return self.UP
            if rsi_score > 70:
                return self.DOWN
        if rsi_score < 42 and self.close_price_trace[-1] < lower[-1] and self.close_price_trace[-2] < self.close_price_trace[-1]:
            return self.UP
        if rsi_score > 70 and self.close_price_trace[-1] > upper[-1]:
            return self.DOWN
        return None

    # called every self.period
    def trade(self, information):


        exchange = list(information['candles'])[0]
        pair = list(information['candles'][exchange])[0]
        target_currency = pair.split('-')[0]  #ETH
        base_currency = pair.split('-')[1]  #USDT

        base_currency_amount = self['assets'][exchange][base_currency] 
        target_currency_amount = self['assets'][exchange][target_currency] 


        # add latest price into trace
        close_price = information['candles'][exchange][pair][0]['close']
        self.close_price_trace = np.append(self.close_price_trace, [float(close_price)])


        # only keep max length of ma_long count elements
        self.close_price_trace = self.close_price_trace[-20:]

        # calculate current ma cross status
        cur_cross = self.get_current_ma_cross()

        # cross up
        if self.last_type == 'sell' and cur_cross == self.UP:
            Log('buying 1 unit of ' + str(target_currency))
            self.last_type = 'buy'
            self.last_cross_status = cur_cross
            return [
                {
                    'exchange': exchange,
                    'amount': 1,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        # cross down
        elif self.last_type == 'buy' and cur_cross == self.DOWN:
            Log('assets before selling: ' + str(self['assets'][exchange][base_currency]))
            self.last_type = 'sell'
            self.last_cross_status = cur_cross
            return [
                {
                    'exchange': exchange,
                    'amount': -target_currency_amount,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]

        self.last_cross_status = cur_cross
        return []
