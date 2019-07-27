from binance.client import Client
import argparse
from str2bool import str2bool
import time
import tweepy
import os

parser = argparse.ArgumentParser()
parser.add_argument("--debug", type=str2bool, nargs='?', const=True, default=True, help="Activate nice mode.")
args = parser.parse_args()
auth = tweepy.OAuthHandler(os.environ['consumer_api_key'], os.environ['consumer_api_secret'])
auth.set_access_token(os.environ['access_token'], os.environ['access_token_secret'])
try:
    redirect_url = auth.get_authorization_url()
except tweepy.TweepError:
    print('Error! Failed to get request token.')
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)


class BinanceTradeAlert:
    asset_list = ["BTCUSDT"]
    DEBUG = args.debug
    tick_rate = 60   # in seconds
    trigger_ratio = 1
    binance_bot_message = "binance volume alert - robot - "
    spike_threshold_table = {
        "BTCUSDT": 10**6
    }

    def __init__(self):
        self.timer = 10 if self.DEBUG else 0
        self.last_trade_id_set = None
        self.check_twitter_status()

    def check_twitter_status(self):
        assert(api.verify_credentials() is not False)
        print("twitter credentials verified...")

    def get_dollars_in_middle_optimized(self, asset='BTCUSDT', num_trades=400):
        """
        num_trades is sensitive to tick frequency
        essentially, we query the amount of dollars for the last num_trades trades
        :param asset: the asset we query for (optional)
        :param num_trades: the number of trades we query (optional)
        :return: amount of dollar since last tick in float
        """
        new_trade_id_set = set(
            [(i['id'], i['price'], i['qty']) for i in client.get_recent_trades(symbol=asset, limit=num_trades)]
        )
        if not self.last_trade_id_set:
            self.last_trade_id_set = new_trade_id_set
            return 0
        diff = new_trade_id_set.difference(self.last_trade_id_set)
        total_dollars = sum([float(i[1]) * float(i[2]) for i in diff])
        msg1 = '${:,.2f} traded'.format(total_dollars)
        msg2 = f', {len(self.last_trade_id_set.difference(new_trade_id_set))} '\
            f'trades for the past {self.tick_rate} seconds'
        print(msg1 + msg2)
        self.last_trade_id_set = new_trade_id_set
        return total_dollars

    def check_spike_alert(self, dollar, asset):
        severity_ratio = round(dollar / self.spike_threshold_table[asset], 2)
        dollar_msg = '${:,.2f} traded'.format(dollar)
        msg = self.binance_bot_message + f'severity level - {severity_ratio}\n' \
            f'{dollar_msg} in {self.tick_rate/60} minutes'
        if severity_ratio >= self.trigger_ratio:
            print(msg)
            self.publish_tweet(msg)

    @staticmethod
    def publish_tweet(msg):
        api.update_status(msg)

    def alert(self):
        counter = 0
        while not self.DEBUG or counter < self.timer:
            counter += 1
            time.sleep(self.tick_rate)
            for asset in self.asset_list:
                dollars = self.get_dollars_in_middle_optimized(asset)
                self.check_spike_alert(dollars, asset)


if __name__ == "__main__":
    client = Client("", "")
    program = BinanceTradeAlert()
    program.alert()
