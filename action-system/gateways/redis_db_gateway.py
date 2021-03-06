"""
Redis gateway help to make connection for Python programs with Redis database.

Run Redis with Docker:
> docker run --name redis-db -d -p 6379:6379 redis
> docker exec -it redis-db bash
> redis-cli

Set for key 'limit' value of 150 with expiration time 5 s.
> SET limit 150 EX 5

Project page: https://pypi.org/project/redis/
GitHub: https://github.com/andymccurdy/redis-py

pip install redis

@Author: Patryk Jacek Laskowski
"""
import argparse
import time
import os

import redis


class RedisGateway:

    HOST_ENV_KEY = 'REDIS_HOST'
    PORT_ENV_KEY = 'REDIS_PORT'
    PASSWD_ENV_KEY = 'REDIS_PASSWD'
    REDIS_FLAG_ENV_KEY = 'REDIS_FLAG'
    REDIS_LIMIT_KEY_ENV_KEY = 'REDIS_LIMIT_KEY'

    def __init__(self, host=None, port=None, password=None, timeout=30):
        self.host = host
        self.port = int(port) if port else print('Choosing Redis default port: 6379') or 6379
        self.password = password

        self.r = redis.Redis(self.host, self.port, password=self.password, db=0, decode_responses=True)
        self._test_connection_with(timeout)

    def __str__(self):
        return f'<{self.__class__.__name__} instance connected to server {self.host}:{self.port}>'

    def _test_connection_with(self, timeout):
        for t in range(1, timeout+1):
            try:
                self._test_connection()
            except redis.exceptions.ConnectionError as e:
                if t >= timeout:
                    raise redis.exceptions.ConnectionError from e
                else:
                    time.sleep(1)
            else:
                break

    def _test_connection(self):
        try:
            self.r.echo('test_value')
        except redis.exceptions.AuthenticationError:
            raise redis.exceptions.AuthenticationError('Authentication required. Provide password.') from None
        except redis.exceptions.ResponseError:
            raise redis.exceptions.ResponseError('Invalid username-password pair or user is disabled') from None
        except redis.exceptions.ConnectionError:
            raise redis.exceptions.ConnectionError(f'Cannot connect to {self.host}:{self.port}. Connection refused.') from None

    def get(self, key, default=None, map_type=int):
        # TODO: Make it asynchronous. To not make eventual delays caused with network connection
        value = None
        try:
            value = map_type(self.r.get(key))
        except TypeError:
            raise TypeError(f'Value received from Redis db cannot be mapped to {str(map_type)}') from None
        finally:
            return value or default

    @classmethod
    def create_redis_parser(cls):
        """
        Helps to build command line interface common arguments for RedisGateway.

        To combine two parsers use 'parents' argument of argparse.ArgumentParser
        e.g.
            final_parser = argparse.ArgumentParser(conflict_handler='resolve', parents=[parser_A, parser_B])
            args = final_parser.parse_args()
        """
        parser = argparse.ArgumentParser()

        redis_flag = '--redis'
        parser.add_argument(redis_flag, action='store_true',
                            default=True if os.getenv(cls.REDIS_FLAG_ENV_KEY) else False,
                            help='Redis flag to help determine if Redis connection is desired.')

        parser.add_argument('--redis_host', type=str, default=os.getenv(cls.HOST_ENV_KEY, '127.0.0.1'),
                            help=f'Redis hosting server ip. Possible to use ENV var {cls.HOST_ENV_KEY}.')
        parser.add_argument('--redis_port', type=int, default=os.getenv(cls.PORT_ENV_KEY, 6379),
                            help=f'Redis server port. Possible to use ENV var {cls.PORT_ENV_KEY}.')
        parser.add_argument('--redis_passwd', type=str, default=os.getenv(cls.PASSWD_ENV_KEY),
                            help=f'Redis server ip. Possible to use ENV var {cls.PASSWD_ENV_KEY}.')

        parser.add_argument('--redis_limit_key', type=str, default=os.getenv(cls.REDIS_LIMIT_KEY_ENV_KEY, 'limit'),
                            help='Key in Redis to get')

        return parser


if __name__ == '__main__':

    parser = RedisGateway.create_redis_parser()
    args = parser.parse_args()

    # From args or read from ENV variables
    host = args.redis_host
    port = args.redis_port
    passwd = args.redis_passwd

    rg = RedisGateway(host, port, passwd)
    print(rg)

    while True:
        limit = rg.get(args.redis_limit_key)
        print(limit)
        time.sleep(0.5)
