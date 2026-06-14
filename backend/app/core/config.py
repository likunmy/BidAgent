from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "mysql+pymysql://root:password@localhost:3306/bidagent"
    upload_dir: str = "./uploads"

    model_config = {"env_file": ".env"}


settings = Settings()
