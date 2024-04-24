from pydantic import BaseModel


class SingleShortUrlCreate(BaseModel):
    """
    创建短链时提交的参数
    """
    long_url: str
    msg_context: str
    short_url: str = "http://127.0.0.1:2345/"
    visits_count: int = 0
    short_tag: str = ""
    created_by: str = ""
