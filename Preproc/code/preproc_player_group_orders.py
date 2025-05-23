#%%
import pandas as pd
import numpy as np

player_data = pd.read_csv('Preproc/temp/normalized_player.csv')
order_data = pd.read_csv('Preproc/temp/normalized_orders.csv')
group_data = pd.read_csv('Preproc/temp/normalized_group.csv')
sess_data = pd.read_csv('Preproc/temp/preproc_session.csv').set_index('session')

print("## Preproc Group - Player - Orders")

# purging practice rounds
print("\t... Purging practice rounds")
group_data = group_data[group_data.is_practice == 0].copy()
np_rounds = group_data['round'].values
start_round = min(np_rounds)
player_data = player_data[player_data['round'] >= start_round].copy()
order_data = order_data[order_data['round'] >= start_round].copy()

#Renumber the rounds
group_data['round'] = group_data['round'] - start_round + 1
player_data['round'] = player_data['round'] - start_round + 1
order_data['round'] = order_data['round'] - start_round + 1


#remove extraneous columns
player_cols = list(player_data)
player_cols_exclude = ['id_in_group', 'dr', 'dmu', 'forecast_error',
                       'forecast_reward', 'forecast_bonus_data', 'risk', 
                       'periods_until_auto_sell', 'periods_until_auto_buy',
                       ]
for c in  player_cols_exclude:
    player_cols.remove(c)
player_data = player_data[player_cols]

group_cols = list(group_data)
for c in ['short', ]:
    group_cols.remove(c)
group_data = group_data[group_cols]




# Generate a UID column for all orders
# this by resetting the index.  So far the index is just the integer row numbers
# Calling #reset_index() causes that to become a column which we rename to 'uid'
order_data = order_data.reset_index().rename(mapper={'index': 'uid'}, axis=1)


#%%
# is shorting
# encode order type as a boolean True:SELL; False:BUY
order_data['is_sell'] = (order_data.type == 'SELL')

print("\t... Splitting orders into BUYS and SELLS and tally buy and sell quantities for each player-round")
# sell_quant is 0 for buy orders and the same as quantity for sell orders
order_data['sell_quant'] = order_data.is_sell * order_data.quantity
# buy_quant is 0 for sell orders and the same as quantity for buy orders
order_data['buy_quant'] = (1 - order_data.is_sell) * order_data.quantity

# For each participant and round, tally the buy and sell quantities.
buy_sell = order_data.groupby(['part_label', 'round'])[['buy_quant', 'sell_quant']].sum()

# Join the buy / sell quantities to the player data.
# Player data is naturally organized by participant and round number
# ".join" is a left join by default, so missing values are set to "nan"
# Set "NaN"s to zero and recast to int.
print("\t... Join buy / sell quantites to player data")
p_with_sell_q =  player_data.join(buy_sell, on=['part_label', 'round'])
p_with_sell_q.sell_quant = p_with_sell_q.sell_quant.fillna(0).astype(int)
p_with_sell_q.buy_quant = p_with_sell_q.buy_quant.fillna(0).astype(int)


#####
#####
#%%
# Group Level items
# Previous Price - Lag of market price
# It is important to not here that "prev_price" is the market price that prevails at the start of the round
# "price" is the market price that is calculated based on the orders submitted during that round.
print("\t... Lagging market prices")
prev_price = group_data.groupby('session').price.shift(1)
# Insert the lagged price into the data frame immediately after the market price.
group_data.insert(3, 'prev_price', prev_price)

group_data.drop(['is_practice', 'float'], axis='columns', inplace=True)

# Group - Peak round diff
peak_rnd_df = group_data.join(sess_data.peak_round, on='session')
pk_rnd_diff = peak_rnd_df['round'] - peak_rnd_df.peak_round
pk_rnd_diff.name = 'pk_rnd_diff'
group_data['pk_rnd_diff'] = pk_rnd_diff

start_price = group_data.set_index(['session', 'round']).prev_price
start_price.name = 'market_price'
start_price = start_price.fillna(14)  # this should be round one price, set to the fundamental value.
#%%

# Returns
print("\t... Calculating Returns")
pct_r = (group_data.price - group_data.prev_price) / group_data.prev_price
group_data.insert(4, 'pct_returns', pct_r)
lr = np.log(group_data.price / group_data.prev_price)
group_data.insert(5, 'log_returns', lr)

# Join that previous price (now "market_price") into the working player data.
df = p_with_sell_q.join(start_price, on=['session', 'round'])
# Adding equity and margin related variables (again this is the working version of the player data)
print("\t... Equity calculations")
df['stock_value'] = df.shares * df.market_price
df['equity'] = df.shares * df.market_price + df.cash

#Orderbook Pressure
od = order_data.set_index(['session', 'round', 'type'])
def get_order_book_pressure(x):
    s = x.session.values[0]
    r = x['round'].values[0]
    price = x.price.values[0]
    
    try:
        od.sort_index(inplace=True)
        bids = od.loc[(s, r, 'BUY')]
    except KeyError:
        bids = None
        
    try:
        asks = od.loc[(s, r, 'SELL')]
    except:
        asks = None
        
    
    bids_below_price = bids[bids.price < price] if bids is not None else None
    asks_above_price = asks[asks.price > price] if asks is not None else None
    
    if bids_below_price is None or bids_below_price.shape[0] == 0:
        max_bid = 0 
        bid_vol = 0    
    else: 
        max_bid = bids_below_price.price.max()
        bid_vol = bids_below_price.quantity.sum()

    if asks_above_price is None or asks_above_price.shape[0] == 0:   
        min_ask = 0 
        ask_vol = 0
    else:
        min_ask = asks_above_price.price.max()
        ask_vol = asks_above_price.quantity.sum()
    
    if ask_vol == 0 and bid_vol == 0:
        obp = 0
    else:
        obp = (max_bid * bid_vol + min_ask * ask_vol) / (bid_vol + ask_vol)
    return obp


book_pressure = group_data.groupby(['session', 'round']).apply(get_order_book_pressure)
book_pressure.name='order_book_pressure'

group_data = group_data.join(book_pressure, on=['session', 'round'])

# Player - peak round diff

#%%
# Write all out to the temp directory
print("\t... Write to disk")
group_data.to_csv('Preproc/temp/preproc_group.csv', index=False)
df.to_csv('Preproc/temp/intermed_player.csv', index=False)  #player data
order_data.to_csv('Preproc/temp/preproc_orders.csv', index=False)