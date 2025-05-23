import os


class DatabaseConfigs:
    login: str = os.getenv("DB_LOGIN")
    password: str = os.getenv("DB_PASSWORD")
    host: str = os.getenv("DB_HOST")
    port: str = os.getenv("DB_PORT")
    name: str = os.getenv("DB_NAME")

    def __call__(self):
        return f"postgresql+asyncpg://{self.login}:{self.password}@{self.host}:{self.port}/{self.name}"


DATABASE_CONFIGS = DatabaseConfigs()


class BotConfings:
    token: str = os.getenv("BOT_TOKEN")
    bot_name: str = os.getenv("BOT_NAME")


BOT_CONFIGS = BotConfings()


class NotifierConfigs:
    port: int = os.getenv("NOTIFIER_PORT")
    host: str = os.getenv("NOTIFIER_HOST")

    def register_url(self):
        return f"http://{self.host}:{self.port}/notify"

    def reg_url(self):
        return f"http://{self.host}:{self.port}/notif"

    def contact_url(self):
        return f"http://{self.host}:{self.port}/contact"

    def products_url(self):
        return f"http://{self.host}:{self.port}/products"

    def start_edu_url(self):
        return f"http://{self.host}:{self.port}/start_edu"

    def finish_edu_url(self):
        return f"http://{self.host}:{self.port}/finish_edu"

    def get_indiv_url(self):
        return f"http://{self.host}:{self.port}/get_indiv"


NOTIFIER_CONFIGS = NotifierConfigs()

LESSONS = [
    ("source4/lesson1.mp4", 20),
    ("source4/lesson1.mp4", 20),
    ("source4/lesson1.mp4", 20)
]

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


