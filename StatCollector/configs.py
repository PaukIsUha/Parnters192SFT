import os


class DatabaseConfigs:
    login: str = os.getenv("DB_LOGIN")
    password: str = os.getenv("DB_PASSWORD")
    host: str = os.getenv("DB_HOST")
    port: str = os.getenv("DB_PORT")
    name: str = os.getenv("DB_NAME")

    def __call__(self):
        return f"postgresql+psycopg2://{self.login}:{self.password}@{self.host}:{self.port}/{self.name}"


DATABASE_CONFIGS = DatabaseConfigs()


class GSheetConfings:
    link: str = os.getenv("GSHEET_LINK")


GSHEET_CONFIGS = GSheetConfings()

SpyLogButton = {
    'register_start': 0,
    'register_finish': 1,
    'register_conv': 2,

    'connect_start': 3,
    'connect_finish': 4,
    'connect_conv': 5,

    'act_prod_start': 6,
    'act_prod_finish': 7,
    'act_prod_conv': 8,

    'edu_start': 9,
    'edu_finish': 10,
    'edu_conv': 11,
}

SpyLogBID = ['register_start',
             'register_finish',
             'register_conv',
             'connect_start',
             'connect_finish',
             'connect_conv',
             'act_prod_start',
             'act_prod_finish',
             'act_prod_conv',
             'edu_start',
             'edu_finish',
             'edu_conv']
